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
    print("❌ DaVinci Resolve is not running. Please open your project first.")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
current_project = project_manager.GetCurrentProject()

if not current_project:
    print("❌ No active project found in Resolve.")
    sys.exit(1)

timeline = current_project.GetCurrentTimeline()
if not timeline:
    print("❌ No active timeline found.")
    sys.exit(1)

placed_clips = timeline.GetItemListInTrack("video", 1) or []
if len(placed_clips) < 2:
    print("⚠️ Need at least 2 clips on Video Track 1 to test copy grades.")
    sys.exit(0)

source_clip = placed_clips[0]
target_clips = placed_clips[1:]

print(f"👑 Testing CopyGrades from master clip '{source_clip.GetName()}' to {len(target_clips)} clips...")
try:
    success = source_clip.CopyGrades(target_clips)
    if success:
        print("🎉 SUCCESS: Color grades copied successfully to all target clips!")
    else:
        print("❌ Error: Resolve returned failure when copying grades.")
except Exception as e:
    print(f"❌ Exception occurred during CopyGrades: {e}")
