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

# ── 1. 定位或建立「南區工作」時間軸 ───────────────────────────
timeline_count = current_project.GetTimelineCount()
target_timeline = None

for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    if "南區工作" in tl.GetName():
        target_timeline = tl
        break

if target_timeline:
    current_project.SetCurrentTimeline(target_timeline)
    print(f"✅ Active timeline: '{target_timeline.GetName()}'")
else:
    target_timeline = media_pool.CreateEmptyTimeline("南區工作")
    print(f"✅ Created empty timeline: '南區工作'")

# ── 2. 在媒體池中尋找指定的背景音樂 ────────────────────────────
def find_clip_recursive(folder, filename):
    # 檢查當前資料夾的 clips
    for clip in folder.GetClipList():
        if filename.lower() in clip.GetName().lower():
            return clip
    # 搜尋子資料夾
    for sub in folder.GetSubFolderList():
        res = find_clip_recursive(sub, filename)
        if res:
            return res
    return None

root_folder = media_pool.GetRootFolder()
bgm_name = "Pawn - The Grey Room _ Golden Palms.mp3"
bgm_clip = find_clip_recursive(root_folder, bgm_name)

if not bgm_clip:
    # 嘗試模糊搜尋 "Pawn" 或 "Golden Palms"
    bgm_clip = find_clip_recursive(root_folder, "Pawn")
    if not bgm_clip:
        bgm_clip = find_clip_recursive(root_folder, "Golden Palms")

if bgm_clip:
    print(f"🎵 Found Background Music: '{bgm_clip.GetName()}'")
    # 清除音軌 1 上舊有的音樂，並重新導入
    try:
        audio_items = target_timeline.GetItemListInTrack("audio", 1)
        if audio_items:
            target_timeline.DeleteClips(audio_items)
    except Exception:
        pass
    
    # 導入音樂至 Audio Track 1
    media_pool.AppendToTimeline([{"mediaPoolItem": bgm_clip, "mediaType": 2, "trackIndex": 1}])
    print("  -> Music appended to Audio Track 1 successfully!")
else:
    print(f"⚠️ Warning: Could not find music '{bgm_name}' in Media Pool. Please import it first.")

# ── 3. AI 音樂節奏生成器 (120 BPM / 24 FPS) ────────────────────
fps_setting = current_project.GetSetting("timelineFrameRate")
try:
    fps = float(fps_setting) if fps_setting else 24.0
except ValueError:
    fps = 24.0

# 120 BPM = 每秒 2 拍。在 24 FPS 下，1 拍 = 12 幀。
# 建立一個充滿呼吸感與電影律動的節奏切點 Pattern (拍數列表)
# 總計 56 拍 = 28 秒的精緻 MV 結構
beat_pattern = [
    4, 4,       # 開頭交代：2.0s, 2.0s (情緒鋪陳)
    2, 2,       # 節奏漸快：1.0s, 1.0s
    1, 1, 1, 1, # 極速高潮：0.5s, 0.5s, 0.5s, 0.5s (快速閃切)
    4, 4,       # 釋放情緒：2.0s, 2.0s (大遠景/慢動作)
    2, 2,       # 再次推進：1.0s, 1.0s
    1, 1, 1, 1, # 二次閃切：0.5s, 0.5s, 0.5s, 0.5s
    4, 4,       # 收尾放慢：2.0s, 2.0s
    2, 2, 2, 2  # 結尾淡出：1.0s, 1.0s, 1.0s, 1.0s
]

# 清除舊的節拍 Markers
target_timeline.DeleteMarkersByColor("Blue")

# 生成精確的影格時間點，並在時間軸上畫上 Blue Markers
beat_frames = []
timeline_start = target_timeline.GetStartFrame()
current_frame = timeline_start

for idx, beats in enumerate(beat_pattern):
    duration_frames = int(beats * (fps * 60 / 120)) # 精確算出此切點的影格數
    current_frame += duration_frames
    beat_frames.append(current_frame)
    # 在時間軸上打上節拍標記
    target_timeline.AddMarker(
        current_frame, 
        "Blue", 
        f"Beat {idx+1}", 
        f"Duration: {beats} beats", 
        1
    )

