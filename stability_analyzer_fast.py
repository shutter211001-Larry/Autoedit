import os
import sys
import time
import cv2
import numpy as np

def find_most_stable_window_fast(video_path, duration_frames, fps, downsample_step=3):
    """
    超高速單次掃描平穩度算法：
    使用單次連續前向解碼 (Sequential Decode)，避免慢速的 cap.set 尋軌操作。
    在 1 秒內分析整段影片，尋找長度為 duration_frames 的最均勻、平滑的最佳切入點。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames <= duration_frames:
        cap.release()
        return 0
        
    motion_series = []
    frame_indices = []
    
    prev_gray = None
    frame_idx = 0
    
    # ── 單次前向連續解碼，硬體極速讀取 ──────────────────────────────
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # 每隔 downsample_step 幀進行一次圖像光流差值計算，其餘幀直接跳過
        if frame_idx % downsample_step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # 低通濾波消除雜訊
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            
            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                mean_diff = float(np.mean(diff))
                motion_series.append(mean_diff)
                frame_indices.append(frame_idx)
                
            prev_gray = gray
            
        frame_idx += 1
        
    cap.release()
    
    if len(motion_series) < 3:
        return max(0, (total_frames - duration_frames) // 2)
        
    # 插值還原為滿幀率的運動能量曲線
    full_motion = np.interp(np.arange(total_frames), frame_indices, motion_series)
    
    # ── 滑動平穩度視窗計算 ──────────────────────────────────────
    # 前後各保留 10% 做按鈕抖動防護帶
    guard_band = int(total_frames * 0.10)
    search_start = guard_band
    search_end = total_frames - duration_frames - guard_band
    
    if search_end <= search_start:
        guard_band = int(total_frames * 0.05)
        search_start = guard_band
        search_end = total_frames - duration_frames - guard_band
        if search_end <= search_start:
            search_start = 0
            search_end = total_frames - duration_frames
            
    best_start = search_start
    best_score = -999999.0
    
    # 計算全片平均運動能量與方差閾值，用於判定剧烈抖動
    SHAKE_LIMIT = np.mean(full_motion) + 1.5 * np.std(full_motion)
    
    for s in range(int(search_start), int(search_end)):
        window = full_motion[s : s + duration_frames]
        
        # 1. 均速平穩性 (Consistency)：低方差代表運鏡速度極度平滑，無加速抖動
        variance = np.var(window) + 1e-6
        consistency_score = -np.log(variance)
        
        # 2. 劇烈晃動懲罰 (Shake Penalty)
        peak_motion = np.max(window)
        mean_motion = np.mean(window)
        
        shake_penalty = 0.0
        if peak_motion > SHAKE_LIMIT:
            shake_penalty = -5.0 * (peak_motion - SHAKE_LIMIT)
            
        # 總穩定度綜合評估 (平滑性高 + 無劇烈抖動 + 合理的相機運動)
        score = 1.0 * consistency_score + 1.0 * shake_penalty - 0.2 * mean_motion
        
        if score > best_score:
            best_score = score
            best_start = s
            
    return int(best_start)

if __name__ == "__main__":
    video_dir = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video\D2\PRIVATE\M4ROOT\CLIP"
    test_clip = os.path.join(video_dir, "C0268.MP4")
    
    if os.path.exists(test_clip):
        print(f"🔍 Analyzing clip stability: '{os.path.basename(test_clip)}' using fast decoder...")
        t0 = time.time()
        
        optimal_start = find_most_stable_window_fast(test_clip, 48, 24)
        
        print(f"⚡ FAST Analysis finished in {time.time() - t0:.2f}s!")
        print(f"👑 Optimal Start Frame: {optimal_start}")
        print(f"👉 Recommended Cut Range: [{optimal_start} to {optimal_start + 48}]")
    else:
        print("Test clip not found")
