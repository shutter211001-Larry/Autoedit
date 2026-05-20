import sys
import os

# ── Resolve 21 初始化 ────────────────────────────────────────
RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
except ImportError as e:
    print(f"Error: Cannot load DaVinciResolveScript: {e}")
    sys.exit(1)

if not resolve:
    print("Error: Resolve not running.")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
current_project = project_manager.GetCurrentProject()

if not current_project:
    print("Error: No open project.")
    sys.exit(1)

media_pool = current_project.GetMediaPool()

# ── 1. 定位並切換至「南區工作」時間軸 ───────────────────────────
timeline_count = current_project.GetTimelineCount()
target_timeline = None

for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    if "南區工作" in tl.GetName():
        target_timeline = tl
        break

if target_timeline:
    current_project.SetCurrentTimeline(target_timeline)
    print(f"✅ Successfully switched active timeline to: '{target_timeline.GetName()}'")
else:
    print("⚠️ Timeline '南區工作' not found. Creating a new one...")
    target_timeline = media_pool.CreateEmptyTimeline("南區工作")
    if not target_timeline:
        print("Error: Failed to create timeline '南區工作'.")
        sys.exit(1)

# ── 2. 讀取「南區工作」時間軸上的音樂節拍 Markers ─────────────────
markers = target_timeline.GetMarkers()
if not markers:
    print("\n[STOP] No beat markers found on timeline '南區工作'.")
    print("👉 Please select your audio track, right-click and use Fairlight 'Detect Beats', or manually press 'M' to add markers, then run again!")
    sys.exit(0)

beat_frames = sorted(list(markers.keys()))
print(f"🎵 Found {len(beat_frames)} beat markers for cinematic cuts.")

cut_intervals = []
timeline_start = target_timeline.GetStartFrame()
last_frame = timeline_start

for beat in beat_frames:
    cut_intervals.append((last_frame, beat))
    last_frame = beat

# ── 3. 導航並讀取 CLIP 資料夾 ──────────────────────────────────
def find_folder_recursive(current_folder, path_parts):
    if not path_parts:
        return current_folder
    target = path_parts[0]
    sub_folders = current_folder.GetSubFolderList()
    for sub in sub_folders:
        if sub.GetName().lower() == target.lower():
            return find_folder_recursive(sub, path_parts[1:])
    return None

root_folder = media_pool.GetRootFolder()
clip_folder = find_folder_recursive(root_folder, ["Video", "D2", "CLIP"])

if not clip_folder:
    print("Error: CLIP folder not found.")
    sys.exit(1)

all_clips = clip_folder.GetClipList()

# ── 4. 嚴格篩選 (Good Takes) 與防重機制 ──────────────────────────
good_takes = {
    "Wide": [],
    "Medium": [],
    "CloseUp": [],
    "Unsorted": []
}

seen_paths = set()
seen_signatures = set()
duplicate_count = 0

print("🔍 Analyzing media pool metadata for 'Good Take' markers...")
for clip in all_clips:
    # 僅讀取勾選 "Good Take" 的素材
    good_take_prop = clip.GetClipProperty("Good Take")
    if not good_take_prop or good_take_prop.strip().lower() not in ("1", "yes", "true"):
        continue

    # 檔案路徑去重
    file_path = clip.GetClipProperty("File Path")
    if file_path:
        if file_path in seen_paths:
            duplicate_count += 1
            continue
        seen_paths.add(file_path)

    # 影格時長特徵去重
    duration = clip.GetClipProperty("Duration")
    frames = clip.GetClipProperty("Frames")
    signature = (duration, frames)
    if duration and frames:
        if signature in seen_signatures:
            duplicate_count += 1
            continue
        seen_signatures.add(signature)

    # 讀取分類與動態標籤
    shot_type = clip.GetClipProperty("Description").strip()
    movement = clip.GetClipProperty("Comments").strip()
    
    clip_info = {
        "item": clip,
        "name": clip.GetName(),
        "movement": movement if movement else "Static"
    }

    if "wide" in shot_type.lower():
        good_takes["Wide"].append(clip_info)
    elif "medium" in shot_type.lower() or "mcu" in shot_type.lower():
        good_takes["Medium"].append(clip_info)
    elif "closeup" in shot_type.lower() or "cu" in shot_type.lower():
        good_takes["CloseUp"].append(clip_info)
    else:
        good_takes["Unsorted"].append(clip_info)

