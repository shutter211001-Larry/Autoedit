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

print(f"🎬 Active Project: '{current_project.GetName()}'")
timeline_count = current_project.GetTimelineCount()

for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    if not tl:
        continue
    name = tl.GetName()
    placed_clips = tl.GetItemListInTrack("video", 1) or []
    for idx, item in enumerate(placed_clips):
        color = item.GetClipColor().lower()
        if color in ["pink", "rose", "red"]:
            print(f"🌟 FOUND Pink/Rose/Red clip on Timeline '{name}' at index {idx+1} (Clip Name: '{item.GetName()}') | Color: '{color}'")
