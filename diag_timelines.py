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

print(f"Active Project: '{current_project.GetName()}'")
print(f"Current Timeline in GUI: '{current_project.GetCurrentTimeline().GetName()}'")

timeline_count = current_project.GetTimelineCount()
print(f"Total timelines in project: {timeline_count}")

for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    v_items = tl.GetItemListInTrack("video", 1)
    a_items = tl.GetItemListInTrack("audio", 1)
    print(f"  [{i}] Timeline Name: '{tl.GetName()}'")
    print(f"      Video items on Track 1: {len(v_items) if v_items else 0}")
    print(f"      Audio items on Track 1: {len(a_items) if a_items else 0}")
    print(f"      Start Frame: {tl.GetStartFrame()}")
