import os
import sys
import time

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
    print("❌ DaVinci Resolve is not running. Please open Resolve and your project first.")
    sys.exit(1)

# 引入自研的對拍模組
try:
    import beat_detector
except ImportError:
    # 如果找不到，將當前工作目錄加入路徑
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import beat_detector

def run_beat_tagging():
    print("🚀 Starting AI Automated Audio Beat & Marker Tagging System...")
    
    project_manager = resolve.GetProjectManager()
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        print("❌ Error: No project is currently open in DaVinci Resolve.")
        sys.exit(1)
        
    timeline = current_project.GetCurrentTimeline()
    if not timeline:
        print("❌ Error: No active timeline found. Please open a timeline first.")
        sys.exit(1)
        
    print(f"🎬 Active Project: '{current_project.GetName()}'")
    print(f"🎞️ Active Timeline: '{timeline.GetName()}'")
    
    # ── 1. 搜尋音軌 1 上的音樂片段 ───────────────────────────────
    audio_items = timeline.GetItemListInTrack("audio", 1)
    if not audio_items:
        print("❌ Error: No audio clips found on Audio Track 1. Please place your background music on Track 1.")
        sys.exit(1)
        
    audio_clip = None
    audio_file_path = None
    
    for item in audio_items:
        mp_item = item.GetMediaPoolItem()
        if mp_item:
            path = mp_item.GetClipProperty("File Path")
            # 確保檔案路徑存在
            if path and os.path.exists(path):
                audio_clip = item
                audio_file_path = path
                break
                
    if not audio_file_path:
        print("⚠️ Warning: Could not resolve physical file path for Track 1 audio clips.")
        print("Searching active Media Pool folder for audio assets as backup...")
        # 備份機制：搜尋 Media Pool 當前目錄下的音訊檔
        media_pool = current_project.GetMediaPool()
        current_folder = media_pool.GetCurrentFolder()
        clips = current_folder.GetClipList()
        for clip in clips:
            path = clip.GetClipProperty("File Path")
            if path and path.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".flac")):
                if os.path.exists(path):
                    audio_file_path = path
                    print(f"📌 Found audio asset in Media Pool: '{clip.GetName()}' -> {path}")
                    break
                    
    if not audio_file_path:
        print("❌ Error: No valid audio file path found. Please ensure your music file exists on disk.")
        sys.exit(1)
        
    print(f"🎵 Found target music file: '{os.path.basename(audio_file_path)}'")
    print(f"📂 Path: {audio_file_path}")
    
    # ── 2. 獲取時間軸的關鍵參數 ──────────────────────────────────
    timeline_start = timeline.GetStartFrame()
    fps = float(current_project.GetSetting("timelineFrameRate") or 24.0)
    print(f"⚙️ Timeline Start Frame: {timeline_start} | Frame Rate (FPS): {fps}")
    
    # 獲取音樂片段在時間軸上的起點
    audio_start_frame = timeline_start
    if audio_clip:
        audio_start_frame = audio_clip.GetStart()
        print(f"🔗 Music clip starts on timeline at frame: {audio_start_frame}")
    
    # ── 3. 呼叫 AI 進行對拍分析 ──────────────────────────────────
    print("\n🎧 Analyzing audio transients... Please wait a few seconds...")
    start_time = time.time()
    beat_times, bpm = beat_detector.analyze_audio_beats(audio_file_path)
    analysis_duration = time.time() - start_time
    
    if not beat_times:
        print("❌ Error: No beats could be detected in this audio file.")
        sys.exit(1)
        
    print(f"🥁 Analysis complete in {analysis_duration:.2f}s! Estimated Tempo: {bpm:.1f} BPM.")
    print(f"⭐ Detected {len(beat_times)} beats.")
    
    # ── 4. 清理現有的 AI 藍色節拍標記 ────────────────────────────
    print("\n🧹 Clearing existing Blue markers on the timeline to prevent clutter...")
    try:
        success = timeline.DeleteMarkersByColor("Blue")
        if success:
            print("   Deleted old Blue beat markers.")
        else:
            print("   No old Blue markers to delete.")
    except Exception as e:
        print(f"   Note: Clear markers failed or not needed: {e}")
        
    # ── 5. 將對拍結果轉換為影格並寫入 Resolve ──────────────────────
    print("✍️ Writing new beat markers to timeline...")
    added_count = 0
    
    for idx, beat_sec in enumerate(beat_times):
        # 拍子相對於時間軸起點的影格數
        # beat_sec 是相對於音訊檔案起點的秒數
        beat_frame = audio_start_frame + int(round(beat_sec * fps))
        
        # 確保不會寫入小於時間軸起點的非法影格
        if beat_frame < timeline_start:
            continue
            
        marker_name = f"Beat {idx+1}"
        marker_note = f"AI Beat Cut | Time: {beat_sec:.2f}s"
        
        # AddMarker 參數: frameId, color, name, note, duration (預設 1), customData
        success = timeline.AddMarker(
            beat_frame,
            "Blue",
            marker_name,
            marker_note,
            1
        )
        if success:
            added_count += 1
            if added_count <= 5 or added_count == len(beat_times):
                print(f"   [Marker #{added_count}] Added Blue marker at frame {beat_frame} ({beat_sec:.2f}s)")
            elif added_count == 6:
                print("   ...")
                
    print(f"\n🎉 SUCCESS! Written {added_count} Blue beat markers to timeline '{timeline.GetName()}'!")
    print("👉 You can now run 'auto_edit_cinematic.py' to automatically perform a Director's Cut matching these markers!")

if __name__ == "__main__":
    run_beat_tagging()
