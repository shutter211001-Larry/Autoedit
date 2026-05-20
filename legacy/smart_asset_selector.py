import os
import sys
import pickle
import cv2
import numpy as np
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

# 確保輸出支援 UTF-8 以防亂碼
if sys.stdout.encoding != 'utf-8':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except Exception:
        pass

# ── 1. 模型與硬體設定 ────────────────────────────────────────
MODEL_NAME = "openai/clip-vit-base-patch32"
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"🖥️ AI Hardware Target: {device.upper()}")

# ── 2. 特徵提取與快取核心 ──────────────────────────────────────
def extract_features_and_cache(video_dir, cache_path=None):
    """
    掃描影片目錄中的所有影片，使用 CLIP 提取語義特徵並使用 OpenCV 計算動態能量，
    最後將其序列化儲存至快取檔案中（支援增量掃描）。
    """
    if cache_path is None:
        cache_path = os.path.join(video_dir, "video_metadata.pkl")
        
    print(f"📂 Scanning video assets in: {video_dir}")
    video_files = [
        os.path.join(video_dir, f)
        for f in os.listdir(video_dir)
        if f.lower().endswith((".mp4", ".mov"))
    ]
    
    if not video_files:
        print("❌ Error: No video files found in the directory.")
        return {}
        
    # 讀取現有的快取檔案以進行增量更新
    metadata_cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                metadata_cache = pickle.load(f)
            print(f"📦 Loaded existing cache with {len(metadata_cache)} files.")
        except Exception as e:
            print(f"⚠️ Warning: Could not load cache file ({e}). Starting fresh.")
            
    # 篩選出需要新掃描的檔案
    new_files = [f for f in video_files if os.path.basename(f) not in metadata_cache]
    
    if not new_files:
        print("✅ Cache is completely up to date. No new video files to analyze.")
        return metadata_cache
        
    print(f"🎬 Found {len(new_files)} new video files to analyze.")
    
    # ── 3. 載入本地 CLIP 模型 ────────────────────────────────────
    print("⏳ Loading local CLIP Model (openai/clip-vit-base-patch32)...")
    try:
        model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
        processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        model.eval()
        print("🚀 CLIP Model successfully loaded on local device!")
    except Exception as e:
        print(f"❌ Error loading CLIP Model: {e}")
        print("Please check your internet connection and HuggingFace accessibility.")
        sys.exit(1)
        
    # ── 4. 逐個提取影片特徵 ──────────────────────────────────────
    print("\n🔍 Extracting visual semantics & motion energy...")
    
    for idx, path in enumerate(new_files):
        filename = os.path.basename(path)
        print(f"   [{idx+1}/{len(new_files)}] Analyzing: '{filename}' ...")
        
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            print(f"   ⚠️ Warning: Cannot open '{filename}', skipping...")
            continue
            
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 29.97)
        duration = total_frames / fps
        
        if total_frames <= 0:
            cap.release()
            continue
            
        # A. 提取 3 張關鍵影格 (在影片長度的 20%, 50%, 80% 處)
        keyframe_indices = [int(total_frames * 0.2), int(total_frames * 0.5), int(total_frames * 0.8)]
        images = []
        
        for frame_idx in keyframe_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                # 轉成 RGB 並轉換為 PIL Image 用於 CLIP
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                images.append(Image.fromarray(rgb))
                
        # B. 計算物理運動能量 (Optical Flow Proxy: 影片中段連續 10 幀的平均像素變化量)
        middle_frame = int(total_frames * 0.5)
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        ret, prev_frame = cap.read()
        motion_values = []
        
        if ret:
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            # 讀取接下來的 10 幀進行光流差值
            for _ in range(10):
                ret, frame = cap.read()
                if not ret:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # 像素絕對差值
                diff = cv2.absdiff(gray, prev_gray)
                motion_values.append(np.mean(diff))
                prev_gray = gray
                
        # 計算平均運動振幅作為運動能量
        motion_energy = float(np.mean(motion_values)) if motion_values else 0.0
        cap.release()
        
        # C. 使用 CLIP 提取圖像特徵向量 (Image Embeddings)
        if not images:
            print(f"   ⚠️ Warning: No keyframes could be extracted from '{filename}'.")
            continue
            
        try:
            with torch.no_grad():
                # 處理圖片並通過模型
                inputs = processor(images=images, return_tensors="pt").to(device)
                image_features = model.get_image_features(**inputs)
                # 對 3 張關鍵影格的特徵求平均值，以獲得該片段最健壯的語義代表
                mean_embedding = image_features.mean(dim=0)
                # L2 歸一化
                mean_embedding = mean_embedding / mean_embedding.norm(p=2, dim=-1, keepdim=True)
                mean_embedding_list = mean_embedding.cpu().numpy().tolist()
        except Exception as e:
            print(f"   ❌ Torch CLIP inference failed: {e}")
            continue
            
        # 寫入快取結構中
        metadata_cache[filename] = {
            "filename": filename,
            "path": path,
            "embedding": mean_embedding_list,
            "motion_energy": motion_energy,
            "fps": fps,
            "frames": total_frames,
            "duration": duration
        }
        
    # ── 5. 序列化儲存快取 ────────────────────────────────────────
    try:
        with open(cache_path, "wb") as f:
            pickle.dump(metadata_cache, f)
        print(f"\n💾 SUCCESSFULLY CACHED! {len(metadata_cache)} files written to '{cache_path}'")
    except Exception as e:
        print(f"❌ Error writing cache file: {e}")
        
    return metadata_cache

