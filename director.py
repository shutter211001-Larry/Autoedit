import sys
import os
import json
import time
import math
import argparse
import numpy as np
import torch

# Ensure output is UTF-8 encoded to prevent console encoding issues
if sys.stdout.encoding != 'utf-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except Exception:
        pass

# Add local path to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import our modular library scripts
from core.resolve_api import (
    connect_to_resolve,
    setup_project_and_timeline,
    force_gui_refresh,
    import_bgm_if_needed,
    clear_scratch_audio,
    append_video_sequence,
    append_bgm,
    append_outro_logos,
    apply_director_motions_and_grades
)
from core.beat_detector import analyze_audio_beats, find_best_climax_window
from core.cv_analyzer import find_optimal_stable_unidirectional_window
from core.aesthetic_gate import (
    load_metadata_cache,
    extract_features_and_cache,
    load_clip_model,
    encode_text_prompts,
    score_assets
)
from diagnostics.track_diagnoser import diagnose_timeline

def get_resolve_folder(media_pool, local_path):
    """
    Locates the matching folder in Resolve's Media Pool structure dynamically
    based on suffixes of the local directory path, falling back to recursive search.
    """
    root_folder = media_pool.GetRootFolder()
    parts = [p for p in local_path.replace("\\", "/").split("/") if p]
    
    def find_folder_recursive(current_folder, path_parts):
        if not path_parts:
            return current_folder
        target = path_parts[0]
        sub_folders = current_folder.GetSubFolderList() or []
        for sub in sub_folders:
            if sub.GetName().lower() == target.lower():
                res = find_folder_recursive(sub, path_parts[1:])
                if res:
                    return res
        return None

    # Search by matching subdirectories
    for i in range(len(parts)):
        sub_parts = parts[i:]
        folder = find_folder_recursive(root_folder, sub_parts)
        if folder:
            return folder
            
    # Fallback to recursively locating the leaf folder
    leaf_folder = parts[-1] if parts else "CLIP"
    def find_any_folder_by_name(current_folder, name):
        if current_folder.GetName().lower() == name.lower():
            return current_folder
        for sub in current_folder.GetSubFolderList() or []:
            res = find_any_folder_by_name(sub, name)
            if res:
                return res
        return None
        
    folder = find_any_folder_by_name(root_folder, leaf_folder)
    if folder:
        return folder
        
    return root_folder

