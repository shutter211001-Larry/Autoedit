import sys
import os
import time

RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

def connect_to_resolve():
    """
    Connect to DaVinci Resolve script application interface.
    """
    try:
        import DaVinciResolveScript as dvr_script  # type: ignore
        resolve = dvr_script.scriptapp("Resolve")
    except ImportError as e:
        print(f"❌ Cannot load DaVinciResolveScript SDK: {e}")
        return None
    if not resolve:
        print("❌ DaVinci Resolve is not running. Please open your project first.")
        return None
    return resolve

def setup_project_and_timeline(resolve, project_name, timeline_name, is_vertical=True):
    """
    Loads the project, deletes or backs up the existing timeline,
    sets the resolution, and creates a fresh empty timeline.
    """
    project_manager = resolve.GetProjectManager()
    current_project = project_manager.GetCurrentProject()
    
    # 確保載入正確專案
    if not current_project or current_project.GetName() != project_name:
        print(f"   🔄 Switching project to '{project_name}'...")
        project_manager.LoadProject(project_name)
        current_project = project_manager.GetCurrentProject()
        
    if not current_project:
        print(f"   ❌ Error: Project '{project_name}' could not be loaded.")
        return None, None, None, None
        
    media_pool = current_project.GetMediaPool()
    
    # 1. 整理舊同名時間軸
    timeline_count = current_project.GetTimelineCount()
    for i in range(1, timeline_count + 1):
        tl = current_project.GetTimelineByIndex(i)
        if tl and tl.GetName() == timeline_name:
            print(f"   ⚠️ 偵測到已存在同名時間軸 '{timeline_name}'，將清空並重新命名舊備份...")
            current_project.SetCurrentTimeline(tl)
            for track_type in ["video", "audio"]:
                tc = tl.GetTrackCount(track_type)
                for t_idx in range(1, tc + 1):
                    items = tl.GetItemListInTrack(track_type, t_idx)
                    if items:
                        tl.DeleteClips(items)
            tl.SetName(f"{timeline_name}_Backup_{int(time.time())}")
            break
            
    # 2. 設定解像度
    if is_vertical:
        print("   📱 Setting timeline resolution to 1080x1920 (9:16 Vertical)...")
        current_project.SetSetting("timelineResolutionWidth", "1080")
        current_project.SetSetting("timelineResolutionHeight", "1920")
    else:
        print("   🖥️ Setting timeline resolution to 1920x1080 (16:9 Horizontal)...")
        current_project.SetSetting("timelineResolutionWidth", "1920")
        current_project.SetSetting("timelineResolutionHeight", "1080")
        
    # 3. 建立全新時間軸
    print(f"   🆕 建立全新空白時間軸: '{timeline_name}'...")
    timeline = media_pool.CreateEmptyTimeline(timeline_name)
    if not timeline:
        print(f"   ❌ Error: Failed to create timeline '{timeline_name}'.")
        return None, None, None, None
        
    # 確保至少有兩個音軌，以便音軌分離
    try:
        audio_track_count = timeline.GetTrackCount("audio")
        if audio_track_count < 2:
            print("   ➕ [AI Track Setup] Adding Audio Track 2 for background music...")
            timeline.AddTrack("audio")
    except Exception as e:
        print(f"   ⚠️ Failed to ensure Audio Track 2: {e}")
        
    current_project.SetCurrentTimeline(timeline)
    
    # 4. GUI 強制重置聚焦
    force_gui_refresh(resolve)
    
    timeline_start = timeline.GetStartFrame()
    fps = float(current_project.GetSetting("timelineFrameRate") or 24.0)
    
    return current_project, timeline, timeline_start, fps

def force_gui_refresh(resolve):
    """
    Force DaVinci Resolve GUI page refreshing to ensure focus is applied correctly.
    """
    try:
        resolve.OpenPage("media")
        time.sleep(0.3)
        resolve.OpenPage("edit")
        time.sleep(0.3)
        print("   🔄 GUI Timeline Focus Forced successfully.")
    except Exception as e:
        print(f"   ⚠️ GUI Refresh Failed: {e}")

