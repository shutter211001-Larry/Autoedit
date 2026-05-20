import os
import sys
import subprocess
import tempfile
import time
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal

# 嘗試載入 librosa
HAS_LIBROSA = False
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    pass

def transcode_to_wav(input_path, output_path):
    """
    使用系統中的 ffmpeg 將任意格式的音軌轉碼為標準的 22050Hz Mono 16-bit WAV 格式
    """
    print(f"🎬 [FFmpeg] Transcoding '{input_path}' to standard mono WAV...")
    
    # 建立 ffmpeg 指令
    # -y: 強制覆寫
    # -ac 1: 單聲道
    # -ar 22050: 採樣率 22050 Hz
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "22050",
        "-f", "wav",
        output_path
    ]
    
    try:
        # 在背景執行轉碼，隱藏輸出
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("✅ [FFmpeg] Transcoding complete.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ [FFmpeg] Transcoding failed! Error: {e.stderr.decode('utf-8', errors='ignore')}")
        return False
    except FileNotFoundError:
        print("❌ [FFmpeg] ffmpeg executable not found in PATH. Please install ffmpeg.")
        return False

def detect_beats_librosa(wav_path):
    """
    主要策略：使用 Librosa 進行專業的動態規劃對拍與 BPM 估算
    """
    print("🎵 [AI Beat] Running Librosa Beat Tracking Engine...")
    y, sr = librosa.load(wav_path, sr=22050)
    
    # 進行對拍追蹤
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    # 將 beats (格數) 轉成秒數
    beat_times = librosa.frames_to_time(beats, sr=sr)
    
    # 確保 tempo 是一個浮點數數值
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0]) if len(tempo) > 0 else 0.0
    else:
        tempo = float(tempo)
        
    print(f"✅ [AI Beat] Librosa completed. Estimated Tempo: {tempo:.2f} BPM. Found {len(beat_times)} beats.")
    return list(beat_times), tempo

def detect_beats_fallback(wav_path):
    """
    備份防禦策略：當系統沒有安裝 Librosa 時，
    使用 SciPy & NumPy 自研的頻譜能量包絡線與暫態峰值檢測 (Transient Onset Detection)。
    在剪輯中，音樂的「鼓點暫態」通常比絕對固定格子的 BPM 更適合做為剪點！
    """
    print("⚡ [AI Beat] Librosa not found. Using SciPy/NumPy Rhythmic Peak Detection (Fallback)...")
    
    # 讀取轉檔後的 WAV 檔案
    sr, data = wavfile.read(wav_path)
    
    # 確保是單聲道浮點數數據
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
        
    # 如果有多聲道（理論上 ffmpeg 轉碼後只有單聲道，但做防禦）
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
        
    # 計算短時能量包絡線 (Short-Time Energy Envelope)
    # 框架大小 1024 點，跳躍步長 512 點 (約 23ms 一幀)
    frame_size = 1024
    hop_size = 512
    
    # 計算信號的滑動能量
    # 快速計算：使用捲積或分塊平方和
    num_frames = (len(data) - frame_size) // hop_size + 1
    energies = np.zeros(num_frames)
    
    for i in range(num_frames):
        start = i * hop_size
        end = start + frame_size
        frame = data[start:end]
        # 使用 RMS (均方根) 作為能量指標
        energies[i] = np.sqrt(np.mean(frame**2) + 1e-8)
        
    # 計算能量的一階差分 (Onset Strength Envelope)
    # 取正值（代表能量遞增的上升沿，也就是鼓點/音符落下的瞬間）
    onset_env = np.diff(energies)
    onset_env = np.maximum(0, onset_env)
    
    # 進行平滑處理 (使用漢寧窗濾波)
    window = signal.windows.hann(5)
    onset_env = signal.convolve(onset_env, window, mode='same')
    
    # 峰值檢測 (Peak Detection)
    # 設定最低間隔距離，避免拍子過於擁擠 (如至少間隔 0.25 秒)
    # 0.25 秒在 sr=22050, hop=512 下約為 0.25 * 22050 / 512 = 10.7 幀
    min_dist_frames = int(0.28 * sr / hop_size)
    
    # 設定閾值為平均能量上升沿的 1.5 倍
    threshold = np.mean(onset_env) + 0.8 * np.std(onset_env)
    
    peaks, _ = signal.find_peaks(
        onset_env, 
        distance=min_dist_frames, 
        prominence=threshold * 0.5
    )
    
    # 將幀索引轉換為時間 (秒)
    # 每一幀的時間中點：(idx * hop_size + frame_size/2) / sr
    beat_times = [(p * hop_size + frame_size / 2) / sr for p in peaks]
    
    # 粗略估算 BPM (計算鄰近拍子間隔的倒數)
    if len(beat_times) > 1:
        intervals = np.diff(beat_times)
        median_interval = np.median(intervals)
        estimated_tempo = 60.0 / median_interval if median_interval > 0 else 120.0
    else:
        estimated_tempo = 120.0
        
    print(f"✅ [AI Beat] SciPy Fallback completed. Estimated Tempo: {estimated_tempo:.2f} BPM. Found {len(beat_times)} rhythmic peaks.")
    return beat_times, estimated_tempo

