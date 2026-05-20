import sys
import os
from datetime import datetime

# Resolve 21 官方模組路徑
RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"

if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
except ImportError as e:
    print(f"Error: Cannot load DaVinciResolveScript — {e}")
    sys.exit(1)

if not resolve:
    print("Error: Failed to connect to Resolve. Ensure Resolve is running and External Scripting is set to 'Local'.")
    print("  → Resolve 偏好設定 > 系統 > 一般 > 外部腳本使用 > 設為 Local")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
if not project_manager:
    print("Error: Failed to get ProjectManager.")
    sys.exit(1)

# 專案名稱 — 可手動修改此變數
project_name = f"New_Project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# 確認同名專案不存在
existing_projects = project_manager.GetProjectListInCurrentFolder()
if existing_projects and project_name in existing_projects:
    print(f"Error: Project '{project_name}' already exists. Aborting to prevent overwrite.")
    sys.exit(1)

# 建立新專案
new_project = project_manager.CreateProject(project_name)
if not new_project:
    print(f"Error: Failed to create project '{project_name}'. Resolve may have rejected the name.")
    sys.exit(1)

print(f"Success: Project '{project_name}' created and opened.")
