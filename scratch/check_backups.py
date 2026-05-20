import sys
import os

RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript as dvr_script  # type: ignore
    resolve = dvr_script.scriptapp("Resolve")
except ImportError as e:
    print(f"❌ Cannot load DaVinciResolveScript SDK: {e}")
    sys.exit(1)

if not resolve:
    print("❌ DaVinci Resolve is not running.")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
current_project = project_manager.GetCurrentProject()

if not current_project:
    print("❌ No active project found.")
    sys.exit(1)

print(f"🎬 Active Project: '{current_project.GetName()}'")
timeline_count = current_project.GetTimelineCount()
print(f"⏱️ Total Timelines Found: {timeline_count}")
print("="*60)

for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    if not tl:
        continue
    name = tl.GetName()
    video_clips = tl.GetItemListInTrack("video", 1) or []
    audio_clips_t1 = tl.GetItemListInTrack("audio", 1) or []
    audio_clips_t2 = tl.GetItemListInTrack("audio", 2) or []
    print(f"🎥 Timeline: '{name}'")
    print(f"   • Video Track 1: {len(video_clips)} clips")
    print(f"   • Audio Track 1: {len(audio_clips_t1)} clips")
    print(f"   • Audio Track 2: {len(audio_clips_t2)} clips")
    print("-"*60)
