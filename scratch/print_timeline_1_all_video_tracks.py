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

# Find 'Timeline 1'
timeline = None
for i in range(1, project.GetTimelineCount() + 1):
    t = project.GetTimelineByIndex(i)
    if t and t.GetName() == "Timeline 1":
        timeline = t
        break

if not timeline:
    print("❌ Timeline 1 not found!")
    sys.exit(1)

print(f"Timeline Name: {timeline.GetName()}")
v_tracks = timeline.GetTrackCount("video")
print(f"Total Video Tracks: {v_tracks}")

for t_idx in range(1, v_tracks + 1):
    items = timeline.GetItemListInTrack("video", t_idx)
    print(f"\n🎬 Track #{t_idx} | Total Items: {len(items) if items else 0}")
    if items:
        for idx, item in enumerate(items):
            media_pool_item = item.GetMediaPoolItem()
            clip_name = media_pool_item.GetName() if media_pool_item else "NoMediaPoolItem"
            if "C055" in clip_name:
                print(f"  🎯 FOUND C055! Index: {idx+1} | Item Name: {item.GetName()} | Start: {item.GetStart()} | End: {item.GetEnd()} | Source Start Frame: {item.GetSourceStartFrame()}")
