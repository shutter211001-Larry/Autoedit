import sys
import os
import time

# Add root folder to sys.path to allow imports from core package
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.resolve_api import connect_to_resolve

def diagnose_timeline(timeline_name=None):
    """
    Connects to DaVinci Resolve, locates the requested timeline (or the active one),
    and outputs a detailed diagnosis of both Video and Audio Tracks.
    """
    resolve = connect_to_resolve()
    if not resolve:
        print("❌ Failed to connect to DaVinci Resolve! Please ensure Resolve is running and External Scripting is enabled.")
        return False

    project_manager = resolve.GetProjectManager()
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        print("❌ No active project found in Resolve! Please open a project first.")
        return False

    # Find the target timeline
    target_timeline = None
    if timeline_name:
        timeline_count = current_project.GetTimelineCount()
        for i in range(1, timeline_count + 1):
            tl = current_project.GetTimelineByIndex(i)
            if tl and tl.GetName() == timeline_name:
                target_timeline = tl
                break
        if not target_timeline:
            print(f"⚠️ Timeline '{timeline_name}' not found. Falling back to active timeline.")
    
    if not target_timeline:
        target_timeline = current_project.GetCurrentTimeline()

    if not target_timeline:
        print("❌ No timeline is currently active in DaVinci Resolve!")
        return False

    print("========================================")
    print(f"🎬 Timeline Name: '{target_timeline.GetName()}'")
    print(f"⏱️ Start Frame: {target_timeline.GetStartFrame()}")
    print(f"⏱️ End Frame: {target_timeline.GetEndFrame()}")
    print("========================================")

    # Video Tracks
    v_track_count = target_timeline.GetTrackCount("video")
    print(f"Total Video Tracks: {v_track_count}")
    for vt in range(1, v_track_count + 1):
        items = target_timeline.GetItemListInTrack("video", vt) or []
        print(f"\n🎥 Video Track {vt} (contains {len(items)} clips):")
        for idx, item in enumerate(items, 1):
            name = item.GetName()
            start = item.GetStart()
            end = item.GetEnd()
            duration = item.GetDuration()
            color = item.GetClipColor()
            try:
                zoom_x = item.GetProperty("ZoomX")
                zoom_y = item.GetProperty("ZoomY")
                rot = item.GetProperty("RotationAngle")
                pan = item.GetProperty("Pan")
                tilt = item.GetProperty("Tilt")
            except Exception:
                zoom_x, zoom_y, rot, pan, tilt = "N/A", "N/A", "N/A", "N/A", "N/A"
            print(f"  [{idx}] Name: '{name}' | Start: {start} | End: {end} | Dur: {duration} | Color: {color}")
            print(f"      Zoom: ({zoom_x}, {zoom_y}) | Rot: {rot} | Pan: {pan} | Tilt: {tilt}")

    # Audio Tracks
    a_track_count = target_timeline.GetTrackCount("audio")
    print(f"\n========================================")
    print(f"Total Audio Tracks: {a_track_count}")
    for at in range(1, a_track_count + 1):
        items = target_timeline.GetItemListInTrack("audio", at) or []
        print(f"\n🎵 Audio Track {at} (contains {len(items)} clips):")
        for idx, item in enumerate(items, 1):
            name = item.GetName()
            start = item.GetStart()
            end = item.GetEnd()
            duration = item.GetDuration()
            print(f"  [{idx}] Name: '{name}' | Start: {start} | End: {end} | Dur: {duration}")

    print("\n========================================")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DaVinci Resolve Timeline Diagnostics Tool")
    parser.add_argument("--timeline", "-t", type=str, default=None, help="Name of the timeline to diagnose")
    args = parser.parse_args()
    
    diagnose_timeline(args.timeline)