def find_clip_by_name(folder, query):
    """
    Recursively search for a media clip by query string in the current folder.
    """
    for clip in folder.GetClipList() or []:
        if query.lower() in clip.GetName().lower():
            return clip
    for sub in folder.GetSubFolderList() or []:
        res = find_clip_by_name(sub, query)
        if res:
            return res
    return None

def import_bgm_if_needed(media_pool, root_folder, bgm_path_local):
    """
    Finds BGM clip in media pool or imports it from local path if missing.
    """
    bgm_filename = os.path.basename(bgm_path_local)
    bgm_name_no_ext = os.path.splitext(bgm_filename)[0]
    
    # 先搜尋媒體庫
    bgm_clip = find_clip_by_name(root_folder, bgm_name_no_ext)
    if not bgm_clip:
        if os.path.exists(bgm_path_local):
            print(f"   📥 Importing BGM from: {bgm_path_local}...")
            media_pool.SetCurrentFolder(root_folder)
            imported = media_pool.ImportMedia([bgm_path_local])
            if imported:
                bgm_clip = imported[0]
                print("   🎉 BGM imported successfully!")
        else:
            print(f"   ❌ Error: BGM local file not found at {bgm_path_local}")
            return None
            
    return bgm_clip

def clear_scratch_audio(timeline):
    """
    Clears camera ambient audio tracks on Audio Track 1.
    """
    try:
        cam_audio_items = timeline.GetItemListInTrack("audio", 1)
        if cam_audio_items:
            print("   🧹 Clearing camera scratch audio from Audio Track 1...")
            timeline.DeleteClips(cam_audio_items)
            return True
    except Exception as e:
        print(f"   ⚠️ Clear scratch audio note: {e}")
    return False

def append_video_sequence(media_pool, clips_to_append):
    """
    Appends the sequential video cuts list to the current empty timeline.
    """
    print("   ⏳ Submitting sequential cuts to DaVinci Resolve...")
    appended = media_pool.AppendToTimeline(clips_to_append)
    return appended

def append_bgm(media_pool, bgm_clip, best_t, max_duration_sec, timeline_start, fps):
    """
    Targeted appends the cropped background music clip to Audio Track 2.
    """
    # 確保當前時間軸至少有兩個音軌
    try:
        import DaVinciResolveScript as dvr_script  # type: ignore
        resolve = dvr_script.scriptapp("Resolve")
        if resolve:
            current_project = resolve.GetProjectManager().GetCurrentProject()
            timeline = current_project.GetCurrentTimeline()
            if timeline:
                audio_track_count = timeline.GetTrackCount("audio")
                if audio_track_count < 2:
                    print("   ➕ [AI Track Setup] Adding Audio Track 2 before appending BGM...")
                    timeline.AddTrack("audio")
    except Exception as e:
        print(f"   ⚠️ Track addition check failed: {e}")

    print("   🎧 [AI Music Climax] Appending cropped BGM onto Audio Track 2...")
    bgm_to_append = [{
        "mediaPoolItem": bgm_clip,
        "startFrame": int(best_t * fps),
        "endFrame": int((best_t + max_duration_sec) * fps),
        "recordFrame": int(timeline_start),
        "trackIndex": 2,
        "mediaType": 2
    }]
    success = media_pool.AppendToTimeline(bgm_to_append)
    if success:
        print("   🎉 SUCCESS: Crop BGM placed perfectly on Audio Track 2!")
        return True
    else:
        print("   ❌ Error: Crop BGM targeted append returned None.")
        return False

