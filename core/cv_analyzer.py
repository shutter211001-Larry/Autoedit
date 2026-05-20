import os
import cv2
import json
import numpy as np

def load_cv_cache(cache_path):
    """
    Loads the global motion profile cache from disk.
    """
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cv_cache(cache, cache_path):
    """
    Saves the updated motion profile cache to disk.
    """
    try:
        # 確保資料夾存在
        dir_name = os.path.dirname(cache_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"   ⚠️ Warning: Could not write cache to {cache_path}: {e}")

def find_optimal_stable_unidirectional_window(video_path, duration_frames, fps, cache_path, downsample_step=16, target_width=80):
    """
    Dual-Core rolling CV search algorithm:
    Finds the optimal start frame (In point) that exhibits stable movement, 
    low shake variance, and strict unidirectional camera translation.
    """
    cache = load_cv_cache(cache_path)
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
            
        motion_series = []  # 光流能量 (像素絕對差)
        motion_dx = []      # 水平位移 (1D 投影互相關 dx)
        frame_indices = []
        
        prev_gray = None
        frame_idx = 0
        
        # 逐步解碼並壓縮影像特徵，提速運算
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
                    # 1. 估算運動能量 (RMS difference)
                    diff = cv2.absdiff(gray, prev_gray)
                    mean_diff = float(np.mean(diff))
                    motion_series.append(mean_diff)
                    
                    # 2. 水平投影剖面特徵位移
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
        
        # 將提取結果寫入快取庫中
        cache[video_path] = {
            "total_frames": total_frames,
            "motion_series": motion_series,
            "motion_dx": motion_dx,
            "frame_indices": frame_indices
        }
        save_cv_cache(cache, cache_path)
        
    if len(motion_series) < 3:
        return max(0, (total_frames - duration_frames) // 2)
        
    # 插值為滿影格率特徵序列
    full_motion = np.interp(np.arange(total_frames), frame_indices, motion_series)
    full_dx = np.interp(np.arange(total_frames), frame_indices, motion_dx)
    
    # 滑動視窗評估
    guard_band = int(total_frames * 0.12)  # 首尾 12% 物理安全屏蔽區
    search_start = guard_band
    search_end = total_frames - duration_frames - guard_band
    
    if search_end <= search_start:
        search_start = 0
        search_end = total_frames - duration_frames
        
    best_start = search_start
    best_score = -999999.0
    
    SHAKE_LIMIT = np.mean(full_motion) + 1.5 * np.std(full_motion)
    
    for s in range(int(search_start), int(search_end)):
        win_motion = full_motion[s : s + duration_frames]
        win_dx = full_dx[s : s + duration_frames]
        
        # A. 平穩度得分 (穩定方差取對數)
        variance = np.var(win_motion) + 1e-6
        consistency_score = -np.log(variance)
        
        # B. 劇烈抖動懲罰
        peak_motion = np.max(win_motion)
        shake_penalty = 0.0
        if peak_motion > SHAKE_LIMIT:
            shake_penalty = -10.0 * (peak_motion - SHAKE_LIMIT)
            
        # C. 運動單方向性檢驗 (防止來回晃動)
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
            
        # D. 平均均速微調
        mean_motion = np.mean(win_motion)
        
        # 綜合權重評估
        score = 1.0 * consistency_score + 1.0 * shake_penalty + 1.0 * reversal_penalty - 0.2 * mean_motion
        
        if score > best_score:
            best_score = score
            best_start = s
            
    return int(best_start)
