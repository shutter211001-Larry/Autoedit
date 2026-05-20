import os
import sys
import time

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
    print("❌ DaVinci Resolve is not running. Please open your project first.")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
current_project = project_manager.GetCurrentProject()
if not current_project:
    print("❌ Error: No project is currently open in DaVinci Resolve. Please open '2605_BCbonacure' first.")
    sys.exit(1)

media_pool = current_project.GetMediaPool()
root_folder = media_pool.GetRootFolder()

print(f"🎬 Connected to Project: '{current_project.GetName()}'")

# ── 1. 遞迴路徑建立與尋找函式 ──────────────────────────────────────
def get_or_create_folder(parent_folder, path_parts):
    if not path_parts:
        return parent_folder
    
    target = path_parts[0]
    sub_folders = parent_folder.GetSubFolderList() or []
    for sub in sub_folders:
        if sub and sub.GetName().lower() == target.lower():
            return get_or_create_folder(sub, path_parts[1:])
            
    # 如果子資料夾不存在，則建立它
    print(f"📁 Creating folder '{target}' under '{parent_folder.GetName()}'...")
    media_pool.SetCurrentFolder(parent_folder)
    new_sub = media_pool.CreateEmptyFolderInCurrentFolder(target)
    
    # 再次檢查確保成功取得
    time.sleep(0.5)
    sub_folders = parent_folder.GetSubFolderList() or []
    for sub in sub_folders:
        if sub and sub.GetName().lower() == target.lower():
            return get_or_create_folder(sub, path_parts[1:])
            
    return None

# 建立 Master/Video/D2/CLIP 資料夾階層
print("📂 Organizing Media Pool folders...")
clip_folder = get_or_create_folder(root_folder, ["Video", "D2", "CLIP"])
if not clip_folder:
    print("❌ Error: Failed to navigate or create Video/D2/CLIP folder structure.")
    sys.exit(1)

# ── 2. 導入 65 個秀場 Raw 影片素材 ───────────────────────────────
media_pool.SetCurrentFolder(clip_folder)
src_video_dir = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video\D2\PRIVATE\M4ROOT\CLIP"

print(f"🔍 Scanning local Sony raw clips in: {src_video_dir}...")
if not os.path.exists(src_video_dir):
    print(f"❌ Error: Local source video directory '{src_video_dir}' not found on Google Drive stream.")
    sys.exit(1)

all_files = os.listdir(src_video_dir)
video_paths = []
for f in all_files:
    if f.upper().endswith(".MP4"):
        full_path = os.path.join(src_video_dir, f)
        video_paths.append(full_path)

# 過濾已在 Media Pool 中的素材，避免重複導入
existing_clips = clip_folder.GetClipList() or []
existing_names = {c.GetName().lower() for c in existing_clips if c}

clips_to_import = [p for p in video_paths if os.path.basename(p).lower() not in existing_names]

if clips_to_import:
    print(f"📥 Importing {len(clips_to_import)} new Sony MP4 clips to '{clip_folder.GetName()}'...")
    imported_clips = media_pool.ImportMedia(clips_to_import)
    if imported_clips:
        print(f"🎉 Success: Imported {len(imported_clips)} video files!")
    else:
        print("❌ Error: Media Pool rejected video file imports.")
else:
    print("✅ All video clips are already loaded in the Media Pool. Skipping import.")

# ── 3. 導入 BGM 音樂素材 ─────────────────────────────────────────
media_pool.SetCurrentFolder(root_folder)
src_bgm_path = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Music\Indian Walk - Nico Staf.mp3"

print(f"🎵 Checking BGM track: '{os.path.basename(src_bgm_path)}'...")
if not os.path.exists(src_bgm_path):
    print(f"❌ Error: Background music '{src_bgm_path}' not found on Google Drive stream.")
    sys.exit(1)

# 檢查 BGM 是否已在根目錄
root_clips = root_folder.GetClipList() or []
bgm_exists = False
for c in root_clips:
    if c and "indian walk" in c.GetName().lower():
        bgm_exists = True
        break

if not bgm_exists:
    print(f"📥 Importing background music: '{os.path.basename(src_bgm_path)}'...")
    imported_bgm = media_pool.ImportMedia([src_bgm_path])
    if imported_bgm:
        print("🎉 Success: BGM imported successfully!")
    else:
        print("❌ Error: Failed to import BGM track.")
else:
    print("✅ BGM 'Indian Walk' is already in the Media Pool. Skipping BGM import.")

print("\n🚀 Ready! Launching AI Rhythmic Event Highlight Editor to reconstruct the timeline...")
time.sleep(1.0)

# ── 4. 自動觸發 run_event_highlight_edit.py ───────────────────────────
import subprocess
result = subprocess.run(["python", "run_event_highlight_edit.py"], capture_output=True, text=True, encoding="utf-8")
print("\n" + "="*60)
print("🤖 TIMELINE BUILDER OUTPUT:")
print("="*60)
print(result.stdout)
if result.stderr:
    print("⚠️ ERRORS/WARNINGS:")
    print(result.stderr)