def append_outro_logos(media_pool, timeline, root_folder, logo_configs, logo_start_frame, logo_duration_frames):
    """
    Imports and targeted-appends branding logos on Video Tracks 2 & 3.
    """
    print("\n🖼️ Step 9: Overlaying Brand Outro Logos on Video Track 2 & 3...")
    appended_any = False
    
    # 搜尋或導入每個 Logo
    logo_list = []
    for config in logo_configs:
        logo_name = config["name"]
        track_idx = config["track"]
        
        # 尋找 logo 檔案
        # 預設搜尋同層或絕對路徑
        logo_path = os.path.abspath(logo_name)
        if not os.path.exists(logo_path):
            # 橫越專案常見資料夾
            possible_paths = [
                os.path.join(r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video\D2\PRIVATE\M4ROOT\CLIP", logo_name),
                os.path.join(r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video", logo_name),
                os.path.join(r"G:\共用雲端硬碟\專業髮品\04影音部\Larry", logo_name),
                os.path.join(os.getcwd(), logo_name)
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    logo_path = p
                    break
        
        logo_clip = find_clip_by_name(root_folder, os.path.splitext(logo_name)[0])
        if not logo_clip and os.path.exists(logo_path):
            print(f"   📥 Importing Outro Logo: {logo_name}...")
            media_pool.SetCurrentFolder(root_folder)
            imported = media_pool.ImportMedia([logo_path])
            if imported:
                logo_clip = imported[0]
                
        if logo_clip:
            logo_list.append({
                "clip": logo_clip,
                "config": config
            })
        else:
            print(f"   ⚠️ Warning: Could not locate or import logo '{logo_name}'!")
            
    if not logo_list:
        print("   ⚠️ No logo clips found or imported.")
        return False
        
    # 準備置入清單
    logos_to_append = []
    for item in logo_list:
        logos_to_append.append({
            "mediaPoolItem": item["clip"],
            "startFrame": 0,
            "endFrame": int(logo_duration_frames),
            "recordFrame": int(logo_start_frame),
            "trackIndex": item["config"]["track"],
            "mediaType": 1
        })
        
    appended_logos = media_pool.AppendToTimeline(logos_to_append)
    if appended_logos:
        print("   🎉 SUCCESS: Branding Logos appended to timeline!")
        time.sleep(0.5)
        
        # 套用幾何特徵設定
        for item in logo_list:
            cfg = item["config"]
            track_idx = cfg["track"]
            logo_items = timeline.GetItemListInTrack("video", track_idx)
            if logo_items:
                # 取得放置在該軌道上最晚的片段 (通常是我們剛放的那個)
                logo_clip_item = logo_items[-1]
                try:
                    logo_clip_item.SetProperty("ZoomX", cfg["zoom"])
                    logo_clip_item.SetProperty("ZoomY", cfg["zoom"])
                    logo_clip_item.SetProperty("Pan", cfg["pan"])
                    logo_clip_item.SetProperty("Tilt", cfg["tilt"])
                except Exception as e:
                    print(f"   ⚠️ Failed to set geometry properties for logo on Track {track_idx}: {e}")
                    
        print("   ✅ Configured Brand Logo coordinates and scales successfully.")
        return True
    else:
        print("   ❌ Error: Logos targeted append returned None.")
        return False

def apply_director_motions_and_grades(timeline, cut_intervals, source_footage_vertical=True):
    """
    Applies motion transforms, rotative cuts, timeline clip color markers, 
    and clones grade settings from Clip 1 to all subsequent clips.
    """
    print("\n🎥 Step 10: Directing AI Camera Motions & Narrative Colors...")
    placed_clips = timeline.GetItemListInTrack("video", 1)
    if not placed_clips:
        print("   ❌ Error: No clips found on Video Track 1!")
        return False
        
    from core.director_rules import get_transform_properties
    
    for idx, item in enumerate(placed_clips):
        if idx >= len(cut_intervals):
            break
        start_f, end_f, role = cut_intervals[idx]
        
        zoom_val, rotation_val, color_name = get_transform_properties(idx, role, source_footage_vertical)
        
        try:
            item.SetProperty("ZoomX", zoom_val)
            item.SetProperty("ZoomY", zoom_val)
            item.SetProperty("RotationAngle", rotation_val)
            item.SetClipColor(color_name)
        except Exception as e:
            print(f"   ⚠️ Transform settings failed on clip #{idx+1}: {e}")
            
    print("   ✅ Directed camera transforms and applied clip narrative colors.")
    
    # 大師級一鍵複製調色節點 (CopyGrades Cloning)
    if len(placed_clips) > 1:
        try:
            source_clip = placed_clips[0]
            target_clips = list(placed_clips[1:])
            success_copy = source_clip.CopyGrades(target_clips)
            if success_copy:
                print("   👑 SUCCESS: Automatically copied node-graph color grade from Clip #1 to all subsequent clips!")
            else:
                print("   ⚠️ Note: CopyGrades API returned False (typical database sync block).")
        except Exception as e:
            print(f"   ⚠️ Auto grade clone failed: {e}")
            
    return True
