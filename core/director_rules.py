# AI Film Director Engine - Cinematic Movement & Layout Rules

COLOR_MAP = {
    "setup": "Navy",
    "detail": "Yellow",
    "catwalk": "Orange",
    "finale": "Purple"
}

def get_aesthetic_grade(a_score):
    """
    Categorizes the aesthetic score into human-readable ratings.
    """
    if a_score >= 0.04:
        return "🌟 Premium"
    elif a_score >= 0.00:
        return "✨ Good"
    elif a_score >= -0.02:
        return "👌 Acceptable (Filtered by Aesthetic Gate)"
    else:
        return "⚠️ Bad-Filtered (Rescued)"

def get_transform_properties(idx, role, source_footage_vertical=True):
    """
    Determines cinematic movement variables (Zoom, Rotation) and timeline colors
    based on the clip's sequential position and narrative role.
    """
    zoom_val = 1.0
    rotation_val = 0.0
    
    # 基礎運鏡公式
    if role == "setup":
        zoom_val = 1.0
        rotation_val = 0.0
    elif role == "detail":
        zoom_val = 1.10
        rotation_val = 0.0
    elif role == "catwalk":
        zoom_val = 1.15
        # 交替斜切擺動，創造手持大秀躍動感
        rotation_val = 4.0 if (idx % 2 == 0) else -4.0
    elif role == "finale":
        zoom_val = 1.20
        rotation_val = 0.0
        
    # 套用直式像素補償 (橫式影片直時間軸需要 x3.16 倍填滿)
    VERTICAL_CROP_ZOOM = 1.0 if source_footage_vertical else 3.16
    zoom_val = zoom_val * VERTICAL_CROP_ZOOM
    
    color_name = COLOR_MAP.get(role, "Navy")
    
    return zoom_val, rotation_val, color_name
