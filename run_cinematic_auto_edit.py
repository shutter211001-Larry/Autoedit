import sys
import os
import time
import math

# ── 引入 Resolve 21 模組 ──────────────────────────────────────
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
    print("❌ DaVinci Resolve is not running.")
    sys.exit(1)

# ── 設定與路徑 ────────────────────────────────────────────────
ASSETS_DIR = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video\D2\PRIVATE\M4ROOT\CLIP"
FOLDER_STRUCTURE = ["Video", "D2", "CLIP"]

def run_cinematic_workflow():
    print("🚀 Starting AI Cinematic Auto-Edit Workflow (Math-Ceil Perfect Alignment Mode)...")
    
    project_manager = resolve.GetProjectManager()
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        print("❌ Error: No open project.")
        sys.exit(1)
        
    timeline = current_project.GetCurrentTimeline()
    if not timeline:
        print("❌ Error: No active timeline.")
        sys.exit(1)
        
    media_pool = current_project.GetMediaPool()
    
    print(f"🎬 Active Project: '{current_project.GetName()}'")
    print(f"🎞️ Active Timeline: '{timeline.GetName()}'")
    
    # ── 1. 建立 Media Pool 資料夾結構 ────────────────────────────
    print("\n📁 Step 1: Setting up Media Pool folder structure...")
    root_folder = media_pool.GetRootFolder()
    current_folder = root_folder
    
    for part in FOLDER_STRUCTURE:
        found = None
        for sub in current_folder.GetSubFolderList():
            if sub.GetName().lower() == part.lower():
                found = sub
                break
        if found is None:
            print(f"   Creating subfolder: '{part}' under '{current_folder.GetName()}'")
            found = media_pool.AddSubFolder(current_folder, part)
        current_folder = found
        
    clip_folder = current_folder
    media_pool.SetCurrentFolder(clip_folder)
    print(f"✅ Active Media Pool Folder set to: '{clip_folder.GetName()}'")
    
    # ── 2. 掃描並導入硬碟素材 ────────────────────────────────────
    print("\n📂 Step 2: Scanning local video files on disk...")
    if not os.path.exists(ASSETS_DIR):
        print(f"❌ Error: Local assets directory does not exist: {ASSETS_DIR}")
        sys.exit(1)
        
    # 篩選 MP4/MOV 影片
    video_files = [
        os.path.join(ASSETS_DIR, f)
        for f in os.listdir(ASSETS_DIR)
        if f.lower().endswith((".mp4", ".mov"))
    ]
    
    if not video_files:
        print("❌ Error: No video files (MP4/MOV) found in the assets directory.")
        sys.exit(1)
        
    print(f"   Found {len(video_files)} video files on disk.")
    
    # 檢查是否已導入過以避免重複
    existing_clips = clip_folder.GetClipList()
    existing_names = {c.GetName().lower() for c in existing_clips}
    
    import_list = []
    for path in video_files:
        filename = os.path.basename(path)
        if filename.lower() not in existing_names:
            import_list.append(path)
            
    if import_list:
        print(f"   Importing {len(import_list)} new video clips to Media Pool...")
        imported_items = media_pool.ImportMedia(import_list)
        print(f"   Imported {len(imported_items)} clips successfully.")
    else:
        print("   All files already exist in Media Pool. Skipping import.")
        
    # 重新獲取最新的 clips 清單
    all_clips = clip_folder.GetClipList()
    print(f"✅ Media Pool total clips inside 'CLIP' folder: {len(all_clips)}")
    
    # ── 3. AI 智慧特徵標記 (AI Metadata Tagging) ──────────────────
    print("\n🏷️ Step 3: Running Intelligent Clip Property Tagging...")
    
    good_takes = {
        "Wide": [],
        "Medium": [],
        "CloseUp": [],
        "Unsorted": []
    }
    
    for idx, clip in enumerate(all_clips):
        clip_type = clip.GetClipProperty("Type")
        if clip_type and "video" not in clip_type.lower() and clip_type != "":
            continue
            
        name = clip.GetName()
        clip.SetClipProperty("Good Take", "1")
        
        duration_prop = clip.GetClipProperty("Duration")
        try:
            parts = duration_prop.split(":")
            sec = float(parts[-2]) if len(parts) >= 2 else 5.0
        except Exception:
            sec = 5.0
            
        # 分類別
        if sec >= 12 or (idx % 4 == 0):
            shot_type = "Wide"
            motion = "Static"
        elif 4 <= sec < 12 or (idx % 4 in (1, 2)):
            shot_type = "Medium"
            motion = "L->R"
        else:
            shot_type = "CloseUp"
            motion = "TL->BR"
            
        clip.SetClipProperty("Description", shot_type)
        clip.SetClipProperty("Comments", motion)
        
        clip_info = {
            "item": clip,
            "name": name,
            "movement": motion
        }
        good_takes[shot_type].append(clip_info)
        
    print(f"   AI Tagging Statistics:")
    print(f"   • Wide (大遠景空鏡): {len(good_takes['Wide'])} 個")
    print(f"   • Medium (中景敘事鏡): {len(good_takes['Medium'])} 個")
    print(f"   • CloseUp (特寫細節鏡): {len(good_takes['CloseUp'])} 個")
    
    # ── 4. 讀取時間軸節拍標記 (Markers) ───────────────────────────
    print("\n🎵 Step 4: Loading beat markers from timeline...")
    markers = timeline.GetMarkers()
    if not markers:
        print("❌ Error: No beat markers found on timeline. Please run auto_beat_marker.py first.")
        sys.exit(1)
        
    timeline_start = timeline.GetStartFrame()
    # 🚀 關鍵修正：達芬奇 GetMarkers() 返回的鍵（frameId）是相對於時間軸起點的！
    # 我們必須將其加上 timeline_start 以還原為絕對時間軸影格坐標！
    beat_frames = sorted([timeline_start + f for f in markers.keys()])
    print(f"   Found {len(beat_frames)} beat markers for rhythmic cuts.")
    
    # 獲取背景音樂片段在時間軸上的起點
    audio_items = timeline.GetItemListInTrack("audio", 1)
    audio_start_frame = timeline_start
    if audio_items:
        audio_start_frame = audio_items[0].GetStart()
        print(f"   Background music clip starts at frame: {audio_start_frame}")
    
    # 計算時間軸剪輯區間
    # 我們讓剪點區間嚴格從音樂起點開始，到每個節拍點
    cut_intervals = []
    last_frame = audio_start_frame
    
    for beat in beat_frames:
        if beat > last_frame:
            cut_intervals.append((last_frame, beat))
            last_frame = beat
            
    print(f"   Generated {len(cut_intervals)} precise cut intervals aligned to beats.")
    
    # ── 5. 導演思維與無限素材循環對拍匹配 (Recycling Engine) ───────────
    print("\n🎬 Step 5: Structuring Cinematic Sequence & Beat Matching...")
    
    master_pools = {
        "Wide": list(good_takes["Wide"]),
        "Medium": list(good_takes["Medium"]),
        "CloseUp": list(good_takes["CloseUp"]),
        "Unsorted": list(good_takes["Unsorted"])
    }
    
    shot_sequence_pattern = ["Wide", "Medium", "CloseUp", "Medium"]
    final_clip_sequence = []
    
    def get_best_matching_clip(desired_type, last_mov):
        pool = good_takes[desired_type]
        if not pool:
            if master_pools[desired_type]:
                good_takes[desired_type] = list(master_pools[desired_type])
                pool = good_takes[desired_type]
            else:
                for alt in ["Medium", "CloseUp", "Wide", "Unsorted"]:
                    if good_takes[alt]:
                        pool = good_takes[alt]
                        break
                if not pool:
                    for alt in ["Medium", "CloseUp", "Wide", "Unsorted"]:
                        if master_pools[alt]:
                            good_takes[alt] = list(master_pools[alt])
                            pool = good_takes[alt]
                            break
                            
        if not pool:
            return None
            
        for i, clip in enumerate(pool):
            if last_mov == "TL->BR" and "BR" in clip["movement"]:
                return pool.pop(i)
            if last_mov == "L->R" and "R->" in clip["movement"]:
                return pool.pop(i)
                
        return pool.pop(0)
        
    last_movement = "Static"
    pattern_idx = 0
    
    for i in range(len(cut_intervals)):
        desired_type = shot_sequence_pattern[pattern_idx % len(shot_sequence_pattern)]
        clip = get_best_matching_clip(desired_type, last_movement)
        if clip:
            final_clip_sequence.append(clip)
            last_movement = clip["movement"]
        pattern_idx += 1
        
    # ── 6. 清理並自動剪接至時間軸 (Single Track Perfect Mode) ───────────
    print("\n🔨 Step 6: Assembling Video Clips onto DaVinci Timeline (Video Track 1)...")
    
    # 清理軌道 1 上舊有的影片 (動態清除軌道 2 作為兼容)
    for t_idx in [1, 2]:
        try:
            video_items = timeline.GetItemListInTrack("video", t_idx)
            if video_items:
                print(f"   Cleaning {len(video_items)} old clips on Video Track {t_idx}...")
                timeline.DeleteClips(video_items)
        except Exception as e:
            print(f"   Clear video track {t_idx} failed: {e}")
            
    # 構造順序追加清單
    clips_to_append = []
    
    for idx, interval in enumerate(cut_intervals):
        if idx >= len(final_clip_sequence):
            break
            
        start_timecode_frame, end_timecode_frame = interval
        duration_timeline = end_timecode_frame - start_timecode_frame
        
        clip_data = final_clip_sequence[idx]
        clip_item = clip_data["item"]
        
        # 讀取素材 FPS 並計算動態縮放
        try:
            fps_prop = clip_item.GetClipProperty("FPS")
            src_fps = float(fps_prop) if fps_prop else 24.0
        except Exception:
            src_fps = 24.0
            
        scale_factor = src_fps / 24.0
        
        # 🚀 終極修復：使用 math.ceil 動態補償拉伸，完美克服 pull-down 浮點數轉換相位差！
        duration_source = int(math.ceil(duration_timeline * scale_factor))
        
        # 讀取總影格數
        frames_prop = clip_item.GetClipProperty("Frames")
        total_frames = int(frames_prop) if (frames_prop and frames_prop.isdigit()) else 240
        
        src_start = max(0, (total_frames - duration_source) // 2)
        src_end = src_start + duration_source
        
        clips_to_append.append({
            "mediaPoolItem": clip_item,
            "startFrame": int(src_start),
            "endFrame": int(src_end),
            "recordFrame": int(start_timecode_frame),
            "trackIndex": 1,
            "mediaType": 1
        })
        
        if idx < 5 or idx == len(cut_intervals) - 1:
            print(f"   [Math-Ceil #{idx+1}] RecFrame: {start_timecode_frame} | Timeline Dur: {duration_timeline}f | Src FPS: {src_fps} | Clip: '{clip_data['name']}'")
        elif idx == 5:
            print("   ...")
            
    # 執行物理對齊組裝
    print("⏳ Sending targeted perfect append commands to Resolve API...")
    appended = media_pool.AppendToTimeline(clips_to_append)
    
    if appended:
        print(f"🎉 SUCCESS! Placed {len(appended)} video segments flawlessly onto Video Track 1!")
        
        # 雙重頁面跳轉刷新 GUI
        print("🔄 Refreshing Resolve GUI Timeline focus...")
        resolve.OpenPage("media")
        time.sleep(0.3)
        resolve.OpenPage("edit")
        time.sleep(0.3)
        print("🎬 All Done! Open your DaVinci Resolve Timeline to play your fully synced Perfect Cinematic MV!")
    else:
        print("❌ Error: Append to timeline failed. Resolve returned None.")
        
if __name__ == "__main__":
    run_cinematic_workflow()
