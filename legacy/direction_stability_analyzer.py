import os
import sys
import time
import cv2
import numpy as np

def estimate_horizontal_shift(gray1, gray2, search_range=8):
    """
    一維水平投影剖面互相關算法：
    計算兩個灰階圖像之間的水平相對位移量 dx (像素)。
    """
    # 1. 垂直投影得到一維特徵剖面
    p1 = np.sum(gray1, axis=0)
    p2 = np.sum(gray2, axis=0)
    
    # 2. 均值歸一化，消除光照不均與亮度波動
    p1 = p1 - np.mean(p1)
    p2 = p2 - np.mean(p2)
    
    best_shift = 0.0
    min_diff = float('inf')
    
    # 3. 在特定搜索區間內進行一維平移比對
    for shift in range(-search_range, search_range + 1):
        if shift < 0:
            diff = np.mean(np.abs(p1[-shift:] - p2[:shift]))
        elif shift > 0:
            diff = np.mean(np.abs(p1[:-shift] - p2[shift:]))
        else:
            diff = np.mean(np.abs(p1 - p2))
            
        if diff < min_diff:
            min_diff = diff
            best_shift = float(shift)
            
    return best_shift

def analyze_directional_movement(video_path, duration_frames, fps, downsample_step=3, target_width=120):
    """
    利用一維投影剖面法，進行超高速運鏡方向單調性分析。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"⚠️ Cannot open video: {os.path.basename(video_path)}")
        return
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    motion_dx = []
    frame_indices = []
    
    prev_gray = None
    frame_idx = 0
    
    # ── 1. 逐幀解碼並進行投影剖面互相關 ──────────────────────────────
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_idx % downsample_step == 0:
            # 降採樣
            h, w = frame.shape[:2]
            scale = target_width / float(w)
            target_height = int(h * scale)
            small_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_NEAREST)
            
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            # 輕微高斯模糊
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            
            if prev_gray is not None:
                # 調用純 NumPy 的一維投影位移計算法
                dx = estimate_horizontal_shift(prev_gray, gray)
                motion_dx.append(dx)
                frame_indices.append(frame_idx)
                
            prev_gray = gray
            
        frame_idx += 1
        
    cap.release()
    
    if len(motion_dx) < 3:
        print("❌ Video too short to analyze.")
        return
        
    # 插值補齊滿影格率的運動方向曲線
    full_dx = np.interp(np.arange(total_frames), frame_indices, motion_dx)
    
    # ── 2. 滑動評估所有視窗的「單調性比例 (Monotonicity Ratio)」 ─────────
    guard_band = int(total_frames * 0.10)
    search_start = guard_band
    search_end = total_frames - duration_frames - guard_band
    
    if search_end <= search_start:
        search_start = 0
        search_end = total_frames - duration_frames
        
    print(f"\n📈 Scanning {total_frames} frames for optimal smooth pan window (Size: {duration_frames}f)...")
    
    best_start = search_start
    best_score = -999999.0
    best_ratio = 0.0
    best_dx_mean = 0.0
    
    for s in range(int(search_start), int(search_end)):
        win_dx = full_dx[s : s + duration_frames]
        
        # A. 方向單調性計算 (Sign Monotonicity)
        # 統計在這個區間內，相機往右移 (dx > 0) 與往左移 (dx < 0) 的格數
        pos_frames = np.sum(win_dx > 0.05)
        neg_frames = np.sum(win_dx < -0.05)
        
        # 計算向主導方向運動的比例
        active_frames = pos_frames + neg_frames
        if active_frames == 0:
            mono_ratio = 1.0
        else:
            mono_ratio = max(pos_frames, neg_frames) / float(active_frames)
            
        # B. 計算位移方差 (Variance)
        variance = np.var(win_dx) + 1e-6
        consistency_score = -np.log(variance)
        
        # C. 綜合評穩度與方向一致性得分
        reversal_penalty = 0.0
        if mono_ratio < 0.90:
            # 比例越接近 0.5 (來回搖擺)，處罰越重
            reversal_penalty = -25.0 * (0.90 - mono_ratio)
            
        mean_abs_dx = np.mean(np.abs(win_dx))
        
        score = 1.0 * consistency_score + 1.0 * reversal_penalty - 0.5 * mean_abs_dx
        
        if score > best_score:
            best_score = score
            best_start = s
            best_ratio = mono_ratio
            best_dx_mean = np.mean(win_dx)
            
    print(f"👑 Analysis Complete!")
    print(f"   • Best Start Frame: {best_start}")
    print(f"   • Directional Monotonicity Ratio: {best_ratio*100:.1f}%")
    print(f"   • Average Translation Speed (dx): {best_dx_mean:.4f} pixels/frame")
    print(f"   • Motion Description: {'Pure Steady Panning' if best_ratio >= 0.92 else 'Inconsistent Jittery'} (Avg DX={best_dx_mean:.3f})")
    print(f"👉 Recommended Cut Range: [{best_start} to {best_start + duration_frames}]")

if __name__ == "__main__":
    video_dir = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video\D2\PRIVATE\M4ROOT\CLIP"
    test_clip = os.path.join(video_dir, "C0268.MP4")
    
    if os.path.exists(test_clip):
        print(f"🔍 Testing direction reversing detector on: '{os.path.basename(test_clip)}'...")
        t0 = time.time()
        analyze_directional_movement(test_clip, duration_frames=48, fps=24)
        print(f"⏱️ Finished in {time.time() - t0:.2f}s!")
    else:
        print("Test clip not found")
