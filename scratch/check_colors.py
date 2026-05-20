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
    print("❌ No active project.")
    sys.exit(1)

timeline = current_project.GetCurrentTimeline()
if not timeline:
    print("❌ No active timeline.")
    sys.exit(1)

print(f"🎬 Current Active Project: '{current_project.GetName()}'")
print(f"⏱️ Current Active Timeline: '{timeline.GetName()}'")

placed_clips = timeline.GetItemListInTrack("video", 1) or []
print(f"Total clips on Video Track 1: {len(placed_clips)}")
for idx, item in enumerate(placed_clips):
    color = item.GetClipColor()
    name = item.GetName()
    print(f"  [{idx+1}] Name: '{name}' | Color: '{color}'")
