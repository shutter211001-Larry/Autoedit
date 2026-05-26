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
if not project:
    print("❌ No current project.")
    sys.exit(1)

media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()

print(f"Project name: {project.GetName()}")

def list_all_clips(folder, depth=0):
    indent = "  " * depth
    print(f"{indent}📁 Folder: {folder.GetName()}")
    for clip in folder.GetClipList():
        print(f"{indent}  🎥 Clip: {clip.GetName()}")
    for sub in folder.GetSubFolderList() or []:
        list_all_clips(sub, depth + 1)

list_all_clips(root_folder)
