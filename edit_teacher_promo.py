"""
DaVinci Resolve 21 - Sam 課程前導影片高能對拍剪輯指令碼
功能：
1. 自動清除 "老師" 時間軸上的所有舊片段。
2. 將 "Sam前導影片.mp4" 依據高精人聲分析剪成 36 個無縫人聲片段，去除所有停頓遲疑。
3. 對 Video Track 1 套用交替縮放重構（A/B鏡位交替 Zoom=1.0 / 1.18），並將 Clip 染色為 Teal（藍綠色）。
4. 在 Audio Track 2 從頭拍入背景音樂 "Pawn - The Grey Room _ Golden Palms.mp3"，並精準在人聲結束時切斷。
"""

import sys
import os
import time

# ── Resolve 21 模組初始化 ──────────────────────────────────────
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
    print("❌ DaVinci Resolve is not running. Please open Resolve first.")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
curr_project = project_manager.GetCurrentProject()
if not curr_project:
    print("❌ No active project loaded in Resolve.")
    sys.exit(1)

media_pool = curr_project.GetMediaPool()
if not media_pool:
    print("❌ Cannot access Media Pool.")
    sys.exit(1)

# ── 1. 定位目標時間軸 "老師" ──────────────────────────────────
target_timeline_name = "老師"
timeline_count = curr_project.GetTimelineCount()
target_timeline = None

for i in range(1, timeline_count + 1):
    tl = curr_project.GetTimelineByIndex(i)
    if tl and tl.GetName() == target_timeline_name:
        target_timeline = tl
        break

if not target_timeline:
    print(f"❌ Timeline '{target_timeline_name}' not found!")
    sys.exit(1)

# 強制將當前時間軸切換為 "老師" 並刷新 Resolve GUI
curr_project.SetCurrentTimeline(target_timeline)
print(f"🎬 已載入目標時間軸: {target_timeline.GetName()}")
resolve.OpenPage("media")
time.sleep(0.3)
resolve.OpenPage("edit")
time.sleep(0.3)

# ── 2. 清空時間軸 ──────────────────────────────────────────────
print("🧹 正在物理清空時間軸上所有舊片段...")
for track_type in ["video", "audio"]:
    track_count = target_timeline.GetTrackCount(track_type)
    for t_idx in range(1, track_count + 1):
        items = target_timeline.GetItemListInTrack(track_type, t_idx)
        if items:
            target_timeline.DeleteClips(items)
print("✅ 時間軸清空完畢！")

# ── 3. 定位素材庫中的影片與音樂 ──────────────────────────────
root_folder = media_pool.GetRootFolder()

def find_clip(folder, name):
    for c in folder.GetClipList():
        if c.GetName() == name:
            return c
    for sub in folder.GetSubFolderList() or []:
        res = find_clip(sub, name)
        if res:
            return res
    return None

print("🔍 正在搜尋素材庫...")
sam_clip = find_clip(root_folder, "Sam前導影片.mp4")
bgm_clip = find_clip(root_folder, "Pawn - The Grey Room _ Golden Palms.mp3")

if not sam_clip:
    print("❌ 找不到影片素材: Sam前導影片.mp4")
    sys.exit(1)
if not bgm_clip:
    print("❌ 找不到音樂素材: Pawn - The Grey Room _ Golden Palms.mp3")
    sys.exit(1)

print(f"📍 成功鎖定影片: {sam_clip.GetName()}")
print(f"📍 成功鎖定配樂: {bgm_clip.GetName()}")

# ── 4. 定義人聲活躍區間（秒）與轉換幀 ──────────────────────────
# 36段去暫停人聲活躍區間
segments = [
    (0.32, 0.92), (1.22, 2.24), (2.58, 4.50), (4.88, 5.74), (6.10, 7.58),
    (7.88, 8.20), (8.54, 9.14), (9.68, 11.38), (11.72, 12.32), (12.60, 13.88),
    (14.40, 16.00), (16.54, 17.52), (17.94, 18.34), (18.96, 19.90), (20.16, 20.56),
    (21.16, 21.86), (22.32, 24.06), (24.62, 27.38), (27.90, 30.02), (30.72, 32.44),
    (32.94, 34.88), (35.20, 35.82), (36.72, 37.44), (38.10, 38.92), (39.70, 41.70),
    (42.28, 43.52), (44.70, 46.86), (47.18, 47.88), (48.24, 49.18), (49.46, 51.60),
    (51.92, 53.52), (53.86, 56.94), (57.40, 58.72), (59.14, 59.66), (60.12, 63.10),
    (63.38, 64.06)
]

