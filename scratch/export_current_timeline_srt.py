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

if not timeline:
    print("❌ No active timeline found!")
    sys.exit(1)

print(f"Active Timeline Name: {timeline.GetName()}")

fps = float(project.GetSetting("timelineFrameRate") or 60.0)
print(f"Timeline FPS: {fps}")

timeline_start = timeline.GetStartFrame()
print(f"Timeline Start Frame: {timeline_start}")

subtitle_track_count = timeline.GetTrackCount("subtitle")
print(f"Subtitle Track Count: {subtitle_track_count}")

if subtitle_track_count == 0:
    print("⚠️ No subtitle tracks found in the active timeline!")
    sys.exit(0)

# We read the first subtitle track
subtitle_items = timeline.GetItemListInTrack("subtitle", 1)
if not subtitle_items:
    print("⚠️ Subtitle track 1 is empty!")
    sys.exit(0)

print(f"Found {len(subtitle_items)} subtitle items on track 1.")

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

srt_lines = []
for idx, item in enumerate(subtitle_items):
    start_frame = item.GetStart()
    end_frame = item.GetEnd()
    
    # Resolve timeline coordinates are absolute (e.g. starting at 86400).
    # We convert them to relative seconds from timeline start.
    start_sec = (start_frame - timeline_start) / fps
    end_sec = (end_frame - timeline_start) / fps
    
    start_tc = format_srt_time(start_sec)
    end_tc = format_srt_time(end_sec)
    
    text = item.GetName()
    srt_lines.append(f"{idx+1}\n{start_tc} --> {end_tc}\n<b>{text}</b>\n\n")

output_path = r"c:\TEST\scratch\Mars_Marketing_Exported.srt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("".join(srt_lines))

print(f"🎉 Successfully exported timeline subtitles to {output_path}!")
print("First 15 lines of exported SRT:")
print("".join(srt_lines[:5]))
