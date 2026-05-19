import os
import sys
import time
import cv2
import numpy as np

def find_most_stable_window(video_path, duration_frames, fps, downsample_step=2):
    """
    動態滑動視窗平穩度算法：
    分析整段影片的訊號，尋找長度為 duration_frames 的區間中「最平穩、無抖動、無按鈕震盪」的最佳切入點。
    返回最佳的起始影格 (src_start)。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"⚠️ Cannot open video: {os.path.basename(video_path)}")
        return 0
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = float(cap.get(cv2.CAP_PROP_FPS) or 29.97)
    
    if total_frames <= duration_frames:
        cap.release()
        return 0
        
    # ── 1. 物理影格差分掃描 (Optical Flow Proxy) ───────────────────
    # 為提升運算速度，我們使用每 downsample_step 影格進行跳格差分
    motion_series = []
    frame_indices = []
    
    prev_gray = None
    success_frames = 0
    
    # 讀取並計算整段影片的逐幀運動能量
    for f_idx in range(0, total_frames, downsample_step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 進行輕微的高斯模糊，濾除高頻雜訊與膠片顆粒雜點，專注於大塊物理相機運動
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        if prev_gray is not None:
            # 計算相鄰幀的絕對像素變化差值
            diff = cv2.absdiff(gray, prev_gray)
            mean_diff = float(np.mean(diff))
            motion_series.append(mean_diff)
            frame_indices.append(f_idx)
            
        prev_gray = gray
        success_frames += 1
        
    cap.release()
    
    if len(motion_series) < 5:
        # 資料過短防禦，直接回傳中段
        return max(0, (total_frames - duration_frames) // 2)
        
    # ── 2. 插值補齊逐影格運動曲線 ────────────────────────────────
    # 將跳格掃描的運動分數插值擴展到與影片總格數一致
    full_motion = np.interp(np.arange(total_frames), frame_indices, motion_series)
    
    # ── 3. 滑動視窗穩定度評估 ───────────────────────────────────
    # 排除影片最開頭與最結尾的 10% 區域 (按鈕按壓抖動防禦)
    guard_band = int(total_frames * 0.10)
    search_start = guard_band
    search_end = total_frames - duration_frames - guard_band
    
    if search_end <= search_start:
        # 若影片太短，收縮防禦帶為 5%
        guard_band = int(total_frames * 0.05)
        search_start = guard_band
        search_end = total_frames - duration_frames - guard_band
        if search_end <= search_start:
            search_start = 0
            search_end = total_frames - duration_frames
            
    best_start = search_start
    best_score = -999999.0
    
    # 運動閥值：高於此值視為劇烈晃動/廢鏡
    SHAKE_LIMIT = np.mean(full_motion) + 1.5 * np.std(full_motion)
    
    for s in range(int(search_start), int(search_end)):
        window = full_motion[s : s + duration_frames]
        
        # A. 運鏡平穩性分數 (Consistency)：運動能量的方差 (Variance)
        # 方差越低，說明運鏡速度極度均勻穩定 (均速平移或穩定懸停)。方差高說明相機在劇烈加速或減速。
        variance = np.var(window) + 1e-6
        consistency_score = -np.log(variance) # 方差越小，分數越高
        
        # B. 抖動劇烈度懲罰 (Peak Shake Penalty)
        # 尋找該視窗內的運動峰值與均值，若有突發性的大晃動則給予極重處罰
        peak_motion = np.max(window)
        mean_motion = np.mean(window)
        
        shake_penalty = 0.0
        if peak_motion > SHAKE_LIMIT:
            # 突發性劇烈抖動
            shake_penalty = -5.0 * (peak_motion - SHAKE_LIMIT)
            
        # C. 總平穩度得分
        # 權重分配：70% 運鏡均勻一致度 + 30% 排除突發震動
        score = 1.0 * consistency_score + 1.0 * shake_penalty - 0.2 * mean_motion
        
        if score > best_score:
            best_score = score
            best_start = s
            
    return int(best_start)

if __name__ == "__main__":
    # 單體測試
    video_dir = r"G:\共用雲端硬碟\專業髮品\04影音部\Larry\Schwarzkopf\260511\Video\D2\PRIVATE\M4ROOT\CLIP"
    test_clip = os.path.join(video_dir, "C0268.MP4") # Medium R->L
    
    if os.path.exists(test_clip):
        print(f"🔍 Analyzing clip stability: '{os.path.basename(test_clip)}'...")
        t0 = time.time()
        
        # 假設我們要在這段影片中擷取 2 秒的片段 (48 影格 @ 24 FPS)
        optimal_start = find_most_stable_window(test_clip, 48, 24)
        
        print(f"⏱️ Analysis finished in {time.time() - t0:.2f}s!")
        print(f"👑 Optimal Start Frame: {optimal_start} (out of 200+ frames)")
        print(f"👉 Recommended Cut Range: [{optimal_start} to {optimal_start + 48}]")
    else:
        print("Test clip not found")
