"""
DaVinci Resolve 21 API 自動探索腳本
執行後將列出所有主要物件的可用方法，輸出至 resolve_api_map.txt
"""
import sys
import os
from datetime import datetime

RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
except ImportError as e:
    print(f"[FATAL] {e}"); sys.exit(1)

if not resolve:
    print("[FATAL] Resolve not running."); sys.exit(1)

project_manager = resolve.GetProjectManager()
current_project  = project_manager.GetCurrentProject()
media_pool       = current_project.GetMediaPool() if current_project else None
root_folder      = media_pool.GetRootFolder()     if media_pool else None
current_timeline = current_project.GetCurrentTimeline() if current_project else None

# ── 建立物件表 ───────────────────────────────────────────────
objects = {
    "resolve":          resolve,
    "project_manager":  project_manager,
    "current_project":  current_project,
    "media_pool":       media_pool,
    "root_folder":      root_folder,
    "current_timeline": current_timeline,
}

# ── 探索函式 ─────────────────────────────────────────────────
def get_api_methods(obj):
    if obj is None:
        return ["[N/A] 物件為 None"]
    return sorted([m for m in dir(obj)
                   if not m.startswith("_") and callable(getattr(obj, m, None))])

# ── 輸出 ─────────────────────────────────────────────────────
lines = []
lines.append(f"DaVinci Resolve 21 API 方法探索報告")
lines.append(f"產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append("=" * 60)

for obj_name, obj in objects.items():
    methods = get_api_methods(obj)
    lines.append(f"\n## {obj_name}  ({len(methods)} 個方法)")
    lines.append("-" * 40)
    for m in methods:
        lines.append(f"  {m}")

# 嘗試取得 TimelineItem 方法（需要時間軸有 clip）
if current_timeline:
    try:
        items = current_timeline.GetItemListInTrack("video", 1)
        if items:
            tl_item_methods = get_api_methods(items[0])
            lines.append(f"\n## timeline_item  ({len(tl_item_methods)} 個方法)")
            lines.append("-" * 40)
            for m in tl_item_methods:
                lines.append(f"  {m}")
    except Exception:
        pass

output_path = r"C:\TEST\resolve_api_map.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("\n".join(lines))
print(f"\n[Done] 已輸出至 {output_path}")
