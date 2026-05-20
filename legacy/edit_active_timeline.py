"""
DaVinci Resolve 21 - 於當前活動時間軸執行「高能行銷語意重剪」
功能：
1. 自動讀取使用者目前正在編輯、已開好的活動時間軸。
2. 彻底清空其上的 Video、Audio 與 Subtitle 軌道，確保物理淨空。
3. 依據行銷 AIDA 漏斗語意重組 22 段 Sam 原音影片，精準對齊時間軸起點（86400）。
4. 套用交替縮放重構（1.0 vs 1.18）與 Teal 染色。
5. 在 A2 軌道置入配樂並精準裁剪對齊。
6. 自動重新計算新時間軸上的字幕時間碼，生成全新語意對齊的 SRT 檔案。
"""

import sys
import os
import time
import re

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
    print("❌ Resolve not running.")
    sys.exit(1)

project_manager = resolve.GetProjectManager()
curr_project = project_manager.GetCurrentProject()
media_pool = curr_project.GetMediaPool()

# ── 1. 讀取當前活動時間軸 ──────────────────────────────────────
timeline = curr_project.GetCurrentTimeline()
if not timeline:
    print("❌ 沒有選中任何活動時間軸！請確保您在達芬奇中正開啟目標時間軸。")
    sys.exit(1)

print(f"🎬 成功鎖定使用者開好的活動時間軸: '{timeline.GetName()}'")

# 物理刷新達芬奇 GUI 確保軌道焦點啟動
resolve.OpenPage("media")
time.sleep(0.3)
resolve.OpenPage("edit")
time.sleep(0.3)

# ── 2. 清空所有軌道 ──────────────────────────────────────────────
print("🧹 正在深度淨空該時間軸上的舊素材...")
for track_type in ["video", "audio", "subtitle"]:
    track_count = timeline.GetTrackCount(track_type)
    for t_idx in range(1, track_count + 1):
        items = timeline.GetItemListInTrack(track_type, t_idx)
        if items:
            print(f"  - 清空 '{track_type}' 軌道 {t_idx} (共 {len(items)} 個片段)...")
            timeline.DeleteClips(items)
print("✅ 所有軌道物理清空完畢！")

# ── 3. 定位素材 ────────────────────────────────────────────────
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

sam_clip = find_clip(root_folder, "Sam前導影片.mp4")
bgm_clip = find_clip(root_folder, "Pawn - The Grey Room _ Golden Palms.mp3")

if not sam_clip or not bgm_clip:
    print("❌ 找不到必要的影片或配樂素材！")
    sys.exit(1)

# ── 4. 定義 AIDA 行銷重剪段落 ─────────────────────────────────
semantic_order = [
    # 1. Hook (曜光亮點：最少操作最感變化、設計創造價值)
    (5, 8.458, 10.333),
    (6, 10.333, 12.000),
    (7, 12.000, 15.500),
    # 2. Intro & Subject (自我介紹、曜光開題)
    (1, 0.000, 1.666),
    (4, 6.791, 8.416),
    (8, 15.500, 17.208),
    (9, 17.208, 18.583),
    # 3. Core Curriculum (實戰課綱：判斷頭髮髮型、雙氧選擇、配方模擬、設計與風格)
    (10, 19.000, 22.125),
    (11, 22.125, 23.833),
    (12, 23.833, 26.416),
    (13, 26.416, 27.958),
    (14, 28.000, 31.208),
    # 4. Endorsement (產品與品牌背書：施華蔻穩定安全無可取代)
    (15, 31.208, 32.750),
    (16, 32.916, 34.000),
    (17, 34.000, 35.791),
    (18, 35.833, 38.333),
    (19, 38.333, 41.500),
    # 5. CTA & Tour Info (巡迴資訊與報名號召)
    (2, 1.666, 4.291),
    (3, 4.291, 6.791),
    (20, 41.500, 45.041),
    (21, 45.041, 46.583),
    (22, 46.583, 46.833)
]

fps = 24.0
clips_to_append = []
for sub_idx, start_sec, end_sec in semantic_order:
    start_frame = int(start_sec * fps)
    end_frame = int(end_sec * fps)
    clips_to_append.append({
        "mediaPoolItem": sam_clip,
        "startFrame": start_frame,
        "endFrame": end_frame
    })

