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

# Find C055
def find_clip(folder, name):
    for c in folder.GetClipList():
        if name in c.GetName():
            return c
    for sub in folder.GetSubFolderList() or []:
        res = find_clip(sub, name)
        if res:
            return res
    return None

c055 = find_clip(root_folder, "C055")
if c055:
    print(f"Found clip: {c055.GetName()}")
    # Let's try to get all known Resolve clip properties
    properties = [
        "Clip Name", "File Name", "File Path", "Format", "Video Codec", "Audio Codec",
        "Start TC", "End TC", "Duration", "Frames", "FPS", "Resolution",
        "Camera", "Angle", "Reel No", "Scene", "Take", "Good Take",
        "Description", "Comments", "Notes", "Slate Ref", "Artist", "Album",
        "Composer", "Key", "Tempo", "Genre", "Year", "Track", "Lyrics",
        "Clip Color", "Usage", "Creation Date", "Modified Date"
    ]
    for prop in properties:
        val = c055.GetClipProperty(prop)
        if val:
            print(f"  {prop}: {val}")
    
    # Check markers
    markers = c055.GetMarkers()
    if markers:
        print(f"  Markers: {markers}")
else:
    print("❌ Clip C055 not found")
