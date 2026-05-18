import sys
import time

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

timeline_count = current_project.GetTimelineCount()
target_timeline = None
for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    if "南區工作" in tl.GetName():
        target_timeline = tl
        break

# 強制切換 GUI 焦點至南區工作
current_project.SetCurrentTimeline(target_timeline)
resolve.OpenPage("media")
time.sleep(0.3)
resolve.OpenPage("edit")
time.sleep(0.3)

root_folder = media_pool.GetRootFolder()
def find_folder_recursive(current_folder, path_parts):
    if not path_parts: return current_folder
    target = path_parts[0]
    for sub in current_folder.GetSubFolderList():
        if sub.GetName().lower() == target.lower():
            return find_folder_recursive(sub, path_parts[1:])
    return None

clip_folder = find_folder_recursive(root_folder, ["Video", "D2", "CLIP"])
media_pool.SetCurrentFolder(clip_folder)
test_clips = clip_folder.GetClipList()[:5]

# 清理舊視訊
try:
    v_items = target_timeline.GetItemListInTrack("video", 1)
    if v_items: target_timeline.DeleteClips(v_items)
except Exception:
    pass

# 使用與第一次成功一模一樣的簡化格式 (無 recordFrame)
clips_to_append = []
for clip in test_clips:
    clips_to_append.append({
        "mediaPoolItem": clip,
        "startFrame": 24, # 從第一秒開始
        "endFrame": 48    # 剪輯 1 秒鐘
    })

appended = media_pool.AppendToTimeline(clips_to_append)
print(f"Appended list: {appended}")
if appended and appended[0] is not None:
    print(f"🎉 SUCCESS! Appended {len(appended)} clips sequentially to '{target_timeline.GetName()}'!")
else:
    print("❌ Sequential append failed.")
