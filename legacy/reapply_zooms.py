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

placed_clips = timeline.GetItemListInTrack("video", 1)
print(f"Found {len(placed_clips)} clips on video track 1.")

# We will recreate the roles and zooms exactly as run_ai2_edit.py did:
# setup: 3 clips
# detail: 8 clips
# catwalk: 14 clips
# finale: 4 clips
# total: 29 clips

roles = (
    ["setup"] * 3 +
    ["detail"] * 8 +
    ["catwalk"] * 14 +
    ["finale"] * 4
)

SOURCE_FOOTAGE_VERTICAL = True
VERTICAL_CROP_ZOOM = 1.0 if SOURCE_FOOTAGE_VERTICAL else 3.16

for idx, item in enumerate(placed_clips):
    role = roles[idx] if idx < len(roles) else "finale"
    zoom_val = 1.0
    rotation_val = 0.0
    if role == "setup":
        zoom_val = 1.0
        rotation_val = 0.0
    elif role == "detail":
        zoom_val = 1.10
        rotation_val = 0.0
    elif role == "catwalk":
        zoom_val = 1.15
        rotation_val = 4.0 if (idx % 2 == 0) else -4.0
    elif role == "finale":
        zoom_val = 1.20
        rotation_val = 0.0
        
    zoom_val = zoom_val * VERTICAL_CROP_ZOOM
    
    s1 = item.SetProperty("ZoomX", zoom_val)
    s2 = item.SetProperty("ZoomY", zoom_val)
    s3 = item.SetProperty("RotationAngle", rotation_val)
    
    print(f"Clip #{idx+1} ({item.GetName()} - {role.upper()}):")
    print(f"  Zoom target: {zoom_val:.3f} | Success: ({s1}, {s2})")
    print(f"  Rotation target: {rotation_val} | Success: {s3}")
