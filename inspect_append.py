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

# 切換至南區工作
timeline_count = current_project.GetTimelineCount()
target_timeline = None
for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    if "南區工作" in tl.GetName():
        target_timeline = tl
        break

current_project.SetCurrentTimeline(target_timeline)
resolve.OpenPage("media")
time.sleep(0.3)
resolve.OpenPage("edit")
time.sleep(0.3)

# 測試 append 一個 clip，並列印其詳細回傳值與屬性
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

test_clip = clip_folder.GetClipList()[0]
print(f"Test clip to append: '{test_clip.GetName()}'")

# 嘗試 append
clip_info = {
    "mediaPoolItem": test_clip,
    "startFrame": 0,
    "endFrame": 48,
    "trackIndex": 1,
    "recordFrame": 86400
}

appended = media_pool.AppendToTimeline([clip_info])
print(f"Appended return value type: {type(appended)}")
print(f"Appended return value: {appended}")

if appended:
    for idx, item in enumerate(appended):
        print(f"  Item [{idx}]:")
        print(f"    Name: {item.GetName()}")
        print(f"    Start Frame on Timeline: {item.GetStart()}")
        print(f"    End Frame on Timeline: {item.GetEnd()}")
        
# 檢查當前時間軸
current_tl = current_project.GetCurrentTimeline()
print(f"Current active timeline name: '{current_tl.GetName()}'")
items = current_tl.GetItemListInTrack("video", 1)
print(f"Clips on Track 1 of '{current_tl.GetName()}': {[x.GetName() for x in items] if items else 'Empty'}")
