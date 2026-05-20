import sys
import os
import torch
import numpy as np
import pickle
import cv2
from PIL import Image

# 預設使用的 CLIP 模型名稱
MODEL_NAME = "openai/clip-vit-base-patch32"

def load_clip_model(model_name=MODEL_NAME):
    """
    Loads pretrained CLIP model and processor onto CPU/GPU.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🖥️  AI Hardware Target: {device.upper()}")
    
    # 嘗試引入 transformers 庫
    try:
        from transformers import CLIPProcessor, CLIPModel
    except ImportError:
        print("❌ Error: 'transformers' library not found. Please install transformers and torch.")
        sys.exit(1)
        
    try:
        print(f"   🧠 Loading CLIP model '{model_name}'...")
        # 隱藏警告
        import warnings
        warnings.filterwarnings("ignore")
        
        model = CLIPModel.from_pretrained(model_name).to(device)
        processor = CLIPProcessor.from_pretrained(model_name)
        model.eval()
        return model, processor, device
    except Exception as e:
        print(f"   ❌ Error loading CLIP model: {e}")
        sys.exit(1)

def encode_text_prompts(model, processor, device, prompts_dict, pos_aesthetic, neg_aesthetic):
    """
    Encodes narrative prompts and positive/negative aesthetic anchors into normalized vectors.
    """
    prompt_keys = list(prompts_dict.keys())
    prompt_texts = [prompts_dict[k] for k in prompt_keys]
    
    aesthetic_keys = ["positive", "negative"]
    aesthetic_texts = [pos_aesthetic, neg_aesthetic]
    
    all_texts = prompt_texts + aesthetic_texts
    
    try:
        from transformers import CLIPProcessor, CLIPModel
    except ImportError:
        pass
        
    with torch.no_grad():
        inputs = processor(text=all_texts, return_tensors="pt", padding=True).to(device)
        text_features = model.get_text_features(**inputs)
        text_embeddings = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
        text_embeddings_np = text_embeddings.cpu().numpy()
        
    # 分配特徵向量
    prompt_embeddings = {prompt_keys[i]: text_embeddings_np[i] for i in range(len(prompt_keys))}
    aesthetic_embeddings = {
        "positive": text_embeddings_np[len(prompt_keys)],
        "negative": text_embeddings_np[len(prompt_keys) + 1]
    }
    
    return prompt_embeddings, aesthetic_embeddings

def score_assets(metadata_cache, prompt_embeddings, aesthetic_embeddings):
    """
    Computes semantic similarity scores and aesthetic composition ratings for all assets.
    """
    clip_rankings = []
    
    for filename, meta in metadata_cache.items():
        img_emb = np.array(meta["embedding"])
        sims = {}
        for theme, emb in prompt_embeddings.items():
            sims[theme] = float(np.dot(img_emb, emb))
            
        # 計算美學得分 (正向相似度 - 負向相似度)
        sim_pos = float(np.dot(img_emb, aesthetic_embeddings["positive"]))
        sim_neg = float(np.dot(img_emb, aesthetic_embeddings["negative"]))
        aesthetic_score = sim_pos - sim_neg
        
        record = {
            "filename": filename,
            "path": meta["path"],
            "aesthetic_score": aesthetic_score,
            "motion_energy": meta.get("motion_energy", 0.0)
        }
        for theme in prompt_embeddings.keys():
            record[f"sim_{theme}"] = sims[theme]
            
        clip_rankings.append(record)
        
    return clip_rankings

def load_metadata_cache(cache_dir_or_path):
    """
    Loads cached CLIP visual embeddings (video_metadata.pkl).
    """
    # 預設路徑搜尋
    pkl_path = cache_dir_or_path
    if os.path.isdir(cache_dir_or_path):
        pkl_path = os.path.join(cache_dir_or_path, "video_metadata.pkl")
        
    if not os.path.exists(pkl_path):
        # 搜尋 root 級
        possible_paths = [
            os.path.join(os.getcwd(), "video_metadata.pkl"),
            os.path.join(os.getcwd(), "cache", "video_metadata.pkl"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video_metadata.pkl"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cache", "video_metadata.pkl")
        ]
        for p in possible_paths:
            if os.path.exists(p):
                pkl_path = p
                break
                
    if not os.path.exists(pkl_path):
        print(f"❌ Error: video_metadata.pkl not found at {pkl_path}")
        return None
        
    try:
        with open(pkl_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"❌ Error loading video_metadata.pkl: {e}")
        return None

def extract_features_and_cache(video_dir, cache_path=None):
    """
    Scans the video directory, extracts visual semantic CLIP features, 
    computes physical motion energy, and caches them to disk (supports incremental updates).
    """
    if cache_path is None:
        cache_path = os.path.join(video_dir, "video_metadata.pkl")
        
    print(f"📂 Scanning video assets in: {video_dir}")
    if not os.path.exists(video_dir):
        print(f"❌ Error: Video directory '{video_dir}' does not exist.")
        return {}
        
    video_files = [
        os.path.join(video_dir, f)
        for f in os.listdir(video_dir)
        if f.lower().endswith((".mp4", ".mov"))
    ]
    
    if not video_files:
        print("❌ Error: No video files found in the directory.")
        return {}
        
    # Read existing cache for incremental scanning
    metadata_cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                metadata_cache = pickle.load(f)
            print(f"📦 Loaded existing cache with {len(metadata_cache)} files.")
        except Exception as e:
            print(f"⚠️ Warning: Could not load cache file ({e}). Starting fresh.")
            
    # Filter files that need to be analyzed
    new_files = [f for f in video_files if os.path.basename(f) not in metadata_cache]
    
    if not new_files:
        print("✅ Cache is completely up to date. No new video files to analyze.")
        return metadata_cache
        
    print(f"🎬 Found {len(new_files)} new video files to analyze.")
    
    # Load model
    model, processor, dev = load_clip_model()
    
    # Extract features
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
            
        # Extract 3 keyframes (at 20%, 50%, 80%)
        keyframe_indices = [int(total_frames * 0.2), int(total_frames * 0.5), int(total_frames * 0.8)]
        images = []
        
        for frame_idx in keyframe_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                images.append(Image.fromarray(rgb))
                
        # Calculate motion energy (optical flow proxy)
        middle_frame = int(total_frames * 0.5)
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        ret, prev_frame = cap.read()
        motion_values = []
        
        if ret:
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            for _ in range(10):
                ret, frame = cap.read()
                if not ret:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                diff = cv2.absdiff(gray, prev_gray)
                motion_values.append(np.mean(diff))
                prev_gray = gray
                
        motion_energy = float(np.mean(motion_values)) if motion_values else 0.0
        cap.release()
        
        # CLIP image embeddings
        if not images:
            print(f"   ⚠️ Warning: No keyframes could be extracted from '{filename}'.")
            continue
            
        try:
            with torch.no_grad():
                inputs = processor(images=images, return_tensors="pt").to(dev)
                image_features = model.get_image_features(**inputs)
                mean_embedding = image_features.mean(dim=0)
                mean_embedding = mean_embedding / mean_embedding.norm(p=2, dim=-1, keepdim=True)
                mean_embedding_list = mean_embedding.cpu().numpy().tolist()
        except Exception as e:
            print(f"   ❌ Torch CLIP inference failed: {e}")
            continue
            
        metadata_cache[filename] = {
            "filename": filename,
            "path": path,
            "embedding": mean_embedding_list,
            "motion_energy": motion_energy,
            "fps": fps,
            "frames": total_frames,
            "duration": duration
        }
        
    # Serialize cache
    try:
        dir_name = os.path.dirname(cache_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(cache_path, "wb") as f:
            pickle.dump(metadata_cache, f)
        print(f"\n💾 SUCCESSFULLY CACHED! {len(metadata_cache)} files written to '{cache_path}'")
    except Exception as e:
        print(f"❌ Error writing cache file: {e}")
        
    return metadata_cache
