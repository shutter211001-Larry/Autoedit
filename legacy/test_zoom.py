import sys

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
timeline = current_project.GetCurrentTimeline()

video_items = timeline.GetItemListInTrack("video", 1)
if not video_items:
    print("No video items on track 1")
    sys.exit(0)

item = video_items[0]
print(f"Clip Name: {item.GetName()}")
print("Setting ZoomX and ZoomY to 3.16...")
s1 = item.SetProperty("ZoomX", 3.16)
s2 = item.SetProperty("ZoomY", 3.16)
print(f"  Set ZoomX success: {s1}")
print(f"  Set ZoomY success: {s2}")

print(f"Reading back ZoomX: {item.GetProperty('ZoomX')}")
print(f"Reading back ZoomY: {item.GetProperty('ZoomY')}")
