import os
import sys
import time
import math

# ── 引入 Resolve 21 模組 ──────────────────────────────────────
RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
except ImportError as e:
    print(f"❌ Cannot load DaVinciResolveScript: {e}")
    sys.exit(1)

if not resolve:
    print("❌ DaVinci Resolve is not running. Please open Resolve and your project first.")
    sys.exit(1)

# 引入自研的對拍模組
try:
    import beat_detector
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import beat_detector

def run_beat_tagging():
    print("🚀 Starting AI Automated Audio Beat & Marker Tagging System (Immune to Offset & Silent Intro)...")
    
    project_manager = resolve.GetProjectManager()
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        print("❌ Error: No project is currently open in DaVinci Resolve.")
        sys.exit(1)
        
    timeline = current_project.GetCurrentTimeline()
    if not timeline:
        print("❌ Error: No active timeline found. Please open a timeline first.")
        sys.exit(1)
        
    print(f"🎬 Active Project: '{current_project.GetName()}'")
    print(f"🎞️ Active Timeline: '{timeline.GetName()}'")
    
    # ── 1. 搜尋音軌 1 上的音樂片段 ───────────────────────────────
    audio_items = timeline.GetItemListInTrack("audio", 1)
    if not audio_items:
        print("❌ Error: No audio clips found on Audio Track 1. Please place your background music on Track 1.")
        sys.exit(1)
        
    audio_clip = None
    audio_file_path = None
    
    for item in audio_items:
        mp_item = item.GetMediaPoolItem()
        if mp_item:
            path = mp_item.GetClipProperty("File Path")
            if path and os.path.exists(path):
                audio_clip = item
                audio_file_path = path
                break
                
    if not audio_file_path:
        print("⚠️ Warning: Could not resolve physical file path for Track 1 audio clips.")
        print("Searching active Media Pool folder for audio assets as backup...")
        media_pool = current_project.GetMediaPool()
        current_folder = media_pool.GetCurrentFolder()
        clips = current_folder.GetClipList()
        for clip in clips:
            path = clip.GetClipProperty("File Path")
            if path and path.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".flac")):
                if os.path.exists(path):
                    audio_file_path = path
                    print(f"📌 Found audio asset in Media Pool: '{clip.GetName()}' -> {path}")
                    break
                    
    if not audio_file_path:
        print("❌ Error: No valid audio file path found. Please ensure your music file exists on disk.")
        sys.exit(1)
        
    print(f"🎵 Found target music file: '{os.path.basename(audio_file_path)}'")
    print(f"📂 Path: {audio_file_path}")
    
    # ── 1.1 自動尋找高潮「起承轉合」區間並裁切音軌 ──────────────────────
    timeline_start = timeline.GetStartFrame()
    fps = float(current_project.GetSetting("timelineFrameRate") or 24.0)
    
    duration_frames = 0
    if audio_clip:
        duration_frames = audio_clip.GetEnd() - audio_clip.GetStart()
        
    target_commercial_duration_frames = int(30.0 * fps)
    
    # 如果音樂片段大於 30 秒 (加點微小容差值 48 影格 / 2 秒)，說明是一首完整曲目，進行高潮裁剪！
    if duration_frames > target_commercial_duration_frames + 48:
        print(f"🎬 [AI Music Climax] Music clip is too long ({duration_frames} frames). Triggering AI Cinematic Climax Arc analysis...")
        best_t = beat_detector.find_best_climax_window(audio_file_path, 30.0)
        
        music_media_item = audio_clip.GetMediaPoolItem() if audio_clip else None
        if music_media_item:
            # 清理軌道 1 上的長音軌
            print(f"🧹 [AI Music Climax] Replacing long audio track with 30s climax crop (Source Start: {best_t:.1f}s)...")
            timeline.DeleteClips(audio_items)
            
            # 重新將裁切好的高潮片段放入音軌 1 最開頭 (recordFrame = timeline_start)
            media_pool = current_project.GetMediaPool()
            clips_to_append = [{
                "mediaPoolItem": music_media_item,
                "startFrame": int(best_t * fps),
                "endFrame": int((best_t + 30.0) * fps),
                "recordFrame": int(timeline_start),
                "trackIndex": 1,
                "mediaType": 2
            }]
            
            appended_audio = media_pool.AppendToTimeline(clips_to_append)
            if appended_audio:
                print("✅ [AI Music Climax] Successfully placed 30s Climax Audio Cut onto Audio Track 1!")
                # 重新取得最新的 audio_clip
                new_audio_items = timeline.GetItemListInTrack("audio", 1)
                if new_audio_items:
                    audio_clip = new_audio_items[0]
            else:
                print("❌ [AI Music Climax] Failed to replace audio track. Proceeding with original clip.")
        else:
            print("⚠️ [AI Music Climax] Could not retrieve original MediaPoolItem. Skipping climax cropping.")
            
    # ── 2. 獲取時間軸的關鍵參數 ──────────────────────────────────
    print(f"⚙️ Timeline Start Frame: {timeline_start} | Frame Rate (FPS): {fps}")
    
    # 讀取剪輯軌道的裁切偏移量 (Left Offset)
    left_offset = 0
    audio_start_frame = timeline_start
    if audio_clip:
        audio_start_frame = audio_clip.GetStart()
        try:
            left_offset = audio_clip.GetLeftOffset()
        except Exception:
            left_offset = 0
        print(f"🔗 Music clip timeline start: {audio_start_frame} | Source Left Offset (Trim): {left_offset} frames")
        
    left_offset_sec = left_offset / fps
    
    # ── 3. 呼叫 AI 進行對拍分析 ──────────────────────────────────
    print("\n🎧 Analyzing audio transients... Please wait a few seconds...")
    start_time = time.time()
    beat_times, bpm = beat_detector.analyze_audio_beats(audio_file_path)
    analysis_duration = time.time() - start_time
    
    if not beat_times:
        print("❌ Error: No beats could be detected in this audio file.")
        sys.exit(1)
        
    print(f"🥁 Analysis complete in {analysis_duration:.2f}s! Estimated Tempo: {bpm:.1f} BPM.")
    print(f"⭐ Detected {len(beat_times)} beats originally.")
    
    # 🚀 新增機制：靜音前奏節拍反向外推 (Extrapolate Beats for Silent Intro)
    # 當音樂最前面有靜音或淡入，沒有偵測到節拍時，反向推導規律節拍以保持開頭有卡點
    beat_interval = 60.0 / bpm
    first_beat = beat_times[0]
    
    if first_beat > beat_interval:
        extrapolated_beats = []
        curr = first_beat - beat_interval
        while curr >= 0.01:
            extrapolated_beats.append(curr)
            curr -= beat_interval
        if extrapolated_beats:
            extrapolated_beats.reverse()
            print(f"   💡 Detected silent intro of {first_beat:.2f}s. Extrapolated {len(extrapolated_beats)} rhythmic beats backwards to fill the start.")
            beat_times = extrapolated_beats + beat_times
            
    # ── 4. 清理現有的 AI 藍色節拍標記 ────────────────────────────
    print("\n🧹 Clearing existing Blue markers on the timeline to prevent clutter...")
    try:
        success = timeline.DeleteMarkersByColor("Blue")
        if success:
            print("   Deleted old Blue beat markers.")
        else:
            print("   No old Blue markers to delete.")
    except Exception as e:
        print(f"   Note: Clear markers failed or not needed: {e}")
        
    # ── 5. 將對拍結果轉換為時間軸影格並寫入 ───────────────────────────
    print("✍️ Writing new beat markers to timeline...")
    added_count = 0
    
    # 🚀 延遲補償與剪輯優化偏置 (Latency Compensation & Lead-In Bias)
    # 預設補償 -0.065 秒 (約合 1.5 影格)，用以精準抵消 FFT 滑動視窗與漢寧平滑濾波產生的相位延遲 (約 69.6ms)，
    # 同時提供專業剪輯師偏好的 1 影格「視覺領先卡點（Lead-In Cut）」，確保畫面與聽覺在播放時完美卡點，不顯拖沓！
    LATENCY_OFFSET_SEC = -0.065
    
    for idx, beat_sec in enumerate(beat_times):
        # 應用延遲補償
        compensated_sec = beat_sec + LATENCY_OFFSET_SEC
        
        # 🚀 裁切免疫計算：排除被裁切掉的開頭節拍，並偏移時間軸座標
        if compensated_sec < left_offset_sec:
            continue
            
        # 計算時間軸上的「絕對」影格位置
        # (compensated_sec - left_offset_sec) 是相對於裁切後音樂片段在時間軸起點的播放時間
        absolute_frame = audio_start_frame + int(round((compensated_sec - left_offset_sec) * fps))
        
        # 🚀 關鍵修正：達芬奇 AddMarker API 接收的 frameId 必須是「相對於時間軸起點的相對影格數」！
        relative_frame = absolute_frame - timeline_start
        
        # 確保不會寫入小於 0 的非法相對影格
        if relative_frame < 0:
            continue
            
        marker_name = f"Beat {idx+1}"
        marker_note = f"AI Beat Cut | Time in File: {beat_sec:.2f}s"
        
        success = timeline.AddMarker(
            relative_frame,
            "Blue",
            marker_name,
            marker_note,
            1
        )
        if success:
            added_count += 1
            if added_count <= 5 or idx == len(beat_times) - 1:
                print(f"   [Marker #{added_count}] Added Blue marker at relative frame {relative_frame} (Absolute: {absolute_frame} | {beat_sec:.2f}s)")
            elif added_count == 6:
                print("   ...")
                
    print(f"\n🎉 SUCCESS! Written {added_count} Blue beat markers to timeline '{timeline.GetName()}'!")
    print("👉 You can now run 'run_cinematic_auto_edit.py' to automatically perform a Director's Cut matching these markers!")

if __name__ == "__main__":
    run_beat_tagging()
