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
timeline = project.GetTimelineByIndex(1) # Timeline 1

print(f"Timeline Name: {timeline.GetName()}")

for track_type in ["video", "audio", "subtitle"]:
    tc = timeline.GetTrackCount(track_type)
    print(f"Track Type: {track_type}, Count: {tc}")
    for idx in range(1, tc + 1):
        items = timeline.GetItemListInTrack(track_type, idx)
        print(f"  Track #{idx} has {len(items) if items else 0} items.")
        if items:
            for item_idx, item in enumerate(items[:5]): # Print first 5 items
                media_pool_item = item.GetMediaPoolItem()
                item_name = media_pool_item.GetName() if media_pool_item else "NoMediaPoolItem"
                print(f"    - [{item_idx+1}] Item Name: {item.GetName()} (MediaPoolItem: {item_name})")
                # Check properties or text if subtitle
                if track_type == "subtitle":
                    pass