print(f"⚡ Generated {len(beat_frames)} synced beat markers on the timeline!")

# 計算影格切點區間
cut_intervals = []
last_frame = timeline_start
for beat in beat_frames:
    cut_intervals.append((last_frame, beat))
    last_frame = beat

# ── 4. 尋找 CLIP 資料夾並分類素材 ──────────────────────────────
def find_folder_recursive(current_folder, path_parts):
    if not path_parts:
        return current_folder
    target = path_parts[0]
    sub_folders = current_folder.GetSubFolderList()
    for sub in sub_folders:
        if sub.GetName().lower() == target.lower():
            return find_folder_recursive(sub, path_parts[1:])
    return None

clip_folder = find_folder_recursive(root_folder, ["Video", "D2", "CLIP"])
if not clip_folder:
    print("Error: CLIP folder not found.")
    sys.exit(1)

all_clips = clip_folder.GetClipList()

# 分類容器
good_takes = {
    "Wide": [],
    "Medium": [],
    "CloseUp": [],
    "Unsorted": []
}

seen_paths = set()
seen_signatures = set()
duplicate_count = 0
manual_good_takes_count = 0

# 先掃描看看使用者是否有手動勾選 "Good Take"
for clip in all_clips:
    good_take_prop = clip.GetClipProperty("Good Take")
    if good_take_prop and good_take_prop.strip().lower() in ("1", "yes", "true"):
        manual_good_takes_count += 1

use_fallback = (manual_good_takes_count == 0)
if use_fallback:
    print("ℹ️ No manual 'Good Take' checked by user. AI Auto-Selection activated to run the edit!")

for clip in all_clips:
    # 如果使用者有手動勾選，嚴格遵循使用者；若無，自動使用全部素材
    if not use_fallback:
        good_take_prop = clip.GetClipProperty("Good Take")
        if not good_take_prop or good_take_prop.strip().lower() not in ("1", "yes", "true"):
            continue

    # 去重機制
    file_path = clip.GetClipProperty("File Path")
    if file_path:
        if file_path in seen_paths:
            duplicate_count += 1
            continue
        seen_paths.add(file_path)

    duration = clip.GetClipProperty("Duration")
    frames = clip.GetClipProperty("Frames")
    signature = (duration, frames)
    if duration and frames:
        if signature in seen_signatures:
            duplicate_count += 1
            continue
        seen_signatures.add(signature)

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

print(f"✅ Pool Statistics (Excluded {duplicate_count} duplicates):")
print(f"  • Wide: {len(good_takes['Wide'])} | Medium: {len(good_takes['Medium'])} | CloseUp: {len(good_takes['CloseUp'])}")

# ── 5. 經典敘事鏡位與連貫性排列 ───────────────────────────────
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

# ── 6. 清理時間軸並開始精準對位剪輯 ────────────────────────────
try:
    video_items = target_timeline.GetItemListInTrack("video", 1)
    if video_items:
        print(f"Cleaning {len(video_items)} old video clips on Track 1...")
        target_timeline.DeleteClips(video_items)
except Exception as e:
    print(f"Clear timeline failed: {e}")

clips_to_append = []

for idx, interval in enumerate(cut_intervals):
    if idx >= len(final_clip_sequence):
        print(f"⚠️ Warning: Not enough clips to fill all {len(cut_intervals)} beat markers.")
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
    print(f"🎬 Cut #{idx+1} | Frame: {start_timecode_frame}➔{end_timecode_frame} ({duration_frames} f) | Clip: {clip_data['name']}")

# 執行組裝
appended = media_pool.AppendToTimeline(clips_to_append)
if appended:
    print(f"\n🎉 SUCCESS! MV Beat-Synced Cinematic Edit completed on timeline '南區工作'!")
    resolve.OpenPage("edit")
else:
    print("Error: Append failed.")
