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
project = project_manager.GetCurrentProject()
media_pool = project.GetMediaPool()
root_folder = media_pool.GetRootFolder()

# ── 1. Create New Timeline "Mars_Antigravity究極精剪版" ──────────────────────────
new_timeline_name = "Mars_Antigravity究極精剪版"

timeline_count = project.GetTimelineCount()
for i in range(1, timeline_count + 1):
    tl = project.GetTimelineByIndex(i)
    if tl and tl.GetName() == new_timeline_name:
        print(f"⚠️ Timeline '{new_timeline_name}' already exists, deleting old one...")
        project.SetCurrentTimeline(tl)
        for track_type in ["video", "audio", "subtitle"]:
            tc = tl.GetTrackCount(track_type)
            for t_idx in range(1, tc + 1):
                items = tl.GetItemListInTrack(track_type, t_idx)
                if items:
                    tl.DeleteClips(items)
        tl.SetName(f"Mars_Antigravity舊備份_{int(time.time())}")
        break

print(f"🆕 Creating new blank timeline: '{new_timeline_name}'...")
new_timeline = media_pool.CreateEmptyTimeline(new_timeline_name)
if not new_timeline:
    print("❌ Failed to create timeline!")
    sys.exit(1)

print(f"🎬 New timeline created successfully: '{new_timeline.GetName()}'")
project.SetCurrentTimeline(new_timeline)

resolve.OpenPage("media")
time.sleep(0.3)
resolve.OpenPage("edit")
time.sleep(0.3)

# ── 2. Locate Source Footage and Music ──────────────────────────
def find_clip(folder, name):
    for c in folder.GetClipList():
        if name in c.GetName():
            return c
    for sub in folder.GetSubFolderList() or []:
        res = find_clip(sub, name)
        if res:
            return res
    return None

c055_clip = find_clip(root_folder, "C055")
c056_clip = find_clip(root_folder, "C056")
c057_clip = find_clip(root_folder, "C057")
c058_clip = find_clip(root_folder, "C058")
c059_clip = find_clip(root_folder, "C059")
bgm_clip = find_clip(root_folder, "Only Little")

if not all([c055_clip, c056_clip, c057_clip, c058_clip, c059_clip]):
    print("❌ Failed to locate all target video clips in Master pool!")
    sys.exit(1)

# ── 3. Define Antigravity's Custom Editorial Flow ──────────────────────────
# Completely decoupled from Timeline 1, built purely on semantic and narrative flow.
custom_flow = [
    # 1. Branding Intro (Davines Collaboration & Topic)
    {
        "clip": c055_clip, "name": "C055", "start": 0, "end": 675, "color": "Rose",
        "subs": ["那這次跟特分立合作的這個商業課程", "這個課程我們主打的是一個商業高層次加區塊設計"]
    },
    # 2. Outline #1: Efficient Cut & Bleaching Details
    {
        "clip": c056_clip, "name": "C056", "start": 759, "end": 1985, "color": "Teal",
        "subs": [
            "那這次課程呢，我們大概會解決幾個要點：第一個",
            "我們會用15分鐘的時間，剪出最高效的層次裁剪，就是讓所有的設計師省時了",
            "不用那麼費力費心，就是省時的高效去做裁剪",
            "讓大家在現場的時候，翻桌率是能夠提升的",
            "那在漂髮的部分呢，我們這次會帶大家去看如何漂到乾淨透亮的程度",
            "那我們去做上色的時候，讓它更有光澤"
        ]
    },
    # 3. Outline #2: No-Bleach Matte One-Bowl Color
    {
        "clip": c057_clip, "name": "C057", "start": 140, "end": 897, "color": "Pink",
        "subs": [
            "第二個主題呢，我們這次會做一個不漂不退的霧感",
            "那依照2025的趨勢的延伸，那我們這次實現所謂的一碗通刷，不退不漂",
            "如何去做到最灰感最霧感的顏色"
        ]
    },
    # 4. Pain Point & Solution: Siam Blending
    {
        "clip": c058_clip, "name": "C058", "start": 2124, "end": 2302, "color": "Orange",
        "subs": ["做出來的尾巴的那個黑色很生硬，不管是在拍照或是肉眼看的時候，硬線都是非常明顯"]
    },
    {
        "clip": c058_clip, "name": "C058", "start": 2574, "end": 2866, "color": "Orange",
        "subs": ["這次的課程要幫所有的設計師，怎麼去做到淡化的效果"]
    },
    {
        "clip": c058_clip, "name": "C058", "start": 3011, "end": 3155, "color": "Orange",
        "subs": ["黑色、主色是要怎麼能夠融合在一起"]
    },
    # 5. Advanced Mindset: Unified Theory of Life & Bleach Colors
    {
        "clip": c058_clip, "name": "C058", "start": 23947, "end": 24796, "color": "Yellow",
        "subs": [
            "你做霧感色系的客人，他終究有一天，他也可能會需要做到漂髮",
            "你做漂髮的客人，他也有一天可能會回歸到這種霧感的生活色",
            "所以我會把這兩種的理論，把它套在一起"
        ]
    },
    # 6. Commercial Results & Call to Action
    {
        "clip": c059_clip, "name": "C059", "start": 4599, "end": 5360, "color": "Green",
        "subs": [
            "我們在現場實作帶來的業績的成長是 80% 到 90%",
            "每個月大概都可以成長大概 10 萬到 20 萬左右",
            "很值得所有設計師來上的一堂課"
        ]
    }
]

