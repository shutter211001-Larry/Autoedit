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
if len(video_items) < 2:
    print("Not enough video items")
    sys.exit(0)

c1 = video_items[0]
c2 = video_items[1]

print("Initial:")
print(f"  Clip 1 ZoomX: {c1.GetProperty('ZoomX')}")
print(f"  Clip 2 ZoomX: {c2.GetProperty('ZoomX')}")

print("Setting Clip 1 ZoomX = 3.16, Clip 2 ZoomX = 3.476...")
c1.SetProperty("ZoomX", 3.16)
c2.SetProperty("ZoomX", 3.476)

print("After Setting:")
print(f"  Clip 1 ZoomX: {c1.GetProperty('ZoomX')}")
print(f"  Clip 2 ZoomX: {c2.GetProperty('ZoomX')}")

print("Copying grades from Clip 1 to Clip 2...")
success = c1.CopyGrades([c2])
print(f"  CopyGrades success: {success}")

print("After CopyGrades:")
print(f"  Clip 1 ZoomX: {c1.GetProperty('ZoomX')}")
print(f"  Clip 2 ZoomX: {c2.GetProperty('ZoomX')}")
