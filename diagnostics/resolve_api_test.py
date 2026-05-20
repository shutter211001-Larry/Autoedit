import sys
import os
from datetime import datetime

# ── Resolve 21 初始化 ────────────────────────────────────────
RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
except ImportError as e:
    print(f"[FATAL] Cannot load DaVinciResolveScript: {e}")
    sys.exit(1)

if not resolve:
    print("[FATAL] Resolve not running or External Scripting not set to Local.")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
if not project_manager:
    print("[FATAL] Cannot get ProjectManager.")
    sys.exit(1)

# ── 工具函式 ─────────────────────────────────────────────────
def ok(label, value=""):
    print(f"  [PASS] {label}" + (f": {value}" if value != "" else ""))

def fail(label, reason=""):
    print(f"  [FAIL] {label}" + (f" — {reason}" if reason else ""))

def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

# ════════════════════════════════════════════════════════════
# TEST 1：Resolve 基本資訊
# ════════════════════════════════════════════════════════════
section("TEST 1 | Resolve 基本資訊")

try:
    version = resolve.GetVersionString()
    ok("GetVersionString", version)
except Exception as e:
    fail("GetVersionString", e)

try:
    page = resolve.GetCurrentPage()
    ok("GetCurrentPage", page)
except Exception as e:
    fail("GetCurrentPage", e)

# ════════════════════════════════════════════════════════════
# TEST 2：ProjectManager — 專案列表
# ════════════════════════════════════════════════════════════
section("TEST 2 | ProjectManager — 專案列表")

try:
    projects = project_manager.GetProjectListInCurrentFolder()
    ok("GetProjectListInCurrentFolder", f"{len(projects)} 個專案")
    for p in projects[:5]:
        print(f"         • {p}")
    if len(projects) > 5:
        print(f"         ... 共 {len(projects)} 個")
except Exception as e:
    fail("GetProjectListInCurrentFolder", e)

try:
    db_info = project_manager.GetCurrentDatabase()
    ok("GetCurrentDatabase", db_info)
except Exception as e:
    fail("GetCurrentDatabase", e)

# ════════════════════════════════════════════════════════════
# TEST 3：當前專案資訊
# ════════════════════════════════════════════════════════════
section("TEST 3 | 當前專案資訊")

current_project = project_manager.GetCurrentProject()
if not current_project:
    fail("GetCurrentProject", "No project open")
else:
    ok("GetCurrentProject")

    try:
        name = current_project.GetName()
        ok("GetName", name)
    except Exception as e:
        fail("GetName", e)

    try:
        settings = current_project.GetSetting()
        fps        = settings.get("timelineFrameRate", "N/A")
        width      = settings.get("timelineResolutionWidth", "N/A")
        height     = settings.get("timelineResolutionHeight", "N/A")
        ok("GetSetting — FPS", fps)
        ok("GetSetting — 解析度", f"{width}x{height}")
    except Exception as e:
        fail("GetSetting", e)

    try:
        presets = current_project.GetRenderPresetList()
        ok("GetRenderPresetList", f"{len(presets)} 個預設")
        for p in presets[:5]:
            print(f"         • {p}")
        if len(presets) > 5:
            print(f"         ... 共 {len(presets)} 個")
    except Exception as e:
        fail("GetRenderPresetList", e)

# ════════════════════════════════════════════════════════════
# TEST 4：MediaPool
# ════════════════════════════════════════════════════════════
section("TEST 4 | MediaPool")

if current_project:
    try:
        media_pool = current_project.GetMediaPool()
        ok("GetMediaPool")
    except Exception as e:
        fail("GetMediaPool", e)
        media_pool = None

    if media_pool:
        try:
            root = media_pool.GetRootFolder()
            ok("GetRootFolder", root.GetName())
        except Exception as e:
            fail("GetRootFolder", e)

        try:
            clips = media_pool.GetRootFolder().GetClipList()
            ok("GetClipList (root)", f"{len(clips)} 個 clip")
        except Exception as e:
            fail("GetClipList", e)

# ════════════════════════════════════════════════════════════
# TEST 5：Timeline
# ════════════════════════════════════════════════════════════
section("TEST 5 | Timeline")

if current_project:
    try:
        tl_count = current_project.GetTimelineCount()
        ok("GetTimelineCount", f"{tl_count} 條時間軸")
    except Exception as e:
        fail("GetTimelineCount", e)
        tl_count = 0

    try:
        current_tl = current_project.GetCurrentTimeline()
        if current_tl:
            ok("GetCurrentTimeline", current_tl.GetName())
            try:
                duration = current_tl.GetEndFrame() - current_tl.GetStartFrame()
                ok("Timeline Duration (frames)", duration)
            except Exception as e:
                fail("GetEndFrame/GetStartFrame", e)
        else:
            ok("GetCurrentTimeline", "（無時間軸）")
    except Exception as e:
        fail("GetCurrentTimeline", e)

# ════════════════════════════════════════════════════════════
# TEST 6：建立空白時間軸（功能性測試）
# ════════════════════════════════════════════════════════════
section("TEST 6 | 建立空白時間軸")

if current_project and media_pool:
    test_tl_name = f"Test_Timeline_{datetime.now().strftime('%H%M%S')}"
    try:
        new_tl = media_pool.CreateEmptyTimeline(test_tl_name)
        if new_tl:
            ok("CreateEmptyTimeline", new_tl.GetName())
        else:
            fail("CreateEmptyTimeline", "返回 None")
    except Exception as e:
        fail("CreateEmptyTimeline", e)

# ════════════════════════════════════════════════════════════
# 總結
# ════════════════════════════════════════════════════════════
section("測試完成")
print(f"  時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  環境：DaVinci Resolve Studio 21 / Windows")
print()
