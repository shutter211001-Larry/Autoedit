import sys

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

timeline_count = current_project.GetTimelineCount()
for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    print(f"\nTimeline '{tl.GetName()}':")
    # Video Tracks
    v_track_count = tl.GetTrackCount("video")
    print(f"  Video tracks: {v_track_count}")
    for vt in range(1, v_track_count + 1):
        items = tl.GetItemListInTrack("video", vt)
        print(f"    Track {vt} clips count: {len(items) if items else 0}")
        if items:
            print(f"      First clip: {items[0].GetName()}")
            print(f"      Last clip: {items[-1].GetName()}")
            
    # Audio Tracks
    a_track_count = tl.GetTrackCount("audio")
    print(f"  Audio tracks: {a_track_count}")
    for at in range(1, a_track_count + 1):
        items = tl.GetItemListInTrack("audio", at)
        print(f"    Track {at} clips count: {len(items) if items else 0}")
