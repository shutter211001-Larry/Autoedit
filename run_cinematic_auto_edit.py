import sys
import os
import time
import math
import pickle
import torch

# ── 確保輸出編碼支援 UTF-8 ──────────────────────────────────────
if sys.stdout.encoding != 'utf-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except Exception:
        pass

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
    print("❌ DaVinci Resolve is not running. Please open your project first.")
    sys.exit(1)

# 引入本機 AI 特徵檢索模組
try:
    import smart_asset_selector
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import smart_asset_selector

# ── 核心設定 ──────────────────────────────────────────────────
ASSETS_DIR = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video\D2\PRIVATE\M4ROOT\CLIP"
FOLDER_STRUCTURE = ["Video", "D2", "CLIP"]

# 🚀 商業廣告模板配置 (30秒卡點商業廣告)
MAX_DURATION_SEC = 30.0  # 限制影片長度為 30 秒

# 🚀 4階段電影感敘事提示詞 (起、承、轉、合 - Chronological Narrative Storyboarding)
# 藉由時間軸位置動態切換提示詞，使影片具備故事發展邏輯，不再是隨機拼湊的畫面！
PROMPTS = {
    "setup": "event backstage preparation hair salon setup venue establishing audience gathering", # 1. 起 (開場準備/現場環境)
    "detail": "hair styling process stylist working with hairspray cosmetic product closeups detail", # 2. 承 (產品使用/造型細節)
    "catwalk": "beautiful fashion model catwalk show runway hair spin movement closeup",            # 3. 轉 (大秀高潮/走秀旋轉)
    "finale": "audience clapping reaction applause grand finale show product branding packaging logo" # 4. 合 (結尾鼓掌/產品定格)
}

