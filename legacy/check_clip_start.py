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
media_pool = current_project.GetMediaPool()

root_folder = media_pool.GetRootFolder()
def find_folder_recursive(current_folder, path_parts):
    if not path_parts: return current_folder
    target = path_parts[0]
    for sub in current_folder.GetSubFolderList():
        if sub.GetName().lower() == target.lower():
            return find_folder_recursive(sub, path_parts[1:])
    return None

clip_folder = find_folder_recursive(root_folder, ["Video", "D2", "CLIP"])
test_clip = clip_folder.GetClipList()[0]

print(f"Analyzing Clip: '{test_clip.GetName()}'")
# 印出所有可能與時間碼、起點影格相關的屬性
properties = ["Start", "End", "Start TC", "End TC", "Frames", "Duration"]
for prop in properties:
    val = test_clip.GetClipProperty(prop)
    print(f"  Clip Property '{prop}': {val} (Type: {type(val)})")
