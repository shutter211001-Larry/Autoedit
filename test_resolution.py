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

print("Current Settings:")
w = current_project.GetSetting("timelineResolutionWidth")
h = current_project.GetSetting("timelineResolutionHeight")
print(f"  Width: {w}")
print(f"  Height: {h}")

print("Setting to 1080x1920...")
success1 = current_project.SetSetting("timelineResolutionWidth", "1080")
success2 = current_project.SetSetting("timelineResolutionHeight", "1920")
print(f"  Width success: {success1}")
print(f"  Height success: {success2}")

print("New Settings:")
w = current_project.GetSetting("timelineResolutionWidth")
h = current_project.GetSetting("timelineResolutionHeight")
print(f"  Width: {w}")
print(f"  Height: {h}")
