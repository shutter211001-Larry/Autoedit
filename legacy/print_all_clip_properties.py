import sys
import os

RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

import DaVinciResolveScript as dvr_script
resolve = dvr_script.scriptapp("Resolve")

project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_pool = project.GetMediaPool()

def find_folder_recursive(current_folder, path_parts):
    if not path_parts: return current_folder
    target = path_parts[0]
    for sub in current_folder.GetSubFolderList():
        if sub.GetName().lower() == target.lower():
            return find_folder_recursive(sub, path_parts[1:])
    return None

root_folder = media_pool.GetRootFolder()
clip_folder = find_folder_recursive(root_folder, ["Video", "D2", "CLIP"])

if clip_folder:
    all_clips = clip_folder.GetClipList()
    
    with open("clip_properties_dump.txt", "w", encoding="utf-8") as f:
        f.write(f"Total Clips in CLIP folder: {len(all_clips)}\n")
        f.write("="*80 + "\n")
        for idx, clip in enumerate(all_clips):
            name = clip.GetName()
            desc = clip.GetClipProperty("Description").strip()
            comments = clip.GetClipProperty("Comments").strip()
            f.write(f"Clip #{idx+1} | Name: {name} | Desc: {desc} | Comments: {comments}\n")
            
    print("✅ Dumped all clip properties to clip_properties_dump.txt successfully!")
else:
    print("❌ CLIP folder not found")