fps = 60.0
clips_to_append = []
for idx, cut in enumerate(custom_flow):
    clips_to_append.append({
        "mediaPoolItem": cut["clip"],
        "startFrame": cut["start"],
        "endFrame": cut["end"]
    })

print(f"🎬 Appending {len(clips_to_append)} custom semantic cuts into V1 timeline...")
append_success = media_pool.AppendToTimeline(clips_to_append)
if not append_success:
    print("❌ Failed to append clips!")
    sys.exit(1)
print("✅ Custom semantic cuts appended successfully!")

# ── 4. Apply Dynamic Reframing and Custom Color Coding ──────────────────────────
time.sleep(0.5)
video_items = new_timeline.GetItemListInTrack("video", 1)
for idx, item in enumerate(video_items):
    # Dynamic reframing (1.0 vs 1.15) to cover jump cuts
    zoom = 1.15 if idx % 2 == 1 else 1.0
    item.SetProperty("ZoomX", zoom)
    item.SetProperty("ZoomY", zoom)
    
    # Custom section coloring
    color = custom_flow[idx]["color"]
    item.SetClipColor(color)
print("✅ Zoom reframing and custom section color coding applied!")

# ── 5. Overlay Background Music (BGM) ──────────────────────────
if bgm_clip:
    timeline_start = new_timeline.GetStartFrame()
    timeline_end = new_timeline.GetEndFrame()
    total_duration_frames = timeline_end - timeline_start
    print(f"⏱️ Video Total Duration: {total_duration_frames / fps:.2f} seconds ({total_duration_frames} frames)")
    
    audio_track_count = new_timeline.GetTrackCount("audio")
    if audio_track_count < 2:
        new_timeline.AddTrack("audio")
        
    bgm_append = [{
        "mediaPoolItem": bgm_clip,
        "startFrame": 0,
        "endFrame": total_duration_frames,
        "recordFrame": timeline_start,
        "trackIndex": 2,
        "mediaType": 2
    }]
    
    print("🎵 Adding background music to A2...")
    bgm_success = media_pool.AppendToTimeline(bgm_append)
    if bgm_success:
        print("✅ Background music aligned and added to A2!")
    else:
        print("⚠️ Background music addition failed.")

# ── 6. Generate Custom SRT Subtitle File ──────────────────────────
srt_lines = []
current_time = 0.0

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

sub_index = 1
for cut in custom_flow:
    duration_secs = (cut["end"] - cut["start"]) / fps
    subs = cut["subs"]
    
    sub_dur = duration_secs / len(subs)
    for txt in subs:
        start_tc = format_srt_time(current_time)
        end_tc = format_srt_time(current_time + sub_dur)
        srt_lines.append(f"{sub_index}\n{start_tc} --> {end_tc}\n<b>{txt}</b>\n\n")
        sub_index += 1
        current_time += sub_dur

srt_path = r"c:\TEST\scratch\Mars_Marketing_Antigravity.srt"
with open(srt_path, "w", encoding="utf-8") as f:
    f.write("".join(srt_lines))

print(f"✅ Generated Antigravity custom SRT subtitle file at {srt_path}")
print("\n" + "="*60)
print("🎉 Antigravity Custom Ultimate Semantic Editing Timeline Created Successfully!")
print("="*60)
print(f"Timeline: '{new_timeline.GetName()}' is now live in DaVinci Resolve.")
print(f"Subtitle: c:\\TEST\\scratch\\Mars_Marketing_Antigravity.srt")