# ── 6. 語義匹配檢索 API ────────────────────────────────────────
def query_semantic_recommendations(prompt, metadata_cache):
    """
    輸入使用者給予的創作方向 Prompt，
    計算與快取中所有影片的 CLIP 相似度，返回排序列表。
    """
    if not metadata_cache:
        return []
        
    print(f"\n🔮 Matching creative prompt: '{prompt}' against video archive...")
    
    # 載入模型以計算文字特徵向量
    try:
        model = CLIPModel.from_pretrained(MODEL_NAME).to(device)
        processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        model.eval()
    except Exception as e:
        print(f"❌ Cannot load CLIP for query: {e}")
        return []
        
    # 計算 Prompt Text Embedding
    try:
        with torch.no_grad():
            inputs = processor(text=[prompt], return_tensors="pt", padding=True).to(device)
            text_features = model.get_text_features(**inputs)
            # L2 歸一化
            text_embedding = text_features[0] / text_features[0].norm(p=2, dim=-1, keepdim=True)
            text_embedding_np = text_embedding.cpu().numpy()
    except Exception as e:
        print(f"❌ Text embedding extraction failed: {e}")
        return []
        
    # 計算相似度得分
    rankings = []
    for filename, meta in metadata_cache.items():
        img_emb = np.array(meta["embedding"])
        # 餘弦相似度 (Cosine Similarity)
        similarity = float(np.dot(img_emb, text_embedding_np))
        rankings.append({
            "filename": filename,
            "path": meta["path"],
            "similarity": similarity,
            "motion_energy": meta["motion_energy"],
            "duration": meta["duration"],
            "frames": meta["frames"],
            "fps": meta["fps"]
        })
        
    # 依照相似度高低排序
    rankings.sort(key=lambda x: x["similarity"], reverse=True)
    
    print("🏆 Top 5 AI Visual Recommendation Matches:")
    for idx, r in enumerate(rankings[:5]):
        print(f"   [Rank #{idx+1}] Similarity: {r['similarity']:.3f} | Motion: {r['motion_energy']:.1f} | Clip: '{r['filename']}'")
        
    return rankings

if __name__ == "__main__":
    # 單體測試
    ASSETS_DIR = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video\D2\PRIVATE\M4ROOT\CLIP"
    if os.path.exists(ASSETS_DIR):
        cache = extract_features_and_cache(ASSETS_DIR)
        # 測試查詢
        if len(sys.argv) > 1:
            q = sys.argv[1]
        else:
            q = "時尚髮特寫 closeup hair spin model"
        query_semantic_recommendations(q, cache)
    else:
        print(f"Directory not found: {ASSETS_DIR}")
