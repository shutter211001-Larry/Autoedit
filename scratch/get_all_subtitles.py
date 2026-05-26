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

subtitle_items = timeline.GetItemListInTrack("subtitle", 1)
print(f"Total Subtitle Items: {len(subtitle_items)}")

with open(r"c:\TEST\scratch\all_subtitles.txt", "w", encoding="utf-8") as f:
    for idx, item in enumerate(subtitle_items):
        start = item.GetStart()
        end = item.GetEnd()
        duration = item.GetDuration()
        text = item.GetName()
        f.write(f"Subtitle #{idx+1} | Start: {start} | End: {end} | Duration: {duration} | Text: {text}\n")

print("✅ Dumped all subtitles to c:\\TEST\\scratch\\all_subtitles.txt")