def analyze_audio_beats(audio_file_path):
    """
    統一對外接口：輸入任何音訊路徑，輸出節拍秒數列表與估計的 BPM
    """
    if not os.path.exists(audio_file_path):
        print(f"❌ [Error] Audio file not found at: {audio_file_path}")
        return [], 0.0
        
    # 建立臨時輸出 wav 檔案路徑
    temp_dir = tempfile.gettempdir()
    temp_wav = os.path.join(temp_dir, "resolve_beat_temp_mono.wav")
    
    # 轉碼
    success = transcode_to_wav(audio_file_path, temp_wav)
    if not success:
        return [], 0.0
        
    beat_times, tempo = [], 0.0
    try:
        # 如果安裝了 librosa，優先使用
        if HAS_LIBROSA:
            beat_times, tempo = detect_beats_librosa(temp_wav)
        else:
            # 否則使用內建的 SciPy 峰值對應
            beat_times, tempo = detect_beats_fallback(temp_wav)
    except Exception as e:
        print(f"⚠️ [AI Beat] Beat analysis encountered an error: {e}. Falling back to SciPy...")
        try:
            beat_times, tempo = detect_beats_fallback(temp_wav)
        except Exception as fallback_err:
            print(f"❌ [AI Beat] Fallback also failed: {fallback_err}")
            
    # 清理暫存檔
    if os.path.exists(temp_wav):
        try:
            os.remove(temp_wav)
        except Exception as e:
            print(f"⚠️ [Clean] Could not remove temp file: {e}")
            
    return beat_times, tempo

def find_best_climax_window(audio_file_path, duration_sec=30.0):
    """
    分析音軌的能量包絡線，使用「起承轉合」數學模型尋找最完美的 30 秒高潮/放緩剪接區間。
    返回最佳的起點秒數 (T_start)。
    """
    if not os.path.exists(audio_file_path):
        print(f"❌ [Error] Audio file not found at: {audio_file_path}")
        return 0.0
        
    # 建立臨時輸出 wav 檔案路徑
    temp_dir = tempfile.gettempdir()
    temp_wav = os.path.join(temp_dir, "resolve_climax_temp.wav")
    
    success = transcode_to_wav(audio_file_path, temp_wav)
    if not success:
        return 0.0
        
    best_start_sec = 0.0
    try:
        sr, data = wavfile.read(temp_wav)
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
            
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
            
        # 計算每一秒的平均 RMS 能量
        total_sec = len(data) // sr
        if total_sec <= duration_sec:
            print(f"⚠️ [AI Music Arc] Audio is too short ({total_sec}s <= {duration_sec}s). Using start 0.0s.")
            return 0.0
            
        sec_energies = []
        for s in range(total_sec):
            start_sample = s * sr
            end_sample = start_sample + sr
            chunk = data[start_sample:end_sample]
            rms = np.sqrt(np.mean(chunk**2) + 1e-8)
            sec_energies.append(rms)
            
        # ── 「起承轉合」數學評分模型 ─────────────────────────────
        # 我們要在 30 秒的視窗中尋找符合以下能量曲線的起點 t：
        # - 起 (0s-5s): 能量較低/中等，建立懸念。
        # - 承 (5s-10s): 能量遞增，鼓點與氣氛上揚。
        # - 轉 (10s-25s): 能量極高，為全曲高潮/副歌 (Chorus Drop)。
        # - 合 (25s-30s): 能量收斂/放緩，給予完美的結尾收尾。
        best_score = -9999.0
        
        for t in range(0, int(total_sec - duration_sec)):
            # 提取 30 秒區間的秒能量
            window = sec_energies[t : t + int(duration_sec)]
            
            # 各階段能量
            e_intro = np.mean(window[0:5])       # 起
            e_buildup = np.mean(window[5:10])     # 承
            e_climax = np.mean(window[10:25])     # 轉 (高潮副歌)
            e_outro = np.mean(window[25:30])      # 合 (放緩結尾)
            
            # 1. 獎勵高潮段落的極致能量
            # 2. 懲罰一開始就已經是最大音量 (缺乏起伏)
            # 3. 懲罰結尾處仍然是最大音量 (缺乏收尾放緩)
            # 4. 獎勵從 '起' 到 '承' 的上揚趨勢
            score = (
                1.8 * e_climax - 
                0.6 * e_intro - 
                0.6 * e_outro + 
                1.0 * (e_buildup - e_intro)
            )
            
            if score > best_score:
                best_score = score
                best_start_sec = float(t)
                
        print(f"👑 [AI Music Arc] Chronological Climax Arc found!")
        print(f"   • Best Start Time: {best_start_sec:.1f}s (Timecode: {time.strftime('%M:%S', time.gmtime(best_start_sec))})")
        print(f"   • Best End Time: {best_start_sec + duration_sec:.1f}s (Timecode: {time.strftime('%M:%S', time.gmtime(best_start_sec + duration_sec))})")
    except Exception as e:
        print(f"❌ [AI Music Arc] Climax analysis failed: {e}. Defaulting to 0.0s.")
        best_start_sec = 0.0
        
    # 清理暫存檔
    if os.path.exists(temp_wav):
        try:
            os.remove(temp_wav)
        except Exception as e:
            pass
            
    return best_start_sec
