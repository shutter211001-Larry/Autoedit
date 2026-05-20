import sys
import os

RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
current_project = project_manager.GetCurrentProject()

timeline_count = current_project.GetTimelineCount()
target_timeline = None
for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    if tl.GetName() == "AI_2":
        target_timeline = tl
        break

if not target_timeline:
    print("❌ Timeline AI_2 not found!")
    sys.exit(1)

print("========================================")
print(f"Timeline Name: '{target_timeline.GetName()}'")
print(f"Start Frame: {target_timeline.GetStartFrame()}")
print(f"End Frame: {target_timeline.GetEndFrame()}")
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
