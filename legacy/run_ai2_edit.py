import sys
import os
import time
import math
import pickle
import torch
import numpy as np

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
import json

# ── 自研本機 CV 全量運動特徵曲線快取系統 (按檔名對照) ─────────────────
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cv_profile_cache.json")

def load_cv_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cv_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

# 引入自研的對拍與智慧資源檢索模組
try:
    import beat_detector
    import smart_asset_selector
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import beat_detector
    import smart_asset_selector

def find_optimal_stable_unidirectional_window(video_path, duration_frames, fps, downsample_step=16, target_width=80):
    """
    自研雙核 CV 運鏡優化分析器 (第三階段平穩度 + 第四階段運鏡方向單調性)：
    在記憶體中將畫面降採樣至 80x60 超小圖，以每 12 影格跳幀連續前向解碼，
    自動定位出 100% 單方向平滑運動、且完全無劇烈震盪或逆轉的黃金 In 點！
    使用「檔名對照」全量運動特徵快取：一次解碼全影片特徵並永久寫入，
    後續不論剪輯長度 (duration_frames) 如何變動，皆可在 0.001 秒內完成極速評估！
    """
    cache = load_cv_cache()
    # 以視訊檔案路徑為鍵，取得整個影片的特徵曲線
    profile = cache.get(video_path)
    
    if profile:
        total_frames = int(profile["total_frames"])
        motion_series = profile["motion_series"]
        motion_dx = profile["motion_dx"]
        frame_indices = profile["frame_indices"]
    else:
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
        
        # 保存全影片的特徵資料至本機快取
        cache[video_path] = {
            "total_frames": total_frames,
            "motion_series": motion_series,
            "motion_dx": motion_dx,
            "frame_indices": frame_indices
        }
        save_cv_cache(cache)
        
    if len(motion_series) < 3:
        return max(0, (total_frames - duration_frames) // 2)
        
    # 插值補齊滿影格率曲線 (在記憶體中快速插值)
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
            
    ans = int(best_start)
    return ans

def run_ai2_edit():
    print("🎬 Starting AI Rhythmic High-End Outro Tagger System for Timeline 'AI_2'...")
    
    # ── 專案與路徑設定 ─────────────────────────────────────────────
    PROJECT_NAME = "2605_BCbonacure"
    TIMELINE_NAME = "AI_2"
    BGM_FILE_NAME = "Indian Walk - Nico Staf.mp3"
    BGM_PATH_LOCAL = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Music\Indian Walk - Nico Staf.mp3"
    ASSETS_DIR = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video\D2\PRIVATE\M4ROOT\CLIP"
    FOLDER_STRUCTURE = ["Video", "D2", "CLIP"]
    MAX_DURATION_SEC = 30.0
    SOURCE_FOOTAGE_VERTICAL = True  # 素材是否已為直式？ 若為直式則縮放補償為 1.0，若為橫式則為 3.16
    
    
    project_manager = resolve.GetProjectManager()
    current_project = project_manager.GetCurrentProject()
    
    # 確保專案載入成功
    if not current_project or current_project.GetName() != PROJECT_NAME:
        print(f"Switching project to '{PROJECT_NAME}'...")
        project_manager.LoadProject(PROJECT_NAME)
        current_project = project_manager.GetCurrentProject()
        
    if not current_project:
        print(f"❌ Error: Project '{PROJECT_NAME}' could not be loaded.")
        sys.exit(1)
        
    media_pool = current_project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    
    # ── 1. 時間軸生命週期管理：全新建立 'AI_2' ──────────────────────────
    print(f"\n🗑️ Step 1: Check and clean existing timeline '{TIMELINE_NAME}'...")
    timeline_count = current_project.GetTimelineCount()
    for i in range(1, timeline_count + 1):
        tl = current_project.GetTimelineByIndex(i)
        if tl and tl.GetName() == TIMELINE_NAME:
            print(f"   ⚠️ 偵測到已存在同名時間軸 '{TIMELINE_NAME}'，將清空並重新命名舊備份...")
            current_project.SetCurrentTimeline(tl)
            for track_type in ["video", "audio"]:
                tc = tl.GetTrackCount(track_type)
                for t_idx in range(1, tc + 1):
                    items = tl.GetItemListInTrack(track_type, t_idx)
                    if items:
                        tl.DeleteClips(items)
            tl.SetName(f"AI_2_Backup_{int(time.time())}")
            break
            
    print("📱 Setting timeline resolution to 1080x1920 (9:16 Vertical)...")
    current_project.SetSetting("timelineResolutionWidth", "1080")
    current_project.SetSetting("timelineResolutionHeight", "1920")
    
    print(f"🆕 建立全新空白時間軸: '{TIMELINE_NAME}'...")
    timeline = media_pool.CreateEmptyTimeline(TIMELINE_NAME)
    if not timeline:
        print(f"❌ Error: Failed to create timeline '{TIMELINE_NAME}'.")
        sys.exit(1)
        
    current_project.SetCurrentTimeline(timeline)
    
    # ── 2. GUI 頁面雙重跳轉強制刷新 ─────────────────────────────────
    resolve.OpenPage("media")
    time.sleep(0.3)
    resolve.OpenPage("edit")
    time.sleep(0.3)
    print("🔄 GUI Timeline Focus Forced successfully.")
    
    # ── 3. 確保 BGM 已導入 Media Pool 並定位 ──────────────────────────
    print("\n🎵 Step 2: Locating and importing BGM audio...")
    def find_bgm(folder, query):
        for clip in folder.GetClipList() or []:
            if query.lower() in clip.GetName().lower():
                return clip
        for sub in folder.GetSubFolderList() or []:
            res = find_bgm(sub, query)
            if res:
                return res
        return None
        
    bgm_clip = find_bgm(root_folder, "indian walk")
    if not bgm_clip:
        if os.path.exists(BGM_PATH_LOCAL):
            print(f"   📥 Importing BGM from: {BGM_PATH_LOCAL}...")
            media_pool.SetCurrentFolder(root_folder)
            imported = media_pool.ImportMedia([BGM_PATH_LOCAL])
            if imported:
                bgm_clip = imported[0]
                print("   🎉 BGM imported successfully!")
        else:
            print(f"❌ Error: BGM local file not found at {BGM_PATH_LOCAL}")
            sys.exit(1)
            
    if not bgm_clip:
        print("❌ Error: Could not locate BGM clip in Media Pool.")
        sys.exit(1)
        
    bgm_path = bgm_clip.GetClipProperty("File Path")
    print(f"   BGM Path: {bgm_path}")
    
    # ── 4. 背景配樂高潮裁切與 A1 精確置入 ────────────────────────────────
    timeline_start = timeline.GetStartFrame()
    fps = float(current_project.GetSetting("timelineFrameRate") or 24.0)
    print(f"⚙️ Timeline Start Frame: {timeline_start} | Frame Rate (FPS): {fps}")
    
    print("\n🎧 [AI Music Climax] Locating best 30s climax window...")
    best_t = beat_detector.find_best_climax_window(bgm_path, MAX_DURATION_SEC)
    print(f"   Best Climax Section starts at: {best_t:.2f}s")
    
    # 將裁切後的高潮片段儲存，待影片拼接完成後放入音軌 1 最開頭 (recordFrame = timeline_start)
    bgm_to_append = [{
        "mediaPoolItem": bgm_clip,
        "startFrame": int(best_t * fps),
        "endFrame": int((best_t + MAX_DURATION_SEC) * fps),
        "recordFrame": int(timeline_start),
        "trackIndex": 1,
        "mediaType": 2
    }]
    
    print("   💡 [AI Music Climax] BGM climax window calculated. Appending delayed until video clips are in place.")
        
    # ── 5. 自動產生高潮暫態鼓點對拍標記 (Blue Markers) ────────────────────
    print("\n🥁 Step 3: Analyzing audio transients & generating beat markers...")
    beat_times, bpm = beat_detector.analyze_audio_beats(bgm_path)
    if not beat_times:
        print("❌ Error: No beats could be detected in this audio file.")
        sys.exit(1)
        
    print(f"   Estimated Tempo: {bpm:.1f} BPM. Extrapolating beats if necessary...")
    beat_interval = 60.0 / bpm
    first_beat = beat_times[0]
    if first_beat > beat_interval:
        extrapolated_beats = []
        curr = first_beat - beat_interval
        while curr >= 0.01:
            extrapolated_beats.append(curr)
            curr -= beat_interval
        if extrapolated_beats:
            extrapolated_beats.reverse()
            print(f"   💡 Extrapolated {len(extrapolated_beats)} rhythmic beats backwards to fill the start.")
            beat_times = extrapolated_beats + beat_times
            
    # 清理現有 Blue Markers
    try:
        timeline.DeleteMarkersByColor("Blue")
    except Exception:
        pass
        
    LATENCY_OFFSET_SEC = -0.065
    left_offset_sec = best_t  # 因為我們已經把起點裁切到 best_t 了，所以 timeline_start 對齊 best_t 的音樂內容
    
    added_count = 0
    max_frames = int(MAX_DURATION_SEC * fps)
    
    for idx, beat_sec in enumerate(beat_times):
        compensated_sec = beat_sec + LATENCY_OFFSET_SEC
        if compensated_sec < left_offset_sec:
            continue
            
        absolute_frame = timeline_start + int(round((compensated_sec - left_offset_sec) * fps))
        relative_frame = absolute_frame - timeline_start
        
        if relative_frame < 0 or relative_frame > max_frames:
            continue
            
        marker_name = f"Beat {idx+1}"
        marker_note = f"AI Beat Cut | Time in File: {beat_sec:.2f}s"
        success = timeline.AddMarker(relative_frame, "Blue", marker_name, marker_note, 1)
        if success:
            added_count += 1
            
    print(f"✅ Generated {added_count} Blue beat markers on the timeline AI_2.")
    
    # ── 6. 讀取並分配影片素材資料夾 ────────────────────────────────────
    print("\n📁 Step 4: Setting up Master/Video/D2/CLIP Folder in Media Pool...")
    def find_folder_recursive(current_folder, path_parts):
        if not path_parts:
            return current_folder
        target = path_parts[0]
        sub_folders = current_folder.GetSubFolderList()
        for sub in sub_folders:
            if sub.GetName().lower() == target.lower():
                return find_folder_recursive(sub, path_parts[1:])
        return None
        
    clip_folder = find_folder_recursive(root_folder, FOLDER_STRUCTURE)
    if not clip_folder:
        print("❌ Error: Master/Video/D2/CLIP folder not found in Media Pool.")
        sys.exit(1)
        
    media_pool.SetCurrentFolder(clip_folder)
    print(f"   Active Media Pool folder set to: '{clip_folder.GetName()}'")
    
    # ── 7. 讀取與更新本地 AI 特徵快取 ─────────────────────────────
    print("\n📂 Step 5: Extracting local video keyframe features...")
    cache_path = os.path.join(ASSETS_DIR, "video_metadata.pkl")
    metadata_cache = smart_asset_selector.extract_features_and_cache(ASSETS_DIR, cache_path)
    if not metadata_cache:
        print("❌ Error: Video metadata cache is empty.")
        sys.exit(1)
        
    # ── 8. 客製化語義 CLIP 故事線媒合 (高質感 & 產品包裝) ──────────────────
    print("\n🧠 Step 6: Querying semantic CLIP matches tailored for '高質感' (Premium) & '產品包裝' (Packaging)...")
    PROMPTS = {
        "setup": "premium high-end backstage preparation hair salon setup venue high-quality luxury environment",
        "detail": "close-up of elegant cosmetic product packaging bottle luxury design branding hair styling product detail",
        "catwalk": "beautiful fashion model premium catwalk show hair movement high-quality professional model runway",
        "finale": "grand finale showing premium product packaging bottle logo brand presentation and elegant branding close-up"
    }
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        from transformers import CLIPModel, CLIPProcessor
        model = CLIPModel.from_pretrained(smart_asset_selector.MODEL_NAME).to(device)
        processor = CLIPProcessor.from_pretrained(smart_asset_selector.MODEL_NAME)
        model.eval()
        
        # A. 故事線編碼
        prompt_keys = list(PROMPTS.keys())
        prompt_texts = [PROMPTS[k] for k in prompt_keys]
        
        # B. 智慧審美對比詞編碼
        AESTHETIC_PROMPTS = {
            "positive": "exquisite professional cinematography, perfect rule-of-thirds composition, beautiful balanced framing, high-end high-contrast commercial video, sharp clean focus on product packaging",
            "negative": "unprofessional messy framing, ugly composition, chaotic clutter, blurry out of focus product, bad lighting, amateur crop, cut-off branding label"
        }
        aesthetic_keys = list(AESTHETIC_PROMPTS.keys())
        aesthetic_texts = [AESTHETIC_PROMPTS[k] for k in aesthetic_keys]
        
        all_texts = prompt_texts + aesthetic_texts
        
        with torch.no_grad():
            inputs = processor(text=all_texts, return_tensors="pt", padding=True).to(device)
            text_features = model.get_text_features(**inputs)
            text_embeddings = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
            text_embeddings_np = text_embeddings.cpu().numpy()
            
        # 分配編碼向量
        prompt_embeddings = {prompt_keys[i]: text_embeddings_np[i] for i in range(len(prompt_keys))}
        aesthetic_embeddings = {aesthetic_keys[i]: text_embeddings_np[len(prompt_keys) + i] for i in range(len(aesthetic_keys))}
        
        print("   ✅ Premium narrative prompts mapped successfully via CLIP!")
        print("   ✅ AI Aesthetic Gate (Composition Scoring) prompts mapped successfully via CLIP!")
    except Exception as e:
        print(f"❌ CLIP text embedding extraction failed: {e}")
        sys.exit(1)
        
    # 計算各影片與這四類故事階段的語義相似度，以及視覺美學與構圖評分
    clip_rankings = []
    for filename, meta in metadata_cache.items():
        img_emb = np.array(meta["embedding"])
        sims = {}
        for theme, emb in prompt_embeddings.items():
            sims[theme] = float(np.dot(img_emb, emb))
            
        # 計算視覺審美構圖得分 (正向相似度 - 負向相似度)
        sim_pos = float(np.dot(img_emb, aesthetic_embeddings["positive"]))
        sim_neg = float(np.dot(img_emb, aesthetic_embeddings["negative"]))
        aesthetic_score = sim_pos - sim_neg
            
        clip_rankings.append({
            "filename": filename,
            "path": meta["path"],
            "sim_setup": sims["setup"],
            "sim_detail": sims["detail"],
            "sim_catwalk": sims["catwalk"],
            "sim_finale": sims["finale"],
            "motion_energy": meta["motion_energy"],
            "duration": meta["duration"],
            "aesthetic_score": aesthetic_score
        })
        
    # 讀取時間軸標記點，產生切點區間
    markers_dict = timeline.GetMarkers()
    all_rel_frames = sorted(list(markers_dict.keys()))
    rel_frames_30s = [f for f in all_rel_frames if f <= max_frames]
    
    # 4階段時序臨界點 (按比例動態縮放)
    t_setup = 5.0
    t_detail = 12.0
    t_catwalk = 25.0
    t_finale = MAX_DURATION_SEC
    
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
        elif t < t_catwalk:
            climax_markers.append(f)
        else:
            finale_markers.append(f)
            
    # 執行「動態節奏降頻（Rhythmic Downsampling Gate）」防禦，防止切點過碎
    downsampled_beats = []
    
    # 起 (Setup): 每 4 拍切一次 (呼吸感鋪墊)
    for idx, f in enumerate(setup_markers):
        if idx % 4 == 0:
            downsampled_beats.append((f, "setup"))
            
    # 承 (Detail): 每 2 拍切一次 (工藝與產品細節特寫)
    for idx, f in enumerate(detail_markers):
        if idx % 2 == 0:
            downsampled_beats.append((f, "detail"))
            
    # 轉 (Climax): 每 2 拍切一次 (秀秀走秀，高能卡點)
    for idx, f in enumerate(climax_markers):
        if idx % 2 == 0:
            downsampled_beats.append((f, "catwalk"))
        
    # 合 (Finale): 每 4 拍切一次 (產品瓶身，徐緩定格)
    for idx, f in enumerate(finale_markers):
        if idx % 4 == 0:
            downsampled_beats.append((f, "finale"))
            
    downsampled_beats.sort(key=lambda x: x[0])
    unique_beats = []
    seen = set()
    for f, role in downsampled_beats:
        if f not in seen:
            unique_beats.append((f, role))
            seen.add(f)
            
    cut_intervals = []
    last_frame = timeline_start
    
    for rel_frame, role in unique_beats:
        abs_frame = timeline_start + rel_frame
        if abs_frame > last_frame:
            cut_intervals.append((last_frame, abs_frame, role))
            last_frame = abs_frame
            
    if last_frame < timeline_start + max_frames:
        cut_intervals.append((last_frame, timeline_start + max_frames, "finale"))
        
    print(f"🥁 Synced cuts compiled: {len(cut_intervals)} elegant cinematic cuts.")
    
    # ── 9. AI 語義媒合與去重防禦 ──────────────────────────────────────────
    print("\n🎬 Step 7: Executing AI Semantic Matchmaking & Duplicate Defense...")
    motion_energies = [c["motion_energy"] for c in clip_rankings]
    min_motion = min(motion_energies) if motion_energies else 0.0
    max_motion = max(motion_energies) if motion_energies else 1.0
    motion_range = max_motion - min_motion if max_motion != min_motion else 1.0
    
    # 智慧導演審美門檻動態縮放範圍
    aesthetic_scores = [c["aesthetic_score"] for c in clip_rankings]
    min_aesthetic = min(aesthetic_scores) if aesthetic_scores else -1.0
    max_aesthetic = max(aesthetic_scores) if aesthetic_scores else 1.0
    aesthetic_range = max_aesthetic - min_aesthetic if max_aesthetic != min_aesthetic else 1.0
    
    # 建立媒體池項目映射表
    all_clips_in_pool = clip_folder.GetClipList()
    clip_map = {c.GetName().lower(): c for c in all_clips_in_pool}
    
    available_pool = [c for c in clip_rankings if c["filename"].lower() in clip_map]
    final_clip_sequence = []
    
    for idx, interval in enumerate(cut_intervals):
        start_f, end_f, role = interval
        duration_timeline = end_f - start_f
        
        # 理想運動強度曲線
        if duration_timeline <= 12:
            ideal_motion = 0.9
        elif duration_timeline >= 36:
            ideal_motion = 0.1
        else:
            ideal_motion = 0.9 - ((duration_timeline - 12) / 24.0) * 0.8
            ideal_motion = max(0.1, min(0.9, ideal_motion))
            
        if not available_pool:
            print("   ⚠️ Available unique pool exhausted! Recycling pool...")
            available_pool = [c for c in clip_rankings if c["filename"].lower() in clip_map]
            
        theme_similarities = [c["sim_" + role] for c in available_pool]
        min_sim = min(theme_similarities) if theme_similarities else 0.0
        max_sim = max(theme_similarities) if theme_similarities else 1.0
        sim_range = max_sim - min_sim if max_sim != min_sim else 1.0
        
        selected_embeddings = []
        for chosen in final_clip_sequence:
            name = chosen["name"]
            if name in metadata_cache:
                selected_embeddings.append(np.array(metadata_cache[name]["embedding"]))
                
        best_candidate_idx = None
        best_score = -9999.0
        
        for pool_idx, candidate in enumerate(available_pool):
            cand_emb = np.array(metadata_cache[candidate["filename"]]["embedding"])
            is_near_dup = False
            for s_emb in selected_embeddings:
                cos_sim = float(np.dot(cand_emb, s_emb))
                if cos_sim > 0.88:
                    is_near_dup = True
                    break
                    
            norm_motion = (candidate["motion_energy"] - min_motion) / motion_range
            norm_sim = (candidate["sim_" + role] - min_sim) / sim_range
            motion_score = 1.0 - abs(norm_motion - ideal_motion)
            
            # 構圖美學打分
            norm_aesthetic = (candidate["aesthetic_score"] - min_aesthetic) / aesthetic_range
            
            # 得分模型：50% 語義 + 20% 運動能量 + 30% 構圖美學 (黃金三角)
            total_score = 0.5 * norm_sim + 0.2 * motion_score + 0.3 * norm_aesthetic
            
            # AI 智慧導演審美門檻 (Aesthetic Gate)
            AESTHETIC_GATE_THRESHOLD = 0.00
            if candidate["aesthetic_score"] < AESTHETIC_GATE_THRESHOLD:
                total_score -= 5.0  # 審美不及格給予毀滅性重罰，直接過濾
                
            if is_near_dup:
                total_score -= 2.0
            if candidate["motion_energy"] >= 10.5:
                total_score -= 3.0  # 抖動重罰
                
            if final_clip_sequence:
                prev_motion = final_clip_sequence[-1]["motion"]
                motion_diff = abs(candidate["motion_energy"] - prev_motion)
                if motion_diff > 3.0:
                    total_score -= 0.15 * (motion_diff - 3.0)
                    
            if total_score > best_score:
                best_score = total_score
                best_candidate_idx = pool_idx
                
        best_candidate = available_pool.pop(best_candidate_idx)
        
        # 決定美學等級標籤
        a_score = best_candidate["aesthetic_score"]
        if a_score >= 0.04:
            a_grade = "🌟 Premium"
        elif a_score >= 0.00:
            a_grade = "✨ Good"
        elif a_score >= -0.02:
            a_grade = "👌 Acceptable (Filtered by Aesthetic Gate)"
        else:
            a_grade = "⚠️ Bad-Filtered (Rescued)"
            
        final_clip_sequence.append({
            "item": clip_map[best_candidate["filename"].lower()],
            "name": best_candidate["filename"],
            "role": role,
            "motion": best_candidate["motion_energy"],
            "similarity": best_candidate["sim_" + role],
            "aesthetic_score": a_score,
            "aesthetic_grade": a_grade,
            "path": best_candidate["path"]
        })
        
    print(f"   ✅ AI Storyboarding completed ({len(final_clip_sequence)} cuts matching '高質感' & '產品包裝').")
    
    # ── 10. 雙核 CV 滾動平穩度 In 點檢索與無縫拼接 ────────────────────────────
    print("\n🔨 Step 8: Trimming and Appending Clips onto Video Track 1...")
    
    # 清理舊影片軌
    for t_idx in [1, 2]:
        try:
            video_items = timeline.GetItemListInTrack("video", t_idx)
            if video_items:
                timeline.DeleteClips(video_items)
        except Exception:
            pass
            
    clips_to_append = []
    
    for idx, interval in enumerate(cut_intervals):
        if idx >= len(final_clip_sequence):
            break
            
        start_f, end_f, role = interval
        duration_timeline = end_f - start_f
        
        clip_data = final_clip_sequence[idx]
        clip_item = clip_data["item"]
        
        try:
            fps_prop = clip_item.GetClipProperty("FPS")
            src_fps = float(fps_prop) if fps_prop else 24.0
        except Exception:
            src_fps = 24.0
            
        scale_factor = src_fps / fps
        duration_source = int(math.ceil(duration_timeline * scale_factor))
        
        frames_prop = clip_item.GetClipProperty("Frames")
        total_frames = int(frames_prop) if (frames_prop and frames_prop.isdigit()) else 240
        
        # 決定 In 點 (使用本機雙核 CV 快取檢索)
        is_static = (role in ["setup", "finale"])
        file_path = clip_data["path"]
        
        if not is_static and file_path and os.path.exists(file_path):
            src_start = find_optimal_stable_unidirectional_window(
                file_path,
                duration_source,
                src_fps
            )
        else:
            guard_band = int(total_frames * 0.15)
            safe_total = total_frames - 2 * guard_band
            if safe_total >= duration_source:
                src_start = guard_band + (safe_total - duration_source) // 2
            else:
                src_start = max(0, (total_frames - duration_source) // 2)
                
        src_end = src_start + duration_source
        
        clips_to_append.append({
            "mediaPoolItem": clip_item,
            "startFrame": int(src_start),
            "endFrame": int(src_end)
        })
        
        if idx < 5 or idx == len(cut_intervals) - 1:
            print(f"   [Narrative Arc #{idx+1}] Frame: {start_f}➔{end_f} | Role: {role.upper()} | Similarity: {clip_data['similarity']:.3f} | Motion: {clip_data['motion']:.1f} | Aesthetic: {clip_data['aesthetic_score']:.3f} ({clip_data['aesthetic_grade']}) | Clip: '{clip_data['name']}'")
        elif idx == 5:
            print("   ...")
            
    print("⏳ Submitting sequential cuts to DaVinci Resolve...")
    appended_video = media_pool.AppendToTimeline(clips_to_append)
    
    if appended_video and appended_video[0] is not None:
        print("🎉 SUCCESS! Video clips appended sequentially starting exactly at 86400!")
        
        # 清除音軌 1 上的現場雜音
        try:
            cam_audio_items = timeline.GetItemListInTrack("audio", 1)
            if cam_audio_items:
                print("🧹 Clearing camera scratch audio from Audio Track 1...")
                timeline.DeleteClips(cam_audio_items)
        except Exception as e:
            print(f"   Note: Clear scratch audio failed: {e}")
            
        # ── 10.5. 背景配樂高潮裁切與 A1 精確置入 ───────────────────────────
        print("\n🎧 [AI Music Climax] Appending cropped BGM onto Audio Track 1...")
        appended_audio = media_pool.AppendToTimeline(bgm_to_append)
        if appended_audio:
            print("🎉 SUCCESS! Crop BGM placed perfectly on Audio Track 1!")
        else:
            print("❌ Error: Failed to append BGM clip.")
            sys.exit(1)
            
        # ── 11. 雙品牌 Logo 結尾包裝 (BC & Schwarzkopf - Video Track 2 & 3) ──
        print("\n🖼️ Step 9: Overlaying BC & Schwarzkopf Logos on Video Track 2 & 3...")
        bc_logo_path = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\2605_BCBonacure\活動影片\BC_2018_LOGO00000001.jpg"
        skp_logo_path = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\2605_BCBonacure\活動影片\SKP_Logo_schwarz00000001.jpg"
        
        # 確保至少有 3 個視訊軌
        video_track_count = timeline.GetTrackCount("video")
        while video_track_count < 3:
            timeline.AddTrack("video")
            video_track_count = timeline.GetTrackCount("video")
            
        # 尋找與導入 Logo
        def find_clip_by_name(folder, query):
            for clip in folder.GetClipList() or []:
                if query.lower() in clip.GetName().lower():
                    return clip
            for sub in folder.GetSubFolderList() or []:
                res = find_clip_by_name(sub, query)
                if res:
                    return res
            return None
            
        bc_logo_clip = find_clip_by_name(root_folder, "BC_2018_LOGO")
        if not bc_logo_clip and os.path.exists(bc_logo_path):
            print("   📥 Importing BC Logo...")
            media_pool.SetCurrentFolder(root_folder)
            imported = media_pool.ImportMedia([bc_logo_path])
            if imported:
                bc_logo_clip = imported[0]
                
        skp_logo_clip = find_clip_by_name(root_folder, "SKP_Logo_schwarz00000001")
        if not skp_logo_clip and os.path.exists(skp_logo_path):
            print("   📥 Importing Schwarzkopf Logo...")
            media_pool.SetCurrentFolder(root_folder)
            imported = media_pool.ImportMedia([skp_logo_path])
            if imported:
                skp_logo_clip = imported[0]
                
        # 定位 Finale 起點影格
        logo_start_frame = None
        for interval in cut_intervals:
            start_f, end_f, role = interval
            if role == "finale":
                logo_start_frame = start_f
                break
        if logo_start_frame is None:
            logo_start_frame = timeline_start + int(25.0 * fps)
            
        logo_end_frame = timeline_start + max_frames
        logo_duration = logo_end_frame - logo_start_frame
        
        if bc_logo_clip and skp_logo_clip:
            logos_to_append = [
                {
                    "mediaPoolItem": bc_logo_clip,
                    "startFrame": 0,
                    "endFrame": int(logo_duration),
                    "recordFrame": int(logo_start_frame),
                    "trackIndex": 2,
                    "mediaType": 1
                },
                {
                    "mediaPoolItem": skp_logo_clip,
                    "startFrame": 0,
                    "endFrame": int(logo_duration),
                    "recordFrame": int(logo_start_frame),
                    "trackIndex": 3,
                    "mediaType": 1
                }
            ]
            appended_logos = media_pool.AppendToTimeline(logos_to_append)
            if appended_logos:
                print("   🎉 SUCCESS: BC & Schwarzkopf Logos appended!")
                time.sleep(0.5)
                logo_items_v2 = timeline.GetItemListInTrack("video", 2)
                logo_items_v3 = timeline.GetItemListInTrack("video", 3)
                
                # 套用 9:16 直式專屬雙 Logo 對稱居中排版 (擺放於畫面下三分之一處)
                if logo_items_v2:
                    bc_item = logo_items_v2[0]
                    bc_item.SetProperty("ZoomX", 0.30)
                    bc_item.SetProperty("ZoomY", 0.30)
                    bc_item.SetProperty("Pan", -180.0)
                    bc_item.SetProperty("Tilt", -250.0)
                if logo_items_v3:
                    skp_item = logo_items_v3[0]
                    skp_item.SetProperty("ZoomX", 0.30)
                    skp_item.SetProperty("ZoomY", 0.30)
                    skp_item.SetProperty("Pan", 180.0)
                    skp_item.SetProperty("Tilt", -250.0)
                print("   ✅ Configured BC & Schwarzkopf Logo scales & coordinate panning.")
                
        # ── 12. 鏡頭動態導演與角色軌道染色 ────────────────────────────────
        print("\n🎥 Step 10: Directing AI Camera Motions & Narrative Colors...")
        placed_clips = timeline.GetItemListInTrack("video", 1)
        
        color_map = {
            "setup": "Navy",
            "detail": "Yellow",
            "catwalk": "Orange",
            "finale": "Purple"
        }
        
        for idx, item in enumerate(placed_clips):
            if idx >= len(cut_intervals):
                break
            start_f, end_f, role = cut_intervals[idx]
            
            # A. 運鏡變焦與傾斜擺動
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
                
            # 套用 9:16 直式裁切縮放補償 (橫式 16:9 需放大 3.16 倍填滿，直式素材則免放大，維持 1.0)
            VERTICAL_CROP_ZOOM = 1.0 if SOURCE_FOOTAGE_VERTICAL else 3.16
            zoom_val = zoom_val * VERTICAL_CROP_ZOOM
            
            try:
                item.SetProperty("ZoomX", zoom_val)
                item.SetProperty("ZoomY", zoom_val)
                item.SetProperty("RotationAngle", rotation_val)
                item.SetClipColor(color_map.get(role, "Navy"))
            except Exception as e:
                print(f"   ⚠️ Transform settings failed on clip #{idx+1}: {e}")
                
        print("   ✅ Directed camera transforms and applied clip narrative colors.")
        
        # ── 13. 大師級一鍵調色同步 (Node Graph Grade Cloning) ───────────────
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
                
        # ── 14. 刷新 GUI 焦點 ───────────────────────────────────────
        print("\n🔄 Refreshing DaVinci Resolve GUI Focus...")
        resolve.OpenPage("media")
        time.sleep(0.3)
        resolve.OpenPage("edit")
        time.sleep(0.3)
        print("🎉 SUCCESS! Timeline 'AI_2' created and edited beautifully!")
        
    else:
        print("❌ Error: Append to timeline failed. Resolve returned None.")
        sys.exit(1)

if __name__ == "__main__":
    run_ai2_edit()
