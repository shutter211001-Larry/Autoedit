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
    print(f"🔍 Auditing {len(all_clips)} clips in Media Pool for 'audience' or '觀眾'...")
    
    count = 0
    for idx, clip in enumerate(all_clips):
        name = clip.GetName()
        desc = clip.GetClipProperty("Description").strip()
        comments = clip.GetClipProperty("Comments").strip()
        
        # 尋找包含觀眾、audience, view, crowd, people 等字詞
        is_audience = False
        text_to_check = (name + " " + desc + " " + comments).lower()
        
        # 繁體中文「觀眾」、「聽眾」、「台下」、「看秀」或英文相關
        if any(w in text_to_check for w in ["觀眾", "audience", "crowd", "people", "view"]):
            is_audience = True
            
        if is_audience:
            count += 1
            print(f"   [{count}] Name: '{name}' | Desc: '{desc}' | Comments: '{comments}'")
            
    print(f"🎬 Total audience-related clips found: {count}")
else:
    print("❌ Master/Video/D2/CLIP folder not found")