def run_cinematic_workflow():
    print("🚀 Starting AI Content-Aware 30s Commercial Editor (Chronological Narrative Arc)...")
    
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
    
    # ── 2. 讀取與更新本地 AI 特徵快取 ─────────────────────────────
    print("\n📂 Step 2: Extracting local video keyframe features...")
    cache_path = os.path.join(ASSETS_DIR, "video_metadata.pkl")
    metadata_cache = smart_asset_selector.extract_features_and_cache(ASSETS_DIR, cache_path)
    if not metadata_cache:
        print("❌ Error: Video metadata cache is empty.")
        sys.exit(1)
        
    # ── 3. 本地 AI 提取「起、承、轉、合」敘事提示詞的特徵向量 ─────────────────
    print("\n🧠 Step 3: Extracting CLIP text embeddings for Narrative Arc phases...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        from transformers import CLIPModel, CLIPProcessor
        model = CLIPModel.from_pretrained(smart_asset_selector.MODEL_NAME).to(device)
        processor = CLIPProcessor.from_pretrained(smart_asset_selector.MODEL_NAME)
        model.eval()
        
        prompt_keys = list(PROMPTS.keys())
        prompt_texts = [PROMPTS[k] for k in prompt_keys]
        
        with torch.no_grad():
            inputs = processor(text=prompt_texts, return_tensors="pt", padding=True).to(device)
            text_features = model.get_text_features(**inputs)
            # L2 歸一化
            text_embeddings = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
            text_embeddings_np = text_embeddings.cpu().numpy()
            
        prompt_embeddings = {prompt_keys[i]: text_embeddings_np[i] for i in range(len(prompt_keys))}
        print("✅ Narrative Prompts mapped successfully.")
    except Exception as e:
        print(f"❌ CLIP text embedding extraction failed: {e}")
        sys.exit(1)
        
    # 計算各影片與這四類故事階段的語義相似度
    clip_rankings = []
    for filename, meta in metadata_cache.items():
        img_emb = np.array(meta["embedding"])
        sims = {}
        for theme, emb in prompt_embeddings.items():
            sims[theme] = float(np.dot(img_emb, emb))
            
        clip_rankings.append({
            "filename": filename,
            "path": meta["path"],
            "sim_setup": sims["setup"],
            "sim_detail": sims["detail"],
            "sim_catwalk": sims["catwalk"],
            "sim_finale": sims["finale"],
            "motion_energy": meta["motion_energy"],
            "duration": meta["duration"]
        })
        
    # ── 4. 讀取時間軸節拍標記 (Markers) 並應用 30 秒限制 ────────────────
    print("\n🎵 Step 4: Loading beat markers and applying 30s commercial limit...")
    markers = timeline.GetMarkers()
    if not markers:
        print("❌ Error: No beat markers found on timeline. Please run auto_beat_marker.py first.")
        sys.exit(1)
        
    timeline_start = timeline.GetStartFrame()
    fps = float(current_project.GetSetting("timelineFrameRate") or 24.0)
    max_frames = int(MAX_DURATION_SEC * fps)
    
    # 僅篩選出前 30 秒內的節拍點
    beat_frames = sorted([timeline_start + f for f in markers.keys()])
    beat_frames = [f for f in beat_frames if (f - timeline_start) <= max_frames]
    
    print(f"   Found {len(beat_frames)} beat markers within the first {MAX_DURATION_SEC} seconds.")
    
    # 獲取背景音樂片段在時間軸上的起點
    audio_items = timeline.GetItemListInTrack("audio", 1)
    audio_start_frame = timeline_start
    if audio_items:
        audio_start_frame = audio_items[0].GetStart()
        
    # 計算剪接區間
    cut_intervals = []
    last_frame = audio_start_frame
    
    for beat in beat_frames:
        if beat > last_frame:
            cut_intervals.append((last_frame, beat))
            last_frame = beat
            
    print(f"   Generated {len(cut_intervals)} precise cut intervals for the 30s commercial.")
    
    # ── 5. 4階段故事線與近重複防禦 AI 媒合 (Narrative Matchmaker) ─────────────
    print("\n🎬 Step 5: Structuring Chronological Narrative & Duplicate Defense...")
    
    # 歸一化運動能量做匹配 [0.0, 1.0]
    motion_energies = [c["motion_energy"] for c in clip_rankings]
    min_motion = min(motion_energies) if motion_energies else 0.0
    max_motion = max(motion_energies) if motion_energies else 1.0
    motion_range = max_motion - min_motion if max_motion != min_motion else 1.0
    
    # A. 預先計算並套用 5-beat 滑動平均濾波，平滑「理想運動能量曲線（Motion Continuity Envelope）」
    # 這能強制相鄰卡點的鏡頭動態緩慢過渡，防止畫面在極快與極慢之間產生鋸齒狀跳變 (視覺衝突)
    raw_ideal_motions = []
    for interval in cut_intervals:
        start_frame, end_frame = interval
        duration_timeline = end_frame - start_frame
        if duration_timeline <= 12:
            ideal = 0.9  # 高動態
        elif duration_timeline >= 36:
            ideal = 0.1  # 靜態美感
        else:
            ideal = 0.9 - ((duration_timeline - 12) / 24.0) * 0.8
            ideal = max(0.1, min(0.9, ideal))
        raw_ideal_motions.append(ideal)
        
    smoothed_ideal_motions = []
    window_size = 5
    half = window_size // 2
    n_cuts = len(raw_ideal_motions)
    for i in range(n_cuts):
        start_w = max(0, i - half)
        end_w = min(n_cuts, i + half + 1)
        smoothed_ideal_motions.append(sum(raw_ideal_motions[start_w:end_w]) / (end_w - start_w))
        
    # 建立媒體池項目映射表
    all_clips = clip_folder.GetClipList()
    clip_map = {c.GetName().lower(): c for c in all_clips}
    
    # 建立可用的影片素材庫
    available_pool = [c for c in clip_rankings if c["filename"].lower() in clip_map]
    print(f"   🎬 Total available unique clips in Media Pool: {len(available_pool)}")
    
    final_clip_sequence = []
    
    for idx, interval in enumerate(cut_intervals):
        start_frame, end_frame = interval
        duration_timeline = end_frame - start_frame
        
        # 計算當前卡點相對於時間軸起點的時間 (秒數)
        elapsed_sec = (start_frame - timeline_start) / fps
        
        # 🚀 電影感 4階段敘事時間配給規則 (起、承、轉、合)：
        # - 0s 到 5s  (起): "setup" (後台準備、現場環境)
        # - 5s 到 12s (承): "detail" (產品使用、吹整美髮造型過程)
        # - 12s 到 25s(轉): "catwalk" (大秀走走、秀髮旋轉高潮)
        # - 25s 到 30s(合): "finale" (結尾定格、現場熱烈鼓掌)
        if elapsed_sec < 5.0:
            role = "setup"
        elif elapsed_sec < 12.0:
            role = "detail"
        elif elapsed_sec < 25.0:
            role = "catwalk"
        else:
            role = "finale"
            
        # 🚀 使用平滑後的運動包絡線，確保動態過渡絲滑不衝突
        ideal_motion = smoothed_ideal_motions[idx]
            
        if not available_pool:
            print("   ⚠️ Warning: Available unique pool exhausted! Recycling pool...")
            available_pool = [c for c in clip_rankings if c["filename"].lower() in clip_map]
            
        # 🚀 對「當前故事階段角色」的相似度在剩餘 pool 中進行 [0.0, 1.0] 的重新歸一化
        theme_similarities = [c["sim_" + role] for c in available_pool]
        min_sim = min(theme_similarities) if theme_similarities else 0.0
        max_sim = max(theme_similarities) if theme_similarities else 1.0
        sim_range = max_sim - min_sim if max_sim != min_sim else 1.0
        
        # 獲取當前已選所有片段的特徵向量 (用於近重複防禦)
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
                if cos_sim > 0.88:  # 視覺相似度大於 88%
                    is_near_dup = True
                    break
                    
            norm_motion = (candidate["motion_energy"] - min_motion) / motion_range
            norm_sim = (candidate["sim_" + role] - min_sim) / sim_range
            motion_score = 1.0 - abs(norm_motion - ideal_motion)
            
            # 得分模型：70% 語義相似度歸一 + 30% 運動強度相符度
            total_score = 0.7 * norm_sim + 0.3 * motion_score
            
            # 近重複大扣分防禦
            if is_near_dup:
                total_score -= 2.0
                
            # 🚀 防震動與大晃動對焦廢片防禦 (Shaky Shot Defense)
            # 實測運動能量 >= 10.5 多為相機重置、手抖或對焦失敗的廢片，重罰 3.0 分以強迫選用穩定絲滑的 Good Takes！
            if candidate["motion_energy"] >= 10.5:
                total_score -= 3.0
                
            # 🚀 電影感前後幀「動態留線銜接防禦」 (Motion Continuity Penalty)
            # 如果目前候選片段的運動能量，與上一鏡片有劇烈物理跳變 (差距 > 3.0)，則給予漸進扣分
            # 這能強制畫面動態維持「視覺慣性流暢感 (Visual Inertia Flow)」，防止快慢動作瞬間衝突！
            if final_clip_sequence:
                prev_motion = final_clip_sequence[-1]["motion"]
                motion_diff = abs(candidate["motion_energy"] - prev_motion)
                if motion_diff > 3.0:
                    total_score -= 0.15 * (motion_diff - 3.0)
                
            if total_score > best_score:
                best_score = total_score
                best_candidate_idx = pool_idx
                
        # 彈出選中的唯一影片
        best_candidate = available_pool.pop(best_candidate_idx)
        
        final_clip_sequence.append({
            "item": clip_map[best_candidate["filename"].lower()],
            "name": best_candidate["filename"],
            "role": role,
            "similarity": best_candidate["sim_" + role],
            "motion": best_candidate["motion_energy"]
        })
        
    print(f"   ✅ Chronological Storyboard compiled successfully. Assigned 4-phase roles to all cuts.")
    
    # ── 6. 清理舊影片並自動剪接至時間軸 ───────────────────────────
    print("\n🔨 Step 6: Assembling Video Clips onto DaVinci Timeline (Video Track 1)...")
    
    for t_idx in [1, 2]:
        try:
            video_items = timeline.GetItemListInTrack("video", t_idx)
            if video_items:
                print(f"   Cleaning {len(video_items)} old clips on Video Track {t_idx}...")
                timeline.DeleteClips(video_items)
        except Exception as e:
            print(f"   Clear video track {t_idx} failed: {e}")
            
    clips_to_append = []
    
    for idx, interval in enumerate(cut_intervals):
        if idx >= len(final_clip_sequence):
            break
            
        start_timecode_frame, end_timecode_frame = interval
        duration_timeline = end_timecode_frame - start_timecode_frame
        
        clip_data = final_clip_sequence[idx]
        clip_item = clip_data["item"]
        
        try:
            fps_prop = clip_item.GetClipProperty("FPS")
            src_fps = float(fps_prop) if fps_prop else 24.0
        except Exception:
            src_fps = 24.0
            
        scale_factor = src_fps / 24.0
        duration_source = int(math.ceil(duration_timeline * scale_factor))
        
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
            print(f"   [Narrative Arc #{idx+1}] Elapsed: {(start_timecode_frame - timeline_start)/24.0:.2f}s | Phase: {clip_data['role'].upper()} | Similarity: {clip_data['similarity']:.3f} | Motion: {clip_data['motion']:.1f} | Clip: '{clip_data['name']}'")
        elif idx == 5:
            print("   ...")
            
    print("⏳ Sending targeted perfect append commands to Resolve API...")
    appended = media_pool.AppendToTimeline(clips_to_append)
    
    if appended:
        print(f"🎉 SUCCESS! Placed {len(appended)} narrative clips flawlessly onto Video Track 1!")
        
        # 🚀 ── 7. 啟動 AI 鏡頭動態導演 (AI Camera Motion Director) ────────────────
        print("\n🎥 Step 7: AI Camera Motion Director active. Directing clip scales & rotations...")
        placed_video_items = timeline.GetItemListInTrack("video", 1)
        
        for idx, item in enumerate(placed_video_items):
            if idx >= len(final_clip_sequence):
                break
                
            clip_data = final_clip_sequence[idx]
            role = clip_data["role"]
            
            zoom_val = 1.0
            rotation_val = 0.0
            
            # 🚀 電影感 4 階段鏡頭設計法則 (大幅增加數值以展現極致視覺張力)：
            # - 起 (SETUP - 0s 到 5s): 鏡頭完全穩定乾淨
            if role == "setup":
                zoom_val = 1.0
                rotation_val = 0.0
            # - 承 (DETAIL - 5s 到 12s): 產品與吹風造型大幅推近 (1.10x)，創造極具魄力的產品特寫
            elif role == "detail":
                zoom_val = 1.10
                rotation_val = 0.0
            # - 轉 (CATWALK - 12s 到 25s): 大秀高潮走秀！交替進行 4.0 與 -4.0 度的強烈斜切 (Slash Cut)，配合 1.15x 縮放 (完全掩蓋黑邊)，營造極其炫酷的手持震動擺感！
            elif role == "catwalk":
                zoom_val = 1.15
                rotation_val = 4.0 if (idx % 2 == 0) else -4.0
            # - 合 (FINALE - 25s 到 30s): 結尾品牌定格強烈大推近 (1.20x)，將視覺重心完全聚焦在產品與商標！
            elif role == "finale":
                zoom_val = 1.20
                rotation_val = 0.0
                
            try:
                item.SetProperty("ZoomX", zoom_val)
                item.SetProperty("ZoomY", zoom_val)
                item.SetProperty("RotationAngle", rotation_val)
            except Exception as e:
                print(f"   ⚠️ Warning: Set camera motion for clip #{idx+1} failed: {e}")
                
        print("✅ AI Camera Motion Director finished directing all clips successfully!")
        
        # 🚀 ── 8. 啟動 AI 色彩風格大師 (AI Color Grade Sync) ─────────────────────
        print("\n🎨 Step 8: AI Color Grade Sync active. Coloring timeline and cloning grades...")
        
        # A. 根據起承轉合 4 階段對時間軸片段進行染色標記
        for idx, item in enumerate(placed_video_items):
            if idx >= len(final_clip_sequence):
                break
                
            clip_data = final_clip_sequence[idx]
            role = clip_data["role"]
            
            # 染色映射表
            color_map = {
                "setup": "Navy",      # 起 -> 藍色 (沉穩環境)
                "detail": "Yellow",   # 承 -> 黃色 (產品工藝)
                "catwalk": "Orange",  # 轉 -> 橙色 (高能秀秀)
                "finale": "Purple"    # 合 -> 紫色 (品牌定格)
            }
            
            target_color = color_map.get(role, "Navy")
            try:
                item.SetClipColor(target_color)
            except Exception as e:
                print(f"   ⚠️ Warning: Set clip color for clip #{idx+1} failed: {e}")
                
        print("   ✅ Timeline clip coloring applied successfully!")
        
        # B. 自動將第一鏡 (Clip #1) 的調色節點 (Grade Graph) 複製克隆給所有其餘 60 個鏡頭！
        # 這保證了全片色調 100% 大一統，完美免去逐個複製貼上調色的痛苦！
        if len(placed_video_items) > 1:
            try:
                source_clip = placed_video_items[0]
                target_clips = list(placed_video_items[1:])
                success_copy = source_clip.CopyGrades(target_clips)
                if success_copy:
                    print("   👑 SUCCESS: Automatically cloned the premium Color Grade from Clip #1 to all 60 target clips!")
                else:
                    print("   ⚠️ Warning: Copy grades returned False.")
            except Exception as e:
                print(f"   ⚠️ Warning: Auto color grade clone failed: {e}")
                
        # 雙重頁面跳轉刷新 GUI
        print("🔄 Refreshing Resolve GUI Timeline focus...")
        resolve.OpenPage("media")
        time.sleep(0.3)
        resolve.OpenPage("edit")
        time.sleep(0.3)
        print("🎬 All Done! Open your DaVinci Resolve Timeline to play your narrative synced Commercial MV!")
    else:
        print("❌ Error: Append to timeline failed. Resolve returned None.")
        
if __name__ == "__main__":
    import numpy as np
    run_cinematic_workflow()