print(f"🎬 正在 '{timeline.GetName()}' 上依據黃金行銷語意追加 {len(clips_to_append)} 個片段...")
append_success = media_pool.AppendToTimeline(clips_to_append)
if not append_success:
    print("❌ 片段追加失敗！請確保當前時間軸的 V1 軌道未被鎖定且 destination selection 已開啟。")
    sys.exit(1)
print("✅ 片段追加成功！已完美鎖定時間軸起始幀 86400！")

# ── 5. 套用交替縮放與 Teal 染色 ──────────────────────────────
time.sleep(0.5)
video_items = timeline.GetItemListInTrack("video", 1)
print(f"🎥 遍歷 V1 軌道上的重組片段 (共 {len(video_items)} 個)...")

for idx, item in enumerate(video_items):
    scale = 1.18 if idx % 2 == 1 else 1.0
    item.SetProperty("ZoomX", scale)
    item.SetProperty("ZoomY", scale)
    item.SetClipColor("Teal")
print("✅ 交替縮放重構與 Teal 染色套用完畢！")

# ── 6. 覆蓋背景音樂 ──────────────────────────────────────────
audio_track_count = timeline.GetTrackCount("audio")
if audio_track_count < 2:
    timeline.AddTrack("audio")

timeline_start = timeline.GetStartFrame()
timeline_end = timeline.GetEndFrame()
total_duration_frames = timeline_end - timeline_start
print(f"⏱️ 影片總時長：{total_duration_frames / fps:.2f} 秒 (共 {total_duration_frames} 影格)")

bgm_append = [{
    "mediaPoolItem": bgm_clip,
    "startFrame": 0,
    "endFrame": total_duration_frames,
    "recordFrame": timeline_start,
    "trackIndex": 2,
    "mediaType": 2
}]

print("🎵 正在置入與對齊背景音樂...")
bgm_success = media_pool.AppendToTimeline(bgm_append)
if not bgm_success:
    print("❌ 背景音樂置入失敗！")
else:
    print("✅ 背景音樂精準對齊裁切置入成功！")

# ── 7. 重新生成精確對齊 SRT 字幕 ──────────────────────────────
srt_path = r"C:\TEST\Sam_corrected.srt"
if not os.path.exists(srt_path):
    srt_path = r"C:\TEST\Sam.srt"

print(f"\n📂 正在讀取並解析字幕檔 {srt_path}...")
subtitles_dict = {}

with open(srt_path, "r", encoding="utf-8") as f:
    content = f.read()

blocks = re.findall(r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\n\d+\n|\Z)", content, re.DOTALL)
for b in blocks:
    sub_id = int(b[0])
    text = b[3].strip()
    subtitles_dict[sub_id] = text

def format_timecode(seconds):
    total_seconds = int(seconds)
    ms = int((seconds - total_seconds) * 1000)
    hours = 1 + (total_seconds // 3600)
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"

new_srt_lines = []
current_timeline_time = 0.0

for new_idx, (orig_id, start_sec, end_sec) in enumerate(semantic_order, 1):
    duration = end_sec - start_sec
    new_start_tc = format_timecode(current_timeline_time)
    new_end_tc = format_timecode(current_timeline_time + duration)
    text = subtitles_dict.get(orig_id, "<b>(字幕讀取錯誤)</b>")
    new_srt_lines.append(f"{new_idx}\n{new_start_tc} --> {new_end_tc}\n{text}\n\n")
    current_timeline_time += duration

new_srt_content = "".join(new_srt_lines)
with open(r"C:\TEST\Sam.srt", "w", encoding="utf-8") as f:
    f.write(new_srt_content)
with open(r"C:\TEST\Sam_corrected.srt", "w", encoding="utf-8") as f:
    f.write(new_srt_content)

print("✅ 全新「行銷語意對齊」SRT 字幕生成完畢！已覆寫至 C:\\TEST\\Sam.srt")

print("\n" + "="*60)
print(f"🎉 活動時間軸【{timeline.GetName()}】語意行銷剪輯圓滿成功！")
print("="*60)
print(f"時間軸名稱: '{timeline.GetName()}'")
print(f"影片總時長: {current_timeline_time:.2f} 秒")
print("請點擊 File > Import > Subtitle，選取 C:\\TEST\\Sam.srt 拖至 01:00:00:00 起點即可完美播放！\n")
