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
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()

def find_clip(folder, name):
    for c in folder.GetClipList():
        if name in c.GetName():
            return c
    for sub in folder.GetSubFolderList() or []:
        res = find_clip(sub, name)
        if res:
            return res
    return None

sub_clip = find_clip(root_folder, "Subtitle 1")
if sub_clip:
    print(f"Found clip: {sub_clip.GetName()}")
    for prop in ["Clip Name", "File Name", "File Path", "Format", "Duration", "Description", "Comments", "Notes"]:
        val = sub_clip.GetClipProperty(prop)
        if val:
            print(f"  {prop}: {val}")
else:
    print("❌ Subtitle 1 clip not found")
