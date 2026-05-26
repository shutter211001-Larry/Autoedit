import sys
import os

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
    print("❌ Resolve not running.")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
timeline = project.GetCurrentTimeline()

print(f"Active Timeline: {timeline.GetName()}")
video_items = timeline.GetItemListInTrack("video", 1)
print(f"Total Video Items: {len(video_items) if video_items else 0}")
if video_items:
    for idx, item in enumerate(video_items):
        media_pool_item = item.GetMediaPoolItem()
        clip_name = media_pool_item.GetName() if media_pool_item else "NoMediaPoolItem"
        print(f"Clip #{idx+1}: Name = {item.GetName()} (MediaPoolItem = {clip_name}), Start = {item.GetStart()}, End = {item.GetEnd()}, Duration = {item.GetEnd() - item.GetStart()}")
