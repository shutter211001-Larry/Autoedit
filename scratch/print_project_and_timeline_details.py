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
print(f"Current Project Name: {project.GetName()}")

timeline = project.GetCurrentTimeline()
print(f"Current Active Timeline: {timeline.GetName() if timeline else 'None'}")

timeline_count = project.GetTimelineCount()
print(f"Total Timelines: {timeline_count}")
for i in range(1, timeline_count + 1):
    tl = project.GetTimelineByIndex(i)
    if tl:
        print(f"  Timeline #{i}: '{tl.GetName()}'")
        for track_type in ["video", "audio", "subtitle"]:
            tc = tl.GetTrackCount(track_type)
            if tc > 0:
                print(f"    - {track_type} tracks: {tc}")
                for t_idx in range(1, tc + 1):
                    items = tl.GetItemListInTrack(track_type, t_idx)
                    print(f"      * Track #{t_idx} has {len(items) if items else 0} items.")
                    if items and track_type == "subtitle":
                        for item_idx, item in enumerate(items[:3]):
                            print(f"        [Sub #{item_idx+1}] start={item.GetStart()} end={item.GetEnd()} text='{item.GetName()}'")