print(f"✅ Filter Results (Excluded {duplicate_count} duplicates):")
print(f"  • Wide: {len(good_takes['Wide'])} | Medium: {len(good_takes['Medium'])} | CloseUp: {len(good_takes['CloseUp'])}")

total_good_takes = sum(len(v) for v in good_takes.values())
if total_good_takes == 0:
    print("\n[STOP] No 'Good Take' checked clips found in CLIP folder!")
    print("👉 Please select your favorite clips in Resolve, and CHECK the 'Good Take' checkbox in the Metadata panel.")
    sys.exit(0)

# ── 5. 鏡位組合與動態連貫性排列 ───────────────────────────────
shot_sequence_pattern = ["Wide", "Medium", "CloseUp", "Medium"]
final_clip_sequence = []

def get_best_matching_clip(shot_pool, last_movement):
    if not shot_pool:
        return None
    for i, clip in enumerate(shot_pool):
        if last_movement == "TL->BR" and "BR" in clip["movement"]:
            return shot_pool.pop(i)
        if last_movement == "L->R" and "R->" in clip["movement"]:
            return shot_pool.pop(i)
    return shot_pool.pop(0)

last_movement = "Static"
pattern_idx = 0

for _ in range(len(cut_intervals)):
    desired_type = shot_sequence_pattern[pattern_idx % len(shot_sequence_pattern)]
    pool = good_takes[desired_type]
    
    if not pool:
        for alternative in ["Medium", "CloseUp", "Wide", "Unsorted"]:
            if good_takes[alternative]:
                pool = good_takes[alternative]
                break
                
    clip = get_best_matching_clip(pool, last_movement)
    if clip:
        final_clip_sequence.append(clip)
        last_movement = clip["movement"]
    pattern_idx += 1

# ── 6. 清理「南區工作」時間軸並開始剪輯對位 ────────────────────────
try:
    video_items = target_timeline.GetItemListInTrack("video", 1)
    if video_items:
        print(f"Cleaning {len(video_items)} existing clips on Video Track 1...")
        target_timeline.DeleteClips(video_items)
except Exception as e:
    print(f"Clear timeline failed: {e}")

clips_to_append = []
fps = float(current_project.GetSetting("timelineFrameRate") or 24.0)

for idx, interval in enumerate(cut_intervals):
    if idx >= len(final_clip_sequence):
        print(f"⚠️ Warning: Not enough Good Takes ({len(final_clip_sequence)}) to fill all {len(cut_intervals)} beat markers.")
        break
        
    start_timecode_frame, end_timecode_frame = interval
    duration_frames = end_timecode_frame - start_timecode_frame
    
    clip_data = final_clip_sequence[idx]
    clip_item = clip_data["item"]
    
    frames_prop = clip_item.GetClipProperty("Frames")
    total_frames = int(frames_prop) if frames_prop else 240
    
    src_start = max(0, (total_frames - duration_frames) // 2)
    src_end = src_start + duration_frames
    
    clips_to_append.append({
        "mediaPoolItem": clip_item,
        "startFrame": int(src_start),
        "endFrame": int(src_end),
        "recordFrame": int(start_timecode_frame),
        "trackIndex": 1
    })
    print(f"🎬 Cut #{idx+1} | Frame: {start_timecode_frame}➔{end_timecode_frame} | Clip: {clip_data['name']} ({desired_type})")

# 執行組裝
appended = media_pool.AppendToTimeline(clips_to_append)
if appended:
    print(f"\n🎉 SUCCESS! Professional Cinematic Edit completed on timeline '南區工作'!")
    resolve.OpenPage("edit")
else:
    print("Error: Append failed.")
