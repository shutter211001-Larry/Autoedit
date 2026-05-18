import sys
import os
import base64

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
root_folder = media_pool.GetRootFolder()

# ── 1. 導航至 CLIP 資料夾 ─────────────────────────────────────
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
    print("Error: Cannot find folder Master/Video/D2/CLIP.")
    sys.exit(1)

clips = clip_folder.GetClipList()
if not clips:
    print("Error: No clips found.")
    sys.exit(1)

# 限制分析前 10 個做為測試，避免生成過多檔案
clips_to_analyze = clips[:10]
print(f"Preparing to export thumbnails for {len(clips_to_analyze)} clips...")

# ── 2. 建立臨時分析時間軸 ──────────────────────────────────────
# 先刪除舊的同名時間軸以防衝突
timelines = [current_project.GetTimelineByIndex(i) for i in range(1, current_project.GetTimelineCount() + 1)]
for tl in timelines:
    if tl.GetName() == "Temp_AI_Analysis":
        media_pool.DeleteTimelines([tl])
        print("Deleted existing Temp_AI_Analysis timeline.")

temp_timeline = media_pool.CreateEmptyTimeline("Temp_AI_Analysis")
if not temp_timeline:
    print("Error: Failed to create temporary timeline.")
    sys.exit(1)

# 將測試素材全部丟進臨時時間軸
media_pool.AppendToTimeline(clips_to_analyze)

# ── 3. 影格轉時間碼工具 ────────────────────────────────────────
fps_setting = current_project.GetSetting("timelineFrameRate")
try:
    fps = float(fps_setting) if fps_setting else 24.0
except ValueError:
    fps = 24.0

def frames_to_timecode(frames, fps):
    h = int(frames // (3600 * fps))
    m = int((frames % (3600 * fps)) // (60 * fps))
    s = int(((frames % (3600 * fps)) % (60 * fps)) // fps)
    f = int(((frames % (3600 * fps)) % (60 * fps)) % fps)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"

# ── 4. 逐個擷取縮圖並儲存 ──────────────────────────────────────
output_dir = r"C:\TEST\thumbnails"
os.makedirs(output_dir, exist_ok=True)

video_items = temp_timeline.GetItemListInTrack("video", 1)
print(f"Timeline has {len(video_items)} clips. Exporting...")

# 取得時間軸起始幀數（Resolve 預設可能是 86400 幀，即 01:00:00:00）
timeline_start_frame = temp_timeline.GetStartFrame()
current_track_offset = timeline_start_frame

for idx, item in enumerate(video_items):
    clip_name = item.GetName()
    duration = item.GetEnd() - item.GetStart()
    
    # 移到片段的正中央影格
    middle_frame_on_timeline = current_track_offset + (duration // 2)
    tc_str = frames_to_timecode(middle_frame_on_timeline, fps)
    
    # 移動播放頭
    temp_timeline.SetCurrentTimecode(tc_str)
    
    # 擷取縮圖
    thumb_data = temp_timeline.GetCurrentClipThumbnailImage()
    
    if thumb_data and "data" in thumb_data:
        try:
            # Resolve 回傳的是 Base64 編碼的 JPEG 資料
            img_bytes = base64.b64decode(thumb_data["data"])
            safe_name = "".join([c for c in clip_name if c.isalnum() or c in (".", "_", "-")]).rstrip()
            out_path = os.path.join(output_dir, f"{safe_name}.jpg")
            
            with open(out_path, "wb") as img_file:
                img_file.write(img_bytes)
            print(f"  [EXPORTED] {clip_name} -> {out_path}")
        except Exception as e:
            print(f"  [FAILED] {clip_name} — {e}")
    else:
        print(f"  [FAILED] {clip_name} — No thumbnail data returned.")
        
    current_track_offset += duration

print("\n[Done] All thumbnails exported successfully!")
