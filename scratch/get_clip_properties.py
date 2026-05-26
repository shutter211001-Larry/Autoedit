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

target_names = [
    "A001_03271229_C055.mov",
    "A001_03271229_C056.mov",
    "A001_03271230_C057.mov",
    "A001_03271231_C058.mov",
    "A001_03271242_C059.mov"
]

def print_properties(folder):
    for clip in folder.GetClipList():
        name = clip.GetName()
        if name in target_names or any(t in name for t in ["C055", "C056", "C057", "C058", "C059"]):
            print(f"🎥 Clip: {name}")
            # Try to get various properties
            for prop in ["Description", "Comments", "Clip Color", "Good Take", "Camera", "Angle", "Notes", "Duration", "Start TC", "End TC"]:
                val = clip.GetClipProperty(prop)
                if val:
                    print(f"  - {prop}: {val}")
            
            # Let's also check markers
            markers = clip.GetMarkers()
            if markers:
                print(f"  - Markers: {markers}")
    for sub in folder.GetSubFolderList() or []:
        print_properties(sub)

print_properties(root_folder)
