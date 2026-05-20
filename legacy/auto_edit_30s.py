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

# 確保專案是 2605_BCbonacure
if not current_project or current_project.GetName() != "2605_BCbonacure":
    print("Switching project to '2605_BCbonacure'...")
    # 嘗試載入
    project_manager.LoadProject("2605_BCbonacure")
    current_project = project_manager.GetCurrentProject()

if not current_project:
    print("Error: Project '2605_BCbonacure' could not be loaded.")
    sys.exit(1)

media_pool = current_project.GetMediaPool()
if not media_pool:
    print("Error: Cannot access MediaPool.")
    sys.exit(1)

# ── 1. 導航至 Timeline 2 ─────────────────────────────────────
# 遍歷時間軸，尋找 Timeline 2
timeline_count = current_project.GetTimelineCount()
target_timeline = None
for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    if "Timeline 2" in tl.GetName():
        target_timeline = tl
        break

if target_timeline:
    current_project.SetCurrentTimeline(target_timeline)
    print(f"Active timeline set to: '{target_timeline.GetName()}'")
else:
    current_timeline = current_project.GetCurrentTimeline()
    if current_timeline and "Timeline 2" in current_timeline.GetName():
        target_timeline = current_timeline
        print(f"Already on timeline: '{target_timeline.GetName()}'")
    else:
        print("Error: 'Timeline 2' not found. Creating a new one...")
        target_timeline = media_pool.CreateEmptyTimeline("Timeline 2")
        if not target_timeline:
            print("Error: Failed to create 'Timeline 2'.")
            sys.exit(1)

# ── 2. 尋找 Bin 資料夾 (Master/Video/D2/CLIP) ───────────────
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
# 搜尋路徑 Video -> D2 -> CLIP
target_path = ["Video", "D2", "CLIP"]
clip_folder = find_folder_recursive(root_folder, target_path)

if not clip_folder:
    print(f"Error: Could not navigate to Bin: {r'Master\Video\D2\CLIP'}")
    # 嘗試印出 Root 下的子資料夾做為診斷
    print("Available root subfolders:")
    for f in root_folder.GetSubFolderList():
        print(f"  - {f.GetName()}")
    sys.exit(1)

print(f"Successfully entered Bin: {clip_folder.GetName()}")

# ── 3. 取得素材清單 ──────────────────────────────────────────
clips = clip_folder.GetClipList()
if not clips:
    print("Error: No clips found in Master/Video/D2/CLIP.")
    sys.exit(1)

print(f"Found {len(clips)} source clips.")

# ── 4. 智慧剪輯邏輯：計算每個 Clip 的秒數以湊滿 30 秒 ──────────
# 讀取時間軸 FPS
fps_setting = current_project.GetSetting("timelineFrameRate")
try:
    fps = float(fps_setting) if fps_setting else 24.0
except ValueError:
    fps = 24.0

target_duration_seconds = 30
total_target_frames = int(target_duration_seconds * fps)

# 限制最大素材數量以確保單片段有足夠長度（最少 1 秒/24幀）
max_clips = total_target_frames // int(fps)
if len(clips) > max_clips:
    print(f"Too many clips ({len(clips)}). Capping to {max_clips} clips to preserve readability.")
    clips = clips[:max_clips]

num_clips = len(clips)
frames_per_clip = total_target_frames // num_clips

print(f"Timeline FPS: {fps}")
print(f"Target duration: 30s ({total_target_frames} frames)")
print(f"Clips used: {num_clips}, allocation per clip: {frames_per_clip} frames (~{frames_per_clip/fps:.2f}s)")

# 解析素材總幀數的工具函式
def get_clip_total_frames(media_item, default_fps):
    # 優先嘗試 "Frames" 欄位
    frames_prop = media_item.GetClipProperty("Frames")
    if frames_prop:
        try:
            return int(frames_prop)
        except ValueError:
            pass
    # 備用：解析 "Duration" 時間碼
    dur_prop = media_item.GetClipProperty("Duration")
    if dur_prop:
        try:
            parts = dur_prop.split(":")
            if len(parts) == 4: # HH:MM:SS:FF
                h, m, s, f = map(int, parts)
                return int(((h * 3600 + m * 60 + s) * default_fps) + f)
            elif len(parts) == 3: # HH:MM:SS
                h, m, s = map(int, parts)
                return int((h * 3600 + m * 60 + s) * default_fps)
        except ValueError:
            pass
    return 240 # 預設假設有 10 秒素材

# ── 5. 清理時間軸上現有內容 ──────────────────────────────────
# 清理 Video 軌道 1 上舊有的素材，確保新剪輯結果乾淨
try:
    video_items = target_timeline.GetItemListInTrack("video", 1)
    if video_items:
        print(f"Clearing {len(video_items)} existing clips on Video Track 1...")
        target_timeline.DeleteClips(video_items)
except Exception as e:
    print(f"Warning during timeline clear: {e}")

# ── 6. 批次加入時間軸 ─────────────────────────────────────────
clips_to_append = []
for clip in clips:
    clip_total = get_clip_total_frames(clip, fps)
    
    # 智慧裁切：擷取素材「中間段落」避開開頭與結尾的晃動或黑影
    if clip_total > frames_per_clip:
        start_frame = (clip_total - frames_per_clip) // 2
    else:
        start_frame = 0
    end_frame = start_frame + frames_per_clip
    
    clips_to_append.append({
        "mediaPoolItem": clip,
        "startFrame": int(start_frame),
        "endFrame": int(end_frame)
    })
    print(f"  • Clip: {clip.GetName()} | Total Frames: {clip_total} -> Use: [{start_frame} - {end_frame}]")

# 使用 AppendToTimeline 批次生成 30 秒故事線
appended_items = media_pool.AppendToTimeline(clips_to_append)

if appended_items:
    print(f"Successfully appended {len(appended_items)} clips to timeline!")
    # 開啟剪輯頁面方便用戶查看
    resolve.OpenPage("edit")
    print("Project switched to Edit Page.")
else:
    print("Error: Failed to append clips to timeline.")
    sys.exit(1)
