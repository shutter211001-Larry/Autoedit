import os
import sys
import json
import time

try:
    import cv2
    import numpy as np
except ImportError:
    print("❌ Error: OpenCV or NumPy is not installed. Please run: pip install opencv-python numpy")
    sys.exit(1)

# ── 設定與路徑 ────────────────────────────────────────────────────────
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cv_profile_cache.json")
SRC_VIDEO_DIR = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video\D2\PRIVATE\M4ROOT\CLIP"

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

def pre_cache_video(video_path, downsample_step=16, target_width=80):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"   ❌ Cannot open video file: {os.path.basename(video_path)}")
        return None
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    motion_series = []
    motion_dx = []
    frame_indices = []
    
    prev_gray = None
    frame_idx = 0
    
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
                diff = cv2.absdiff(gray, prev_gray)
                mean_diff = float(np.mean(diff))
                motion_series.append(mean_diff)
                
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
    
    return {
        "total_frames": total_frames,
        "motion_series": motion_series,
        "motion_dx": motion_dx,
        "frame_indices": frame_indices
    }

def main():
    print("🚀 Starting Standalone OpenCV Motion Profile Pre-Caching System...")
    print(f"📂 Scanning Directory: {SRC_VIDEO_DIR}")
    
    if not os.path.exists(SRC_VIDEO_DIR):
        print(f"❌ Error: Source video directory not found: {SRC_VIDEO_DIR}")
        sys.exit(1)
        
    all_files = sorted([f for f in os.listdir(SRC_VIDEO_DIR) if f.upper().endswith(".MP4")])
    print(f"📊 Found {len(all_files)} raw video clips.")
    
    cache = load_cv_cache()
    print(f"📦 Loaded existing cache. Already contains {len(cache)} profiles.")
    
    files_to_process = [f for f in all_files if os.path.join(SRC_VIDEO_DIR, f) not in cache]
    
    if not files_to_process:
        print("✅ All video clips are already cached! No work needed.")
        sys.exit(0)
        
    print(f"📥 {len(files_to_process)} clips remaining to scan. Starting batch pre-caching...\n")
    
    for idx, f in enumerate(files_to_process):
        video_path = os.path.join(SRC_VIDEO_DIR, f)
        print(f"[{idx+1}/{len(files_to_process)}] 🎬 Processing {f}...")
        
        start_t = time.time()
        profile = pre_cache_video(video_path)
        
        if profile:
            cache[video_path] = profile
            save_cv_cache(cache)
            elapsed = time.time() - start_t
            print(f"   ✅ Done in {elapsed:.2f}s! ({profile['total_frames']} frames)")
        else:
            print("   ❌ Failed to process.")
            
    print("\n🎉 All raw clip motion profiles have been cached successfully!")
    print(f"💾 Total profiles stored in '{os.path.basename(CACHE_FILE)}': {len(cache)}")

if __name__ == "__main__":
    main()
