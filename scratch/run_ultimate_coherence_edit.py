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

# ── 1. Create New Timeline "Mars_AI導演獨立探索版" ──────────────────────────
new_timeline_name = "Mars_AI導演獨立探索版"

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
        tl.SetName(f"Mars_獨立探索舊備份_{int(time.time())}")
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

# ── 3. Define the AI Director's Fully Coherent Narrative Flow ──────────────────────────
# 100% independent of Timeline 1, perfectly grouped by technical themes to eliminate all subject jumps.
ultimate_coherent_flow = [
    # ── PART 1: WELCOME & BRAND INTRO ──
    {
        "clip": c058_clip, "name": "C058", "start": 28203, "end": 28290, "color": "Rose",
        "subs": ["大家好我是Mars，我們這堂課呢"]
    },
    {
        "clip": c058_clip, "name": "C058", "start": 28413, "end": 28686, "color": "Rose",
        "subs": [
            "分別是暹羅貓漂色",
            "另外一個是不漂的霧感"
        ]
    },
    {
        "clip": c055_clip, "name": "C055", "start": 0, "end": 1019, "color": "Rose",
        "subs": [
            "那這次跟特分立合作的商業課程",
            "這個課程我們主打的是",
            "商業高層次加區塊設計"
        ]
    },
    {
        "clip": c056_clip, "name": "C056", "start": 0, "end": 759, "color": "Rose",
        "subs": [
            "主要以層次的堆疊跟光影掌控",
            "創造板面的引流效果"
        ]
    },
    {
        "clip": c056_clip, "name": "C056", "start": 759, "end": 987, "color": "Rose",
        "subs": [
            "那這次課程呢，我們會解決幾項要點"
        ]
    },
    
    # ── PART 2: SIAM BLOCK COLORING (PAIN POINT ➔ SOLUTIONS) ──
    {
        "clip": c058_clip, "name": "C058", "start": 2124, "end": 2302, "color": "Orange",
        "subs": [
            "做出來的尾巴黑色很生硬",
            "不管是拍照或肉眼看的時候",
            "硬線都是非常明顯"
        ]
    },
    {
        "clip": c058_clip, "name": "C058", "start": 3011, "end": 3155, "color": "Teal",
        "subs": [
            "黑色、主色是要怎麼融合在一起"
        ]
    },
    {
        "clip": c058_clip, "name": "C058", "start": 20981, "end": 21486, "color": "Teal",
        "subs": [
            "區塊的公式配方，需要高飽和時",
            "我的歐系染膏拿出來能夠做到飽和",
            "但我需要淡化的時候",
            "我的歐系染膏同時也能做到一樣效果"
        ]
    },
    
    # ── PART 3: EFFICIENT CUTTING & MATTE生活色 (TREND & WHITE HAIR) ──
    {
        "clip": c056_clip, "name": "C056", "start": 1145, "end": 1985, "color": "Pink",
        "subs": [
            "第一點是15分鐘高效裁剪",
            "讓大家在現場的時候",
            "翻桌率是能夠提升的",
            "那在漂髮的部分呢",
            "我們這次會帶大家去看",
            "如何漂到乾淨透亮的程度",
            "那我們去做上色的時候",
            "讓它更有光澤"
        ]
    },
    {
        "clip": c057_clip, "name": "C057", "start": 140, "end": 897, "color": "Pink",
        "subs": [
            "第二個主題呢",
            "我們這次會做不漂不退的霧感",
            "那依照2025的趨勢的延伸",
            "那我們這次實現一碗通刷",
            "不退不漂",
            "如何去做到最灰最霧的顏色"
        ]
    },
    {
        "clip": c059_clip, "name": "C059", "start": 1402, "end": 1906, "color": "Pink",
        "subs": [
            "針對白髮我用最簡單配方比例",
            "去做到能夠實現白髮既有霧透感",
            "它也能蓋到70%到80%的程度"
        ]
    },
    {
        "clip": c058_clip, "name": "C058", "start": 23947, "end": 24796, "color": "Yellow",
        "subs": [
            "你做霧感色系的客人",
            "他終究有一天也可能會需要漂髮",
            "你做漂髮的客人",
            "有一天也可能會回歸生活色",
            "所以我會把這兩種理論套在一起"
        ]
    },
    
    # ── PART 4: CLOSING & IG CTA ──
    {
        "clip": c059_clip, "name": "C059", "start": 4599, "end": 5360, "color": "Green",
        "subs": [
            "我們在現場實作",
            "帶來的業績成長是80%到90%",
            "每個月大概都可以成長",
            "大概10萬到20萬左右",
            "很值得所有設計師來上的課"
        ]
    },
    {
        "clip": c058_clip, "name": "C058", "start": 29156, "end": 29443, "color": "Green",
        "subs": [
            "把這個作品的高張力",
            "引流到IG版面，吸取更多客戶"
        ]
    }
]

fps = 60.0
clips_to_append = []
for idx, cut in enumerate(ultimate_coherent_flow):
    clips_to_append.append({
        "mediaPoolItem": cut["clip"],
        "startFrame": cut["start"],
        "endFrame": cut["end"]
    })

print(f"🎬 Appending {len(clips_to_append)} ultimate coherent cuts into V1 timeline...")
append_success = media_pool.AppendToTimeline(clips_to_append)
if not append_success:
    print("❌ Failed to append clips!")
    sys.exit(1)
print("✅ Ultimate coherent cuts appended successfully!")

# ── 4. Apply Dynamic Reframing and Custom Color Coding ──────────────────────────
time.sleep(0.5)
video_items = new_timeline.GetItemListInTrack("video", 1)
for idx, item in enumerate(video_items):
    # Dynamic reframing zoom (1.0 vs 1.15) to make it premium
    zoom = 1.15 if idx % 2 == 1 else 1.0
    item.SetProperty("ZoomX", zoom)
    item.SetProperty("ZoomY", zoom)
    
    # Apply custom coloring
    color = ultimate_coherent_flow[idx]["color"]
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

# ── 6. Generate Custom SRT Subtitle File with strictly shortened lines ──────────────────────────
srt_lines = []
current_time = 0.0

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

sub_index = 1
for cut in ultimate_coherent_flow:
    duration_secs = (cut["end"] - cut["start"]) / fps
    subs = cut["subs"]
    
    sub_dur = duration_secs / len(subs)
    for txt in subs:
        start_tc = format_srt_time(current_time)
        end_tc = format_srt_time(current_time + sub_dur)
        srt_lines.append(f"{sub_index}\n{start_tc} --> {end_tc}\n<b>{txt}</b>\n\n")
        sub_index += 1
        current_time += sub_dur

# Overwrite both files
paths_to_write = [
    r"c:\TEST\scratch\Mars_Marketing_Antigravity.srt",
    r"c:\TEST\scratch\Mars_Marketing_Ultimate.srt"
]

for p in paths_to_write:
    with open(p, "w", encoding="utf-8") as f:
        f.write("".join(srt_lines))
    print(f"✅ Generated and updated SRT subtitle file at {p}")

print("\n" + "="*60)
print("🎉 AI Director Ultimate Coherent Timeline Created successfully!")
print("="*60)
print(f"Timeline: '{new_timeline.GetName()}' is active.")
print(f"Subtitle: c:\\TEST\\scratch\\Mars_Marketing_Antigravity.srt")
