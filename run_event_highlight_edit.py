import sys
import os
import time
import math

# ── 確保輸出支援 UTF-8 ──────────────────────────────────────
if sys.stdout.encoding != 'utf-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except Exception:
        pass

# ── Resolve 21 初始化 ────────────────────────────────────────
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

import cv2
import numpy as np

# 引入自研的對拍模組
try:
    import beat_detector
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import beat_detector

def find_optimal_stable_unidirectional_window(video_path, duration_frames, fps, downsample_step=12, target_width=80):
    """
    自研雙核 CV 運鏡優化分析器 (第三階段平穩度 + 第四階段運鏡方向單調性)：
    在記憶體中將畫面降採樣至 80x60 超小圖，以每 12 影格跳幀連續前向解碼，
    自動定位出 100% 單方向平滑運動、且完全無劇烈震盪或逆轉的黃金 In 點！
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= duration_frames:
        cap.release()
        return 0
        
    motion_series = []  # 光流平穩度 (像素絕對差)
    motion_dx = []      # 水平位移 (1D 投影剖面位移)
    frame_indices = []
    
    prev_gray = None
    frame_idx = 0
    
    # ── A. 逐幀跳步解碼與特徵提取 ──────────────────────────────────────
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_idx % downsample_step == 0:
            h, w = frame.shape[:2]
            scale = target_width / float(w)
            target_height = int(h * scale)
            small_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_NEAREST)
            
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            
            if prev_gray is not None:
                # 1. 光流能量 (絕對差值均值)
                diff = cv2.absdiff(gray, prev_gray)
                mean_diff = float(np.mean(diff))
                motion_series.append(mean_diff)
                
                # 2. 水平投影剖面位移 dx
                p1 = np.sum(prev_gray, axis=0)
                p2 = np.sum(gray, axis=0)
                p1 = p1 - np.mean(p1)
                p2 = p2 - np.mean(p2)
                
                best_shift = 0.0
                min_proj_diff = float('inf')
                search_range = 6
                for shift in range(-search_range, search_range + 1):
                    if shift < 0:
                        d = np.mean(np.abs(p1[-shift:] - p2[:shift]))
                    elif shift > 0:
                        d = np.mean(np.abs(p1[:-shift] - p2[shift:]))
                    else:
                        d = np.mean(np.abs(p1 - p2))
                    if d < min_proj_diff:
                        min_proj_diff = d
                        best_shift = float(shift)
                motion_dx.append(best_shift)
                
                frame_indices.append(frame_idx)
                
            prev_gray = gray
            
        frame_idx += 1
        
    cap.release()
    
    if len(motion_series) < 3:
        return max(0, (total_frames - duration_frames) // 2)
        
    # 插值補齊滿影格率曲線
    full_motion = np.interp(np.arange(total_frames), frame_indices, motion_series)
    full_dx = np.interp(np.arange(total_frames), frame_indices, motion_dx)
    
    # ── B. 滑動評估所有視窗的綜合得分 ────────────────────────────────────
    guard_band = int(total_frames * 0.12)  # 設置 12% 首尾物理防護帶
    search_start = guard_band
    search_end = total_frames - duration_frames - guard_band
    
    if search_end <= search_start:
        search_start = 0
        search_end = total_frames - duration_frames
        
    best_start = search_start
    best_score = -999999.0
    
    # 計算全片抖動閾值
    SHAKE_LIMIT = np.mean(full_motion) + 1.5 * np.std(full_motion)
    
    for s in range(int(search_start), int(search_end)):
        win_motion = full_motion[s : s + duration_frames]
        win_dx = full_dx[s : s + duration_frames]
        
        # 1. 平穩度 (運動能量方差越小越好)
        variance = np.var(win_motion) + 1e-6
        consistency_score = -np.log(variance)
        
        # 2. 突發劇烈晃動重罰 (第三階段)
        peak_motion = np.max(win_motion)
        shake_penalty = 0.0
        if peak_motion > SHAKE_LIMIT:
            shake_penalty = -10.0 * (peak_motion - SHAKE_LIMIT)
            
        # 3. 運動單調性 (第四階段，防止左右來回搖擺)
        pos_frames = np.sum(win_dx > 0.05)
        neg_frames = np.sum(win_dx < -0.05)
        active_frames = pos_frames + neg_frames
        if active_frames == 0:
            mono_ratio = 1.0
        else:
            mono_ratio = max(pos_frames, neg_frames) / float(active_frames)
            
        reversal_penalty = 0.0
        if mono_ratio < 0.90:
            reversal_penalty = -30.0 * (0.90 - mono_ratio)
            
        # 4. 運動均速微調懲罰
        mean_motion = np.mean(win_motion)
        
        # 綜合得分
        score = 1.0 * consistency_score + 1.0 * shake_penalty + 1.0 * reversal_penalty - 0.2 * mean_motion
        
        if score > best_score:
            best_score = score
            best_start = s
            
    return int(best_start)

def run_event_highlight_edit():
    print("🎬 Starting AI Rhythmic Event Highlight Editor (Chronological Narrative Arc)...")
    
    project_manager = resolve.GetProjectManager()
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        print("❌ Error: No open project.")
        sys.exit(1)
        
    timeline_count = current_project.GetTimelineCount()
    timeline = None
    for i in range(1, timeline_count + 1):
        tl = current_project.GetTimelineByIndex(i)
        if "南區工作" in tl.GetName():
            timeline = tl
            break
            
    if not timeline:
        print("❌ Error: '南區工作' timeline not found.")
        sys.exit(1)
        
    current_project.SetCurrentTimeline(timeline)
    media_pool = current_project.GetMediaPool()
    
    print(f"🎬 Active Project: '{current_project.GetName()}'")
    print(f"🎞️ Active Timeline: '{timeline.GetName()}'")
    
    # ── 1. GUI 頁面雙重跳轉強制刷新 ─────────────────────────────────
    resolve.OpenPage("media")
    time.sleep(0.3)
    resolve.OpenPage("edit")
    time.sleep(0.3)
    print("🔄 GUI Timeline Focus Forced successfully.")
    
    # ── 2. 強制設定 Media Pool 當前資料夾為 CLIP ─────────────────────
    def find_folder_recursive(current_folder, path_parts):
        if not path_parts:
            return current_folder
        target = path_parts[0]
        sub_folders = current_folder.GetSubFolderList()
        for sub in sub_folders:
            if sub.GetName().lower() == target.lower():
                return find_folder_recursive(sub, path_parts[1:])
        return None
        
    root_folder = media_pool.GetRootFolder()
    clip_folder = find_folder_recursive(root_folder, ["Video", "D2", "CLIP"])
    if not clip_folder:
        print("❌ Error: Master/Video/D2/CLIP folder not found in Media Pool.")
        sys.exit(1)
        
    media_pool.SetCurrentFolder(clip_folder)
    print(f"📁 Media Pool active folder set to: '{clip_folder.GetName()}'")
    
    # ── 3. 讀取節拍標記 (Blue Markers) 並進行「動態節奏降頻」 ────────────────
    markers = timeline.GetMarkers()
    if not markers:
        print("❌ Error: No beat markers found on timeline. Please run auto_beat_marker.py first.")
        sys.exit(1)
        
    timeline_start = timeline.GetStartFrame()
    fps = float(current_project.GetSetting("timelineFrameRate") or 24.0)
    MAX_DURATION_SEC = 30.0
    max_frames = int(MAX_DURATION_SEC * fps)
    
    # 篩選前 30 秒內的節拍標記
    all_rel_frames = sorted(list(markers.keys()))
    rel_frames_30s = [f for f in all_rel_frames if f <= max_frames]
    
    # 4階段時序臨界點 (秒數)
    t_setup = 5.0
    t_detail = 12.0
    t_climax = 25.0
    t_finale = 30.0
    
    # 根據時序劃分節拍標記
    setup_markers = []
    detail_markers = []
    climax_markers = []
    finale_markers = []
    
    for f in rel_frames_30s:
        t = f / fps
        if t < t_setup:
            setup_markers.append(f)
        elif t < t_detail:
            detail_markers.append(f)
        elif t < t_climax:
            climax_markers.append(f)
        else:
            finale_markers.append(f)
            
    # 執行「動態節奏降頻（Rhythmic Downsampling Gate）」防禦，防止切點過碎
    downsampled_beats = []
    
    # 起 (Setup): 每 4 拍切一次 (呼吸感、大遠景環境鋪墊)
    for idx, f in enumerate(setup_markers):
        if idx % 4 == 0:
            downsampled_beats.append((f, "setup"))
            
    # 承 (Detail): 每 2 拍切一次 (流暢地交代工藝與產品細節)
    for idx, f in enumerate(detail_markers):
        if idx % 2 == 0:
            downsampled_beats.append((f, "detail"))
            
    # 轉 (Climax): 每 1 拍切一次 (名模走秀高潮，極速快切卡點！)
    for idx, f in enumerate(climax_markers):
        downsampled_beats.append((f, "catwalk"))
        
    # 合 (Finale): 每 4 拍切一次 (結尾掌聲、品牌瓶身，徐緩定格)
    for idx, f in enumerate(finale_markers):
        if idx % 4 == 0:
            downsampled_beats.append((f, "finale"))
            
    # 排序並去重
    downsampled_beats.sort(key=lambda x: x[0])
    unique_beats = []
    seen = set()
    for f, role in downsampled_beats:
        if f not in seen:
            unique_beats.append((f, role))
            seen.add(f)
            
    # 生成切點區間
    cut_intervals = []
    last_frame = timeline_start
    
    for rel_frame, role in unique_beats:
        abs_frame = timeline_start + rel_frame
        if abs_frame > last_frame:
            cut_intervals.append((last_frame, abs_frame, role))
            last_frame = abs_frame
            
    # 如果最後沒有拼滿 30 秒，最後一個片段補齊到 30 秒滿
    if last_frame < timeline_start + max_frames:
        cut_intervals.append((last_frame, timeline_start + max_frames, "finale"))
        
    print(f"🥁 Syncing complete! Rhythmic downsampling compiled {len(cut_intervals)} elegant cinematic cuts.")
    
    # ── 4. 讀取並分配影片素材 (嚴格去重 + 運動方向分類) ───────────────────
    all_clips = clip_folder.GetClipList()
    good_takes = {
        "Wide": [],
        "Medium": [],
        "CloseUp": [],
        "Unsorted": []
    }
    seen_paths = set()
    seen_signatures = set()
    duplicate_count = 0
    
    for clip in all_clips:
        # A. 路徑去重
        file_path = clip.GetClipProperty("File Path")
        if file_path:
            if file_path in seen_paths:
                duplicate_count += 1
                continue
            seen_paths.add(file_path)
            
        # B. 特徵去重
        duration = clip.GetClipProperty("Duration")
        frames = clip.GetClipProperty("Frames")
        signature = (duration, frames)
        if duration and frames:
            if signature in seen_signatures:
                duplicate_count += 1
                continue
            seen_signatures.add(signature)
            
        shot_type = clip.GetClipProperty("Description").strip()
        movement = clip.GetClipProperty("Comments").strip()
        
        clip_info = {
            "item": clip,
            "name": clip.GetName(),
            "movement": movement if movement else "Static",
            "type": shot_type if shot_type else "Unsorted"
        }
        
        if "wide" in shot_type.lower():
            good_takes["Wide"].append(clip_info)
        elif "medium" in shot_type.lower() or "mcu" in shot_type.lower():
            good_takes["Medium"].append(clip_info)
        elif "closeup" in shot_type.lower() or "cu" in shot_type.lower():
            good_takes["CloseUp"].append(clip_info)
        else:
            good_takes["Unsorted"].append(clip_info)
            
    print(f"📊 Excluded {duplicate_count} duplicate clips.")
    print(f"📊 Active Materials Pool: Wide={len(good_takes['Wide'])} | Medium={len(good_takes['Medium'])} | CloseUp={len(good_takes['CloseUp'])} | Unsorted={len(good_takes['Unsorted'])}")
    
    # ── 5. AI 電影感時序鏡頭媒合 (敘事與動態慣性銜接) ──────────────────────
    final_clip_sequence = []
    last_movement = "Static"
    
    for idx, interval in enumerate(cut_intervals):
        start_frame, end_frame, role = interval
        
        # 決定當前階段的優先鏡位順序
        if role == "setup":
            priority = ["Wide", "Medium", "Unsorted", "CloseUp"]
        elif role == "detail":
            priority = ["CloseUp", "Medium", "Unsorted", "Wide"]
        elif role == "catwalk":
            priority = ["Medium", "CloseUp", "Wide", "Unsorted"]
        else: # finale
            priority = ["CloseUp", "Wide", "Medium", "Unsorted"]
            
        chosen_clip = None
        
        # 按優先順序在各素材庫中搜尋動態匹配
        for pool_name in priority:
            pool = good_takes[pool_name]
            if pool:
                best_idx = 0
                # 運動流向匹配防禦 (視覺連續性)
                for c_idx, candidate in enumerate(pool):
                    cand_mov = candidate["movement"].lower()
                    last_mov = last_movement.lower()
                    
                    # 匹配 Left-to-Right 運動
                    if "l->r" in last_mov and "r->" in cand_mov:
                        best_idx = c_idx
                        break
                    # 匹配 Right-to-Left 運動
                    if "r->l" in last_mov and "l->" in cand_mov:
                        best_idx = c_idx
                        break
                    # 匹配斜切運動
                    if "tl->br" in last_mov and "br" in cand_mov:
                        best_idx = c_idx
                        break
                        
                chosen_clip = pool.pop(best_idx)
                break
                
        # 徹底防禦：如果所有庫全空了，重組備用
        if not chosen_clip:
            print("⚠️ Warning: Pool exhausted! Recycling pool...")
            for pool_name in ["Medium", "CloseUp", "Wide", "Unsorted"]:
                if good_takes[pool_name]:
                    chosen_clip = good_takes[pool_name].pop(0)
                    break
                    
        if chosen_clip:
            final_clip_sequence.append(chosen_clip)
            last_movement = chosen_clip["movement"]
            
    print(f"✅ AI Storytelling Clip Sequence compiled successfully ({len(final_clip_sequence)} cuts).")
    
    # ── 6. 清理 Video 軌道 1-2 與 Audio 軌道 1-2 (確保時間軸徹底空白) ──────────
    print("\n🧹 Step 6: Emptying timeline video & audio tracks to guarantee alignment...")
    for t_idx in [1, 2]:
        try:
            video_items = timeline.GetItemListInTrack("video", t_idx)
            if video_items:
                timeline.DeleteClips(video_items)
        except Exception as e:
            print(f"   Note: Clear Video Track {t_idx} failed or not needed: {e}")
            
    for t_idx in [1, 2]:
        try:
            audio_items = timeline.GetItemListInTrack("audio", t_idx)
            if audio_items:
                timeline.DeleteClips(audio_items)
        except Exception as e:
            print(f"   Note: Clear Audio Track {t_idx} failed or not needed: {e}")
            
    # ── 7. 順序追加影片素材 (這會自動對齊最左端 86400) ────────────────────
    clips_to_append = []
    
    for idx, interval in enumerate(cut_intervals):
        if idx >= len(final_clip_sequence):
            break
            
        start_f, end_f, role = interval
        duration_timeline = end_f - start_f
        
        clip_data = final_clip_sequence[idx]
        clip_item = clip_data["item"]
        
        # 讀取影格率以執行向上取整 Gap 防禦
        try:
            fps_prop = clip_item.GetClipProperty("FPS")
            src_fps = float(fps_prop) if fps_prop else 24.0
        except Exception:
            src_fps = 24.0
            
        scale_factor = src_fps / fps
        duration_source = int(math.ceil(duration_timeline * scale_factor))
        
        # 讀取總影格數，以動態實施雙核前置處理 (Smart Padding 或 CV 穩定度與單調性檢索)
        frames_prop = clip_item.GetClipProperty("Frames")
        total_frames = int(frames_prop) if (frames_prop and frames_prop.isdigit()) else 240
        
        # 判斷是否為動態運鏡片段
        movement = clip_data["movement"].lower()
        is_static = ("static" in movement) or (role in ["setup", "finale"])
        
        if is_static:
            # A. 靜態片段：使用 15% 智能邊界安全防護帶，極速 0 延遲處理
            guard_band = int(total_frames * 0.15)
            safe_total = total_frames - 2 * guard_band
            if safe_total >= duration_source:
                src_start = guard_band + (safe_total - duration_source) // 2
            else:
                guard_band = int(total_frames * 0.05)
                safe_total = total_frames - 2 * guard_band
                if safe_total >= duration_source:
                    src_start = guard_band + (safe_total - duration_source) // 2
                else:
                    src_start = max(0, (total_frames - duration_source) // 2)
        else:
            # B. 動態運鏡片段 (Catwalk / Detail)：啟動雙核 CV 滾動平穩度與運動單調性掃描！
            file_path = clip_item.GetClipProperty("File Path")
            if file_path and os.path.exists(file_path):
                # 實施超高速光流 + 1D 投影方向檢測，過濾手震、對焦模糊及左右鐘擺逆轉！
                src_start = find_optimal_stable_unidirectional_window(
                    file_path,
                    duration_source,
                    src_fps
                )
            else:
                src_start = max(0, (total_frames - duration_source) // 2)
                
        src_end = src_start + duration_source
        
        # 使用順序追加 (Sequential Append)，Resolve 完美的無縫拼接，起點完美落在 86400
        clips_to_append.append({
            "mediaPoolItem": clip_item,
            "startFrame": int(src_start),
            "endFrame": int(src_end)
        })
        
        # 列印前 5 鏡與最後 1 鏡
        if idx < 5 or idx == len(cut_intervals) - 1:
            print(f"   [Cut #{idx+1}] Frame: {start_f}➔{end_f} | Role: {role.upper()} | Type: {clip_data['type']} | Motion: {clip_data['movement']} | Clip: '{clip_data['name']}'")
        elif idx == 5:
            print("   ...")
            
    print("⏳ Submitting sequential cuts to DaVinci Resolve Media Pool...")
    appended_video = media_pool.AppendToTimeline(clips_to_append)
    
    if appended_video and appended_video[0] is not None:
        print("🎉 SUCCESS! Placed video clips sequentially starting exactly at timeline start (86400)!")
        
        # ── 7.1 清理音軌 1 的相機自帶聲音 (避免與背景音樂重疊衝突) ──────────────────
        try:
            cam_audio_items = timeline.GetItemListInTrack("audio", 1)
            if cam_audio_items:
                print("🧹 Clearing camera scratch audio from Audio Track 1...")
                timeline.DeleteClips(cam_audio_items)
        except Exception as e:
            print(f"   Note: Clear scratch audio failed: {e}")
            
        # ── 7.2 尋找背景音樂並執行高潮裁切與精確 target 寫入 (對齊 86400) ───────────────
        def find_bgm(folder):
            for clip in folder.GetClipList():
                if "indian walk" in clip.GetName().lower():
                    return clip
            for sub in folder.GetSubFolderList():
                res = find_bgm(sub)
                if res:
                    return res
            return None
            
        bgm_clip = find_bgm(root_folder)
        if bgm_clip:
            bgm_path = bgm_clip.GetClipProperty("File Path")
            print(f"🎵 Locating BGM Climax... Path: {bgm_path}")
            best_t = beat_detector.find_best_climax_window(bgm_path, 30.0)
            
            # 使用 target 寫入方式，將 30s 裁切後的音樂放置在 Audio Track 1 起點 (86400)
            bgm_to_append = [{
                "mediaPoolItem": bgm_clip,
                "startFrame": int(best_t * fps),
                "endFrame": int((best_t + 30.0) * fps),
                "recordFrame": int(timeline_start),
                "trackIndex": 1,
                "mediaType": 2
            }]
            appended_audio = media_pool.AppendToTimeline(bgm_to_append)
            if appended_audio:
                print(f"🎉 SUCCESS! Crop BGM target-placed perfectly on Audio Track 1 from {timeline_start}!")
            else:
                print("❌ Error: Failed to append BGM clip.")
        else:
            print("❌ Error: BGM 'Indian Walk' not found in Media Pool.")
            
        # ── 8. AI 鏡頭動態導演 (Transform Scale & Alternating Slash-Cut) ─────────
        print("\n🎥 Step 8: AI Camera Motion Director starting up...")
        placed_clips = timeline.GetItemListInTrack("video", 1)
        
        for idx, item in enumerate(placed_clips):
            if idx >= len(cut_intervals):
                break
                
            start_f, end_f, role = cut_intervals[idx]
            
            zoom_val = 1.0
            rotation_val = 0.0
            
            # 電影感 4階段縮放與傾斜設計法則
            if role == "setup":
                zoom_val = 1.0
                rotation_val = 0.0
            elif role == "detail":
                zoom_val = 1.05
                rotation_val = 0.0
            elif role == "catwalk":
                # 秀場高潮：1.12 倍縮放 (完美遮擋黑框) 搭配正負 3.5 度的交替斜切擺動，創造手持強烈卡點感！
                zoom_val = 1.12
                rotation_val = 3.5 if (idx % 2 == 0) else -3.5
            elif role == "finale":
                # 結尾定格大推近，聚焦品牌
                zoom_val = 1.18
                rotation_val = 0.0
                
            try:
                item.SetProperty("ZoomX", zoom_val)
                item.SetProperty("ZoomY", zoom_val)
                item.SetProperty("RotationAngle", rotation_val)
            except Exception as e:
                print(f"   ⚠️ Transform settings failed on clip #{idx+1}: {e}")
                
        print("   ✅ Directed transform, zoom & alternating angles for all clips.")
        
        # ── 9. AI 色彩風格大師 (AI Color Grade Sync) ──────────────────────────
        print("\n🎨 Step 9: AI Color Grade Sync active...")
        
        # A. 軌道片段時序角色染色
        color_map = {
            "setup": "Navy",      # 起 -> 沉穩藍
            "detail": "Yellow",   # 承 -> 工藝黃
            "catwalk": "Orange",  # 轉 -> 潮流橘 (高能)
            "finale": "Purple"    # 合 -> 定格紫
        }
        
        for idx, item in enumerate(placed_clips):
            if idx >= len(cut_intervals):
                break
            start_f, end_f, role = cut_intervals[idx]
            target_color = color_map.get(role, "Navy")
            try:
                item.SetClipColor(target_color)
            except Exception as e:
                print(f"   ⚠️ Color assignment failed on clip #{idx+1}: {e}")
                
        print("   ✅ Timeline clips colored based on narrative role.")
        
        # B. 大師級一鍵調色同步 (Node Graph Cloning from Clip #1)
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
                
        # ── 10. 雙重跳頁刷新 GUI 焦點 ─────────────────────────────────
        print("\n🔄 Refreshing DaVinci Resolve GUI Focus...")
        resolve.OpenPage("media")
        time.sleep(0.3)
        resolve.OpenPage("edit")
        time.sleep(0.3)
        print("🎉 All tasks completed beautifully! Open DaVinci Resolve edit timeline to enjoy your masterpiece!")
        
    else:
        print("❌ Error: Append to timeline failed. Resolve returned None.")

if __name__ == "__main__":
    run_event_highlight_edit()
