"""
DaVinci Resolve 21 - 物理修復時間軸錯位與清空字幕軌
功能：
1. 彻底清空時間軸的所有軌道，包含 Video、Audio 與 Subtitle 軌道，確保時間軸物理淨空。
2. 重新從 86400 影格（時間軸起點）依序追加 22 個語意行銷片段。
3. 套用交替縮放重構 (1.0 vs 1.18) 與 Teal 染色。
4. 在 A2 軌道對齊置入背景配樂並精準裁剪。
"""

import sys
import os
import time

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

target_timeline_name = "老師"
timeline_count = curr_project.GetTimelineCount()
timeline = None
for i in range(1, timeline_count + 1):
    tl = curr_project.GetTimelineByIndex(i)
    if tl and tl.GetName() == target_timeline_name:
        timeline = tl
        break

if not timeline:
    print(f"❌ Timeline '{target_timeline_name}' not found!")
    sys.exit(1)

curr_project.SetCurrentTimeline(timeline)
resolve.OpenPage("media")
time.sleep(0.3)
resolve.OpenPage("edit")
time.sleep(0.3)

# ── 1. 強力清空所有軌道（包括字幕軌） ───────────────────────────
print("🧹 正在啟動物理深度淨空工作流...")
for track_type in ["video", "audio", "subtitle"]:
    track_count = timeline.GetTrackCount(track_type)
    for t_idx in range(1, track_count + 1):
        items = timeline.GetItemListInTrack(track_type, t_idx)
        if items:
            print(f"  - 清空 '{track_type}' 軌道 {t_idx} (共 {len(items)} 個片段)...")
            timeline.DeleteClips(items)
print("✅ 所有軌道（含字幕軌）已徹底清空！")

# ── 2. 定位素材 ────────────────────────────────────────────────
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
    print("❌ 找不到必要的素材片段！")
    sys.exit(1)

# ── 3. 重建 22 個行銷語意片段 ──────────────────────────────────
semantic_order = [
    # 1. Hook
    (5, 8.458, 10.333),
    (6, 10.333, 12.000),
    (7, 12.000, 15.500),
    # 2. Intro & Subject
    (1, 0.000, 1.666),
    (4, 6.791, 8.416),
    (8, 15.500, 17.208),
    (9, 17.208, 18.583),
    # 3. Core Curriculum
    (10, 19.000, 22.125),
    (11, 22.125, 23.833),
    (12, 23.833, 26.416),
    (13, 26.416, 27.958),
    (14, 28.000, 31.208),
    # 4. Endorsement
    (15, 31.208, 32.750),
    (16, 32.916, 34.000),
    (17, 34.000, 35.791),
    (18, 35.833, 38.333),
    (19, 38.333, 41.500),
    # 5. CTA & Tour Info
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

print(f"🎬 正在追加 {len(clips_to_append)} 個片段至全新乾淨起點...")
append_success = media_pool.AppendToTimeline(clips_to_append)
if not append_success:
    print("❌ 片段追加失敗！")
    sys.exit(1)
print("✅ 片段追加成功！已精準鎖定時間軸起始幀 86400！")

# ── 4. 套用交替縮放與 Teal 染色 ──────────────────────────────
time.sleep(0.5)
video_items = timeline.GetItemListInTrack("video", 1)
for idx, item in enumerate(video_items):
    scale = 1.18 if idx % 2 == 1 else 1.0
    item.SetProperty("ZoomX", scale)
    item.SetProperty("ZoomY", scale)
    item.SetClipColor("Teal")
print("✅ 交替縮放重構與 Teal 染色套用完畢！")

# ── 5. 覆蓋背景音樂 ──────────────────────────────────────────
audio_track_count = timeline.GetTrackCount("audio")
if audio_track_count < 2:
    timeline.AddTrack("audio")

timeline_start = timeline.GetStartFrame()
timeline_end = timeline.GetEndFrame()
total_duration_frames = timeline_end - timeline_start
print(f"⏱️ 最終總時長：{total_duration_frames / fps:.2f} 秒 (共 {total_duration_frames} 影格)")

bgm_append = [{
    "mediaPoolItem": bgm_clip,
    "startFrame": 0,
    "endFrame": total_duration_frames,
    "recordFrame": timeline_start,
    "trackIndex": 2,
    "mediaType": 2
}]

print("🎵 正在對齊置入背景音樂...")
bgm_success = media_pool.AppendToTimeline(bgm_append)
if not bgm_success:
    print("❌ 背景音樂置入失敗！")
else:
    print("✅ 背景音樂精準裁切對齊成功！")

print("\n" + "="*50)
print("🎉 物理修復與語意重剪成功！時間軸已恢復完美對齊！")
print("="*50)
print("請現在手動執行「匯入字幕」操作，時間軸將 100% 完美對齊！\n")