fps = 24.0
clips_to_append = []

for idx, (start_sec, end_sec) in enumerate(segments):
    start_frame = int(start_sec * fps)
    end_frame = int(end_sec * fps)
    clips_to_append.append({
        "mediaPoolItem": sam_clip,
        "startFrame": start_frame,
        "endFrame": end_frame
    })

print(f"🎬 正在順序追加 {len(clips_to_append)} 個去暫停人聲片段...")
append_success = media_pool.AppendToTimeline(clips_to_append)
if not append_success:
    print("❌ 影片追加失敗！")
    sys.exit(1)
print("✅ 人聲片段追加成功！")

# ── 5. 套用交替縮放重構與 Teal 染色 ──────────────────────────
# 等待達芬奇完成追加
time.sleep(0.5)

video_items = target_timeline.GetItemListInTrack("video", 1)
print(f"🎥 遍歷 V1 軌道上的時間軸片段 (共 {len(video_items)} 個)...")

for idx, item in enumerate(video_items):
    # 奇偶交替 Zoom (1.0 vs 1.18)
    scale = 1.18 if idx % 2 == 1 else 1.0
    item.SetProperty("ZoomX", scale)
    item.SetProperty("ZoomY", scale)
    # 將片段標記為藍綠色 (Teal)
    item.SetClipColor("Teal")

print("✅ 交替畫幅重構（Alternating Zooms）與 Teal 染色套用完畢！")

# ── 6. 覆蓋背景音樂 (A2 Track) ──────────────────────────────
# 確保至少有兩個 Audio 軌道
audio_track_count = target_timeline.GetTrackCount("audio")
if audio_track_count < 2:
    print("🎵 正在為背景音樂建立 Audio Track 2...")
    target_timeline.AddTrack("audio")

# 計算總時間軸長度以決定音樂截斷點
timeline_start = target_timeline.GetStartFrame()
timeline_end = target_timeline.GetEndFrame()
total_duration_frames = timeline_end - timeline_start
print(f"⏱️ 剪輯後人聲總時長：{total_duration_frames / fps:.2f} 秒 (共 {total_duration_frames} 影格)")

bgm_append = [{
    "mediaPoolItem": bgm_clip,
    "startFrame": 0,
    "endFrame": total_duration_frames,
    "recordFrame": timeline_start,
    "trackIndex": 2,
    "mediaType": 2
}]

print("🎵 正在 Audio Track 2 從頭置入並對齊背景音樂...")
bgm_success = media_pool.AppendToTimeline(bgm_append)
if not bgm_success:
    print("❌ 背景音樂置入失敗！")
else:
    print("✅ 背景音樂精準對齊並置入成功！")

# ── 7. 結束宣告 ──────────────────────────────────────────────
print("\n" + "="*50)
print("🎉 SAM 課程前導影片高能對拍剪輯圓滿完成！")
print("="*50)
print(f"時間軸名稱: '{target_timeline.GetName()}'")
print(f"原片時長: 64.88 秒")
print(f"精簡後時長: {total_duration_frames / fps:.2f} 秒")
print(f"已自動去除 {64.88 - (total_duration_frames / fps):.2f} 秒的無聲與語氣停頓區間！")
print(f"視覺效果: A/B鏡位交替 Zoom=1.0/1.18 呼吸重構 ＆ Teal 染色")
print(f"背景音樂: Pawn - The Grey Room _ Golden Palms.mp3 於 A2 精準對齊")
print("\n💡 溫馨提醒（手動拋光 1 秒鐘）：")
print("1. 請手動將音軌 2 (A2) 音量拉低至 -20dB 左右，以獲得完美的背景襯托效果。")
print("2. 建議在音軌 2 結尾拉一個 1.5 秒的 Fade Out（淡出），讓結尾更絲滑收束！\n")
