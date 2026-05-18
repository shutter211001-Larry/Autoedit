import sys
import os

# ── Resolve 21 初始化 ────────────────────────────────────────
RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
except ImportError as e:
    print(f"Error: Cannot load DaVinciResolveScript: {e}")
    sys.exit(1)

if not resolve:
    print("Error: Resolve not running.")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
current_project = project_manager.GetCurrentProject()
media_pool = current_project.GetMediaPool()
root_folder = media_pool.GetRootFolder()

# 導航至 CLIP 資料夾
def find_folder_recursive(current_folder, path_parts):
    if not path_parts:
        return current_folder
    target = path_parts[0]
    sub_folders = current_folder.GetSubFolderList()
    for sub in sub_folders:
        if sub.GetName().lower() == target.lower():
            return find_folder_recursive(sub, path_parts[1:])
    return None

clip_folder = find_folder_recursive(root_folder, ["Video", "D2", "CLIP"])
if not clip_folder:
    print("Error: Cannot find CLIP folder.")
    sys.exit(1)

clips = clip_folder.GetClipList()

print("🧹 Resetting all Clip Flags to None...")
for clip in clips:
    clip.ClearFlags("All")

print("🎉 Success! All flags cleared. You can now manually flag your actual Good Takes (Green Flags) in Resolve!")