def run_precache(config_data):
    """
    Builds both CLIP visual semantics metadata cache (.pkl) and
    optical flow motion profiles cache (.json) for all video assets.
    """
    media_dir = config_data.get("media_folder_path")
    if not os.path.exists(media_dir):
        print(f"❌ Error: Media directory '{media_dir}' does not exist.")
        sys.exit(1)
        
    cache_dir = os.path.join(root_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    pkl_path = os.path.join(cache_dir, "video_metadata.pkl")
    json_path = os.path.join(cache_dir, ".cv_profile_cache.json")
    
    print("\n⚡ Step 1: Pre-caching Semantic CLIP Embeddings...")
    extract_features_and_cache(media_dir, pkl_path)
    
    print("\n⚡ Step 2: Pre-caching Optical Flow & Stability Profiles...")
    video_files = [
        os.path.join(media_dir, f)
        for f in os.listdir(media_dir)
        if f.lower().endswith((".mp4", ".mov"))
    ]
    
    # Process each video to ensure it resides in cv_analyzer's cache
    # We pass a dummy duration and fps since we just want to trigger extraction if missing
    for idx, path in enumerate(video_files, 1):
        filename = os.path.basename(path)
        print(f"   [{idx}/{len(video_files)}] Extracting motion curves: '{filename}'...")
        find_optimal_stable_unidirectional_window(path, 120, 24.0, json_path)
        
    print("\n🎉 Pre-caching successfully finished! All assets are fully compiled and optimized.")

def run_editing_engine(config_data, aesthetic_override=None, vertical_override=None):
    """
    Orchestrates the entire modular movie director edit timeline pipeline.
    """
    print("\n" + "="*60)
    print("🎬 AI FILM DIRECTOR ENGINE — MODULAR REVOLUTION Launching...")
    print("="*60)
    
    project_name = config_data.get("project_name")
    timeline_name = config_data.get("timeline_name")
    duration_sec = config_data.get("duration_seconds", 30.0)
    
    is_vertical = vertical_override if vertical_override is not None else config_data.get("source_footage_vertical", True)
    aesthetic_threshold = aesthetic_override if aesthetic_override is not None else config_data.get("aesthetic_threshold", 0.00)
    
    # Setup cache directories
    cache_dir = os.path.join(root_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    pkl_path = os.path.join(cache_dir, "video_metadata.pkl")
    cv_cache_path = os.path.join(cache_dir, ".cv_profile_cache.json")
    
    # 1. Initialize Resolve Connection
    resolve = connect_to_resolve()
    if not resolve:
        sys.exit(1)
        
    # 2. Setup Project, timeline lifecycle & resolution aspect ratios
    current_project, timeline, timeline_start, fps = setup_project_and_timeline(
        resolve, project_name, timeline_name, is_vertical
    )
    if not timeline:
        sys.exit(1)
        
    # 3. Locate, load and crop Climax Audio BGM
    bgm_path_local = config_data.get("bgm_path")
    media_pool = current_project.GetMediaPool()
    bgm_clip = import_bgm_if_needed(media_pool, media_pool.GetRootFolder(), bgm_path_local)
    if not bgm_clip:
        print("❌ Error: BGM audio could not be located or imported.")
        sys.exit(1)
        
    bgm_path = bgm_clip.GetClipProperty("File Path")
    print(f"   🎬 Target BGM File: '{os.path.basename(bgm_path)}'")
    
    print("\n🎧 [AI Music Climax] Locating best climax window...")
    best_t = find_best_climax_window(bgm_path, duration_sec)
    print(f"   🎯 Golden Climax Section: {best_t:.1f}s ➔ {best_t + duration_sec:.1f}s")
    
    # Calculate crop frames for BGM
    bgm_crop_info = {
        "mediaPoolItem": bgm_clip,
        "startFrame": int(best_t * fps),
        "endFrame": int((best_t + duration_sec) * fps),
        "recordFrame": int(timeline_start),
        "trackIndex": 1,
        "mediaType": 2
    }
    
    # 4. Extract beat markers
    print("\n🥁 Step 3: Running transient beat analysis and creating markers...")
    beat_times, bpm = analyze_audio_beats(bgm_path)
    if not beat_times:
        print("❌ Error: No beat markers generated.")
        sys.exit(1)
        
    # Back-extrapolate beats to cover the intro
    beat_interval = 60.0 / bpm
    first_beat = beat_times[0]
    if first_beat > beat_interval:
        extrapolated = []
        curr = first_beat - beat_interval
        while curr >= 0.01:
            extrapolated.append(curr)
            curr -= beat_interval
        if extrapolated:
            extrapolated.reverse()
            beat_times = extrapolated + beat_times
            
    # Clear existing Blue Markers
    try:
        timeline.DeleteMarkersByColor("Blue")
    except Exception:
        pass
        
    LATENCY_OFFSET_SEC = -0.065
    left_offset_sec = best_t
    added_markers = 0
    max_frames = int(duration_sec * fps)
    
    for idx, beat_sec in enumerate(beat_times):
        compensated_sec = beat_sec + LATENCY_OFFSET_SEC
        if compensated_sec < left_offset_sec:
            continue
        abs_frame = timeline_start + int(round((compensated_sec - left_offset_sec) * fps))
        rel_frame = abs_frame - timeline_start
        if rel_frame < 0 or rel_frame > max_frames:
            continue
            
        success = timeline.AddMarker(rel_frame, "Blue", f"Beat {idx+1}", f"AI Beat Cut | File Time: {beat_sec:.2f}s", 1)
        if success:
            added_markers += 1
            
    print(f"   ✅ Generated {added_markers} Blue beat markers on timeline.")
    
    # 5. Connect and set clip active folder in Resolve
    media_folder = config_data.get("media_folder_path")
    clip_folder = get_resolve_folder(media_pool, media_folder)
    media_pool.SetCurrentFolder(clip_folder)
    print(f"   ✅ Target Media Pool clip folder set to: '{clip_folder.GetName()}'")
    
    # 6. Load CLIP semantic metadata cache
    print("\n📂 Loading semantic feature embeddings...")
    metadata_cache = load_metadata_cache(pkl_path)
    if not metadata_cache:
        print("⚠️ CLIP visual cache missing. Performing incremental feature extraction...")
        metadata_cache = extract_features_and_cache(media_folder, pkl_path)
        
    if not metadata_cache:
        print("❌ Error: CLIP visual metadata could not be loaded.")
        sys.exit(1)
        
    # 7. Semantic Storyboarding using CLIP
    print(f"\n🧠 Step 6: Coding narrative prompts & Aesthetic Gate prompts...")
    model, processor, dev = load_clip_model()
    
    AESTHETIC_PROMPTS = {
        "positive": "exquisite professional cinematography, perfect rule-of-thirds composition, beautiful balanced framing, high-end high-contrast commercial video, sharp clean focus on product packaging",
        "negative": "unprofessional messy framing, ugly composition, chaotic clutter, blurry out of focus product, bad lighting, amateur crop, cut-off branding label"
    }
    
    prompt_embeddings, aesthetic_embeddings = encode_text_prompts(
        model, processor, dev,
        config_data.get("prompts"),
        AESTHETIC_PROMPTS["positive"],
        AESTHETIC_PROMPTS["negative"]
    )
    
    # Score video assets
    clip_rankings = score_assets(metadata_cache, prompt_embeddings, aesthetic_embeddings)
    
    # 8. Align story beats with narrative roles
    markers_dict = timeline.GetMarkers()
    all_rel_frames = sorted(list(markers_dict.keys()))
    rel_frames_30s = [f for f in all_rel_frames if f <= max_frames]
    
    # Define timing boundaries
    t_setup = 5.0
    t_detail = 12.0
    t_catwalk = 25.0
    
    setup_markers = []
    detail_markers = []
    climax_markers = []
    finale_markers = []
    
    for f in rel_frames_30s:
        t = f / fps
        if t < t_setup:
            setup_markers.append(f)
        elif t < t_detail:
            detail_markers.append(f)
        elif t < t_catwalk:
            climax_markers.append(f)
        else:
            finale_markers.append(f)
            
    # Dynamic rhythm downsampling
    downsampled_beats = []
    for idx, f in enumerate(setup_markers):
        if idx % 4 == 0:
            downsampled_beats.append((f, "setup"))
    for idx, f in enumerate(detail_markers):
        if idx % 2 == 0:
            downsampled_beats.append((f, "detail"))
    for idx, f in enumerate(climax_markers):
        if idx % 2 == 0:
            downsampled_beats.append((f, "catwalk"))
    for idx, f in enumerate(finale_markers):
        if idx % 4 == 0:
            downsampled_beats.append((f, "finale"))
            
    downsampled_beats.sort(key=lambda x: x[0])
    unique_beats = []
    seen = set()
    for f, role in downsampled_beats:
        if f not in seen:
            unique_beats.append((f, role))
            seen.add(f)
            
    cut_intervals = []
    last_frame = timeline_start
    for rel_frame, role in unique_beats:
        abs_frame = timeline_start + rel_frame
        if abs_frame > last_frame:
            cut_intervals.append((last_frame, abs_frame, role))
            last_frame = abs_frame
            
    if last_frame < timeline_start + max_frames:
        cut_intervals.append((last_frame, timeline_start + max_frames, "finale"))
        
    print(f"🥁 Synced cuts compiled: {len(cut_intervals)} elegant cinematic cuts.")
    
    # 9. Execute storyboarding selection with duplicate defense
    print("\n🎬 Step 7: Executing AI Semantic Matchmaking & Duplicate Defense...")
    motion_energies = [c["motion_energy"] for c in clip_rankings]
    min_motion = min(motion_energies) if motion_energies else 0.0
    max_motion = max(motion_energies) if motion_energies else 1.0
    motion_range = max_motion - min_motion if max_motion != min_motion else 1.0
    
    aesthetic_scores = [c["aesthetic_score"] for c in clip_rankings]
    min_aesthetic = min(aesthetic_scores) if aesthetic_scores else -1.0
    max_aesthetic = max(aesthetic_scores) if aesthetic_scores else 1.0
    aesthetic_range = max_aesthetic - min_aesthetic if max_aesthetic != min_aesthetic else 1.0
    
    all_clips_in_pool = clip_folder.GetClipList() or []
    clip_map = {c.GetName().lower(): c for c in all_clips_in_pool}
    
    available_pool = [c for c in clip_rankings if c["filename"].lower() in clip_map]
    final_clip_sequence = []
    
    print(f"🛡️  AI Aesthetic Gate active. Threshold: {aesthetic_threshold:.3f}")
    
    for idx, interval in enumerate(cut_intervals):
        start_f, end_f, role = interval
        duration_timeline = end_f - start_f
        
        # Determine ideal motion energy based on duration
        if duration_timeline <= 12:
            ideal_motion = 0.9
        elif duration_timeline >= 36:
            ideal_motion = 0.1
        else:
            ideal_motion = 0.9 - ((duration_timeline - 12) / 24.0) * 0.8
            ideal_motion = max(0.1, min(0.9, ideal_motion))
            
        if not available_pool:
            print("   ⚠️ Available unique pool exhausted! Recycling pool...")
            available_pool = [c for c in clip_rankings if c["filename"].lower() in clip_map]
            
        theme_similarities = [c[f"sim_{role}"] for c in available_pool]
        min_sim = min(theme_similarities) if theme_similarities else 0.0
        max_sim = max(theme_similarities) if theme_similarities else 1.0
        sim_range = max_sim - min_sim if max_sim != min_sim else 1.0
        
        selected_embeddings = []
        for chosen in final_clip_sequence:
            name = chosen["name"]
            if name in metadata_cache:
                selected_embeddings.append(np.array(metadata_cache[name]["embedding"]))
                
        best_candidate_idx = None
        best_score = -9999.0
        
        for pool_idx, candidate in enumerate(available_pool):
            cand_emb = np.array(metadata_cache[candidate["filename"]]["embedding"])
            is_near_dup = False
            for s_emb in selected_embeddings:
                cos_sim = float(np.dot(cand_emb, s_emb))
                if cos_sim > 0.88:
                    is_near_dup = True
                    break
                    
            norm_motion = (candidate["motion_energy"] - min_motion) / motion_range
            norm_sim = (candidate[f"sim_{role}"] - min_sim) / sim_range
            motion_score = 1.0 - abs(norm_motion - ideal_motion)
            
            norm_aesthetic = (candidate["aesthetic_score"] - min_aesthetic) / aesthetic_range
            
            # Gold scoring formula: 50% semantics, 20% motion variance, 30% aesthetic
            total_score = 0.5 * norm_sim + 0.2 * motion_score + 0.3 * norm_aesthetic
            
            # Filter low aesthetic scores
            if candidate["aesthetic_score"] < aesthetic_threshold:
                total_score -= 5.0
                
            if is_near_dup:
                total_score -= 2.0
            if candidate["motion_energy"] >= 10.5:
                total_score -= 3.0
                
            if final_clip_sequence:
                prev_motion = final_clip_sequence[-1]["motion"]
                motion_diff = abs(candidate["motion_energy"] - prev_motion)
                if motion_diff > 3.0:
                    total_score -= 0.15 * (motion_diff - 3.0)
                    
            if total_score > best_score:
                best_score = total_score
                best_candidate_idx = pool_idx
                
        best_candidate = available_pool.pop(best_candidate_idx)
        
        from core.director_rules import get_aesthetic_grade
        a_grade = get_aesthetic_grade(best_candidate["aesthetic_score"])
        
        final_clip_sequence.append({
            "item": clip_map[best_candidate["filename"].lower()],
            "name": best_candidate["filename"],
            "role": role,
            "motion": best_candidate["motion_energy"],
            "similarity": best_candidate[f"sim_{role}"],
            "aesthetic_score": best_candidate["aesthetic_score"],
            "aesthetic_grade": a_grade,
            "path": best_candidate["path"]
        })
        
    print(f"   ✅ AI Storyboarding finished successfully ({len(final_clip_sequence)} cuts).")
    
    # 10. Trim and construct sequence list
    print("\n🔨 Step 8: Trimming and Appending Clips onto Video Track 1...")
    
    # Clear Video Tracks
    for t_idx in [1, 2, 3]:
        try:
            video_items = timeline.GetItemListInTrack("video", t_idx)
            if video_items:
                timeline.DeleteClips(video_items)
        except Exception:
            pass
            
    clips_to_append = []
    for idx, interval in enumerate(cut_intervals):
        if idx >= len(final_clip_sequence):
            break
            
        start_f, end_f, role = interval
        duration_timeline = end_f - start_f
        
        clip_data = final_clip_sequence[idx]
        clip_item = clip_data["item"]
        
        try:
            fps_prop = clip_item.GetClipProperty("FPS")
            src_fps = float(fps_prop) if fps_prop else 24.0
        except Exception:
            src_fps = 24.0
            
        scale_factor = src_fps / fps
        duration_source = int(math.ceil(duration_timeline * scale_factor))
        
        frames_prop = clip_item.GetClipProperty("Frames")
        total_frames = int(frames_prop) if (frames_prop and frames_prop.isdigit()) else 240
        
        is_static = (role in ["setup", "finale"])
        file_path = clip_data["path"]
        
        if not is_static and file_path and os.path.exists(file_path):
            src_start = find_optimal_stable_unidirectional_window(
                file_path,
                duration_source,
                src_fps,
                cv_cache_path
            )
        else:
            guard_band = int(total_frames * 0.15)
            safe_total = total_frames - 2 * guard_band
            if safe_total >= duration_source:
                src_start = guard_band + (safe_total - duration_source) // 2
            else:
                src_start = max(0, (total_frames - duration_source) // 2)
                
        src_end = src_start + duration_source
        
        clips_to_append.append({
            "mediaPoolItem": clip_item,
            "startFrame": int(src_start),
            "endFrame": int(src_end)
        })
        
        if idx < 5 or idx == len(cut_intervals) - 1:
            print(f"   [Narrative Arc #{idx+1}] Frame: {start_f}➔{end_f} | Role: {role.upper()} | Similarity: {clip_data['similarity']:.3f} | Motion: {clip_data['motion']:.1f} | Aesthetic: {clip_data['aesthetic_score']:.3f} ({clip_data['aesthetic_grade']}) | Clip: '{clip_data['name']}'")
        elif idx == 5:
            print("   ...")
            
    # 11. Append video clips sequentially
    appended_video = append_video_sequence(media_pool, clips_to_append)
    if appended_video and appended_video[0] is not None:
        print("🎉 SUCCESS! Video clips appended sequentially starting exactly at 86400!")
        
        # Clear scratch field sound
        clear_scratch_audio(timeline)
        
        # Target BGM placement
        bgm_appended = append_bgm(media_pool, bgm_clip, best_t, duration_sec, timeline_start, fps)
        
        # Add branding logos
        logo_start_frame = None
        for interval in cut_intervals:
            start_f, end_f, role = interval
            if role == "finale":
                logo_start_frame = start_f
                break
        if logo_start_frame is None:
            logo_start_frame = timeline_start + int(25.0 * fps)
            
        logo_end_frame = timeline_start + max_frames
        logo_duration = logo_end_frame - logo_start_frame
        
        logo_configs = config_data.get("outro_logos", [])
        append_outro_logos(
            media_pool,
            timeline,
            media_pool.GetRootFolder(),
            logo_configs,
            logo_start_frame,
            logo_duration
        )
        
        # Apply camera motion scales, rotations, markers and node cloning
        apply_director_motions_and_grades(timeline, cut_intervals, is_vertical)
        
        # Refresh focus and verify
        force_gui_refresh(resolve)
        print(f"\n🎉 SUCCESS! AI Director Reorganized Engine finished. Open timeline '{timeline_name}' to see your premium edit!")
    else:
        print("❌ Error: Video append failed. Resolve returned None.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="🎬 AI智慧導演剪輯引擎 (AI Film Director Engine CLI)")
    parser.add_argument("--config", "-c", type=str, required=True, help="Path to JSON configuration file")
    parser.add_argument("--action", "-a", type=str, choices=["run", "diagnose", "precache"], default="run", help="Action to execute")
    parser.add_argument("--threshold", "-t", type=float, default=None, help="Dynamic CLIP aesthetic score threshold override (e.g. 0.00)")
    parser.add_argument("--vertical", "-v", type=str, choices=["true", "false"], default=None, help="Force override vertical video mapping setting")
    
    args = parser.parse_args()
    
    # Load configuration
    if not os.path.exists(args.config):
        print(f"❌ Error: Config file not found at: {args.config}")
        sys.exit(1)
        
    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"❌ Error: Failed to parse configuration JSON: {e}")
        sys.exit(1)
        
    # Parse boolean override
    vertical_override = None
    if args.vertical is not None:
        vertical_override = (args.vertical == "true")
        
    # Execute action
    if args.action == "diagnose":
        timeline_name = config_data.get("timeline_name", "AI_2")
        diagnose_timeline(timeline_name)
    elif args.action == "precache":
        run_precache(config_data)
    elif args.action == "run":
        run_editing_engine(config_data, args.threshold, vertical_override)

if __name__ == "__main__":
    main()
