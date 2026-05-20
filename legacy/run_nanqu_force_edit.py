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
    print(f"Error: {e}"); sys.exit(1)

project_manager = resolve.GetProjectManager()
current_project = project_manager.GetCurrentProject()
media_pool = current_project.GetMediaPool()

# ── 1. 切換至「南區工作」時間軸 ───────────────────────────────
timeline_count = current_project.GetTimelineCount()
target_timeline = None
for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    if "南區工作" in tl.GetName():
        target_timeline = tl
        break

if target_timeline:
    current_project.SetCurrentTimeline(target_timeline)
    print(f"✅ Active timeline set to: '{target_timeline.GetName()}'")
else:
    print("Error: '南區工作' timeline not found.")
    sys.exit(1)

# ── 2. 強制將 Media Pool 當前資料夾切換至 CLIP ─────────────────
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
    print("Error: Master/Video/D2/CLIP folder not found.")
    sys.exit(1)

# ⭐️ 關鍵關鍵：強制設定 Media Pool 的目前資料夾，讓 AppendToTimeline 絕不失手！
media_pool.SetCurrentFolder(clip_folder)
print(f"📁 Force set Media Pool current folder to: '{clip_folder.GetName()}'")

# ── 3. 讀取 BGM 音樂與時間軸節拍 Markers ───────────────────────
bgm_clip = find_clip_recursive = None
# 用更直接的方式在整個 Master 尋找音樂
def find_bgm(folder):
    for clip in folder.GetClipList():
        if "Pawn" in clip.GetName() or "Golden Palms" in clip.GetName():
            return clip
    for sub in folder.GetSubFolderList():
        res = find_bgm(sub)
        if res:
            return res
    return None

bgm_clip = find_bgm(root_folder)

# 確保音樂在 Audio Track 1
if bgm_clip:
    try:
        audio_items = target_timeline.GetItemListInTrack("audio", 1)
        if audio_items:
            target_timeline.DeleteClips(audio_items)
    except Exception:
        pass
    media_pool.AppendToTimeline([{"mediaPoolItem": bgm_clip, "mediaType": 2, "trackIndex": 1}])
    print("🎵 Background Music appended to Audio Track 1.")

# 重新生成 22 個節奏節拍點 Markers (120 BPM)
target_timeline.DeleteMarkersByColor("Blue")
fps = float(current_project.GetSetting("timelineFrameRate") or 24.0)

beat_pattern = [
    4, 4, 2, 2, 1, 1, 1, 1,
    4, 4, 2, 2, 1, 1, 1, 1,
    4, 4, 2, 2, 2, 2
]

beat_frames = []
current_frame = target_timeline.GetStartFrame()
for idx, beats in enumerate(beat_pattern):
    duration_frames = int(beats * (fps * 60 / 120))
    current_frame += duration_frames
    beat_frames.append(current_frame)
    target_timeline.AddMarker(current_frame, "Blue", f"Beat {idx+1}", "", 1)

cut_intervals = []
last_frame = target_timeline.GetStartFrame()
for beat in beat_frames:
    cut_intervals.append((last_frame, beat))
    last_frame = beat

# ── 4. 讀取並分配影片素材 (AI 智慧分配 + 嚴格去重) ───────────────
all_clips = clip_folder.GetClipList()
good_takes = {"Wide": [], "Medium": [], "CloseUp": [], "Unsorted": []}
seen_paths = set()
seen_signatures = set()

# 直接進行 AI 自動篩選分配
for idx, clip in enumerate(all_clips):
    # 去重
    file_path = clip.GetClipProperty("File Path")
    if file_path:
        if file_path in seen_paths: continue
        seen_paths.add(file_path)

    duration = clip.GetClipProperty("Duration")
    frames = clip.GetClipProperty("Frames")
    signature = (duration, frames)
    if duration and frames:
        if signature in seen_signatures: continue
        seen_signatures.add(signature)

    shot_type = clip.GetClipProperty("Description").strip()
    movement = clip.GetClipProperty("Comments").strip()
    clip_info = {"item": clip, "name": clip.GetName(), "movement": movement}

    if "wide" in shot_type.lower():
        good_takes["Wide"].append(clip_info)
    elif "medium" in shot_type.lower() or "mcu" in shot_type.lower():
        good_takes["Medium"].append(clip_info)
    elif "closeup" in shot_type.lower() or "cu" in shot_type.lower():
        good_takes["CloseUp"].append(clip_info)
    else:
        good_takes["Unsorted"].append(clip_info)

# ── 5. 排序影片故事線 ─────────────────────────────────────────
shot_sequence_pattern = ["Wide", "Medium", "CloseUp", "Medium"]
final_clip_sequence = []

def get_best_clip(pool, last_mov):
    if not pool: return None
    for i, c in enumerate(pool):
        if last_mov == "TL->BR" and "BR" in c["movement"]: return pool.pop(i)
        if last_mov == "L->R" and "R->" in c["movement"]: return pool.pop(i)
    return pool.pop(0)

last_mov = "Static"
pattern_idx = 0
for _ in range(len(cut_intervals)):
    desired = shot_sequence_pattern[pattern_idx % len(shot_sequence_pattern)]
    pool = good_takes[desired]
    if not pool:
        for alt in ["Medium", "CloseUp", "Wide", "Unsorted"]:
            if good_takes[alt]: pool = good_takes[alt]; break
    clip = get_best_clip(pool, last_mov)
    if clip:
        final_clip_sequence.append(clip)
        last_mov = clip["movement"]
    pattern_idx += 1

# ── 6. 清理 Video 軌道 1 並寫入時間軸 ──────────────────────────
try:
    video_items = target_timeline.GetItemListInTrack("video", 1)
    if video_items:
        target_timeline.DeleteClips(video_items)
except Exception:
    pass

clips_to_append = []
for idx, interval in enumerate(cut_intervals):
    if idx >= len(final_clip_sequence): break
    start_f, end_f = interval
    dur = end_f - start_f
    
    clip_data = final_clip_sequence[idx]
    clip_item = clip_data["item"]
    
    frames_prop = clip_item.GetClipProperty("Frames")
    total_f = int(frames_prop) if frames_prop else 240
    
    src_start = max(0, (total_f - dur) // 2)
    src_end = src_start + dur
    
    clips_to_append.append({
        "mediaPoolItem": clip_item,
        "startFrame": int(src_start),
        "endFrame": int(src_end),
        "recordFrame": int(start_f),
        "trackIndex": 1
    })

# 執行強行組裝
appended = media_pool.AppendToTimeline(clips_to_append)
if appended:
    print(f"🎉 SUCCESS! Force appended {len(appended)} video clips to timeline '南區工作'!")
    resolve.OpenPage("edit")
else:
    print("Error: Append failed.")
