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

timeline_count = project.GetTimelineCount()
print(f"Total Timelines in Project: {timeline_count}")

for i in range(1, timeline_count + 1):
    tl = project.GetTimelineByIndex(i)
    if not tl:
        continue
    tl_name = tl.GetName()
    v_tracks = tl.GetTrackCount("video")
    a_tracks = tl.GetTrackCount("audio")
    sub_tracks = tl.GetTrackCount("subtitle")
    
    sub_items_count = 0
    if sub_tracks > 0:
        sub_items = tl.GetItemListInTrack("subtitle", 1)
        sub_items_count = len(sub_items) if sub_items else 0
        
    print(f"Timeline #{i}: '{tl_name}' | Video Tracks: {v_tracks} | Audio Tracks: {a_tracks} | Subtitle Tracks: {sub_tracks} | Subtitle Items in Track 1: {sub_items_count}")
