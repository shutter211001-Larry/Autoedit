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

# ── 1. Create New Timeline "Mars_行銷語意重剪版" ──────────────────────────
new_timeline_name = "Mars_行銷語意重剪版"

# Delete existing same-name timeline if any to start clean
timeline_count = project.GetTimelineCount()
for i in range(1, timeline_count + 1):
    tl = project.GetTimelineByIndex(i)
    if tl and tl.GetName() == new_timeline_name:
        print(f"⚠️ Timeline '{new_timeline_name}' already exists, deleting old one...")
        # Resolve does not have delete timeline API, so we rename it and empty it
        project.SetCurrentTimeline(tl)
        for track_type in ["video", "audio", "subtitle"]:
            tc = tl.GetTrackCount(track_type)
            for t_idx in range(1, tc + 1):
                items = tl.GetItemListInTrack(track_type, t_idx)
                if items:
                    tl.DeleteClips(items)
        tl.SetName(f"Mars_舊備份_{int(time.time())}")
        break

print(f"🆕 Creating new blank timeline: '{new_timeline_name}'...")
new_timeline = media_pool.CreateEmptyTimeline(new_timeline_name)
if not new_timeline:
    print("❌ Failed to create timeline!")
    sys.exit(1)

print(f"🎬 New timeline created successfully: '{new_timeline.GetName()}'")
project.SetCurrentTimeline(new_timeline)

# GUI Refresh
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

c056_clip = find_clip(root_folder, "C056")
c057_clip = find_clip(root_folder, "C057")
c058_clip = find_clip(root_folder, "C058")
c059_clip = find_clip(root_folder, "C059")
bgm_clip = find_clip(root_folder, "Only Little")

if not all([c056_clip, c057_clip, c058_clip, c059_clip]):
    print("❌ Failed to locate all target video clips in Master pool!")
    sys.exit(1)

# ── 3. Define Reordered Marketing Cuts (Pain Point -> Solution -> Benefit) ──────────────────────────
# Using exact source frame bounds extracted from Timeline 1
marketing_flow = [
    # === SECTION 1: HOOK & PAIN POINTS ===
    {"clip": c058_clip, "name": "C058", "start": 28203, "end": 28290, "subs": ["大家好我是Mars", "我們這堂課呢"]},
    {"clip": c058_clip, "name": "C058", "start": 2124, "end": 2302, "subs": ["做出來的尾巴的那個黑色很生硬", "不管是在拍照或是肉眼看的時候", "硬線都是非常明顯"]},
    
    # === SECTION 2: SOLUTIONS ===
    {"clip": c056_clip, "name": "C056", "start": 759, "end": 987, "subs": ["那這次課程呢", "我們大概會解決幾個要點", "第一個"]},
    {"clip": c056_clip, "name": "C056", "start": 1145, "end": 1985, "subs": ["15分鐘的高效裁剪", "讓大家在現場的時候", "翻桌率是能夠提升的", "那在漂髮的部分呢", "我們這次會帶大家", "去看如何漂到乾淨透亮的程度", "那我們去做上色的時候", "讓它更有光澤"]},
    {"clip": c057_clip, "name": "C057", "start": 140, "end": 897, "subs": ["第二個主題呢", "我們這次會做一個不漂不退的霧感", "那依照2025的趨勢的延伸", "那我們這次實現所謂的一碗通刷", "不退不漂", "如何去做到最灰感最霧感的顏色"]},
    {"clip": c058_clip, "name": "C058", "start": 3843, "end": 3922, "subs": ["區塊的公式配方", "我需要飽和度高的時候"]},
    {"clip": c058_clip, "name": "C058", "start": 20981, "end": 21486, "subs": ["我需要飽和度高的時候", "我的歐系染膏拿出來", "我能夠做到飽和", "但我需要淡化的時候", "我的歐系染膏同時", "也能做到一樣的效果"]},
    {"clip": c059_clip, "name": "C059", "start": 1044, "end": 1098, "subs": ["針對白髮呢", "我用最簡單的配方比例"]},
    {"clip": c059_clip, "name": "C059", "start": 1402, "end": 1906, "subs": ["我用最簡單的配方比例", "去做到能夠實現", "白髮既有霧透感", "它也能蓋到70% 80%的程度"]},
    {"clip": c057_clip, "name": "C057", "start": 1582, "end": 1714, "subs": ["我們只需要一碗就能夠搞定"]},
    
    # === SECTION 3: BENEFITS & CTA ===
    {"clip": c059_clip, "name": "C059", "start": 4599, "end": 4878, "subs": ["我們在現場實作帶來的業績的成長是", "80%到90%"]},
    {"clip": c059_clip, "name": "C059", "start": 4963, "end": 5164, "subs": ["每個月大概都可以成長", "大概10萬到20萬左右"]},
    {"clip": c059_clip, "name": "C059", "start": 5203, "end": 5360, "subs": ["很值得所有設計師來上的一堂課"]},
    {"clip": c058_clip, "name": "C058", "start": 26724, "end": 26842, "subs": ["你的消費者應該更適合哪一種", "讓所有的設計師能夠更好的運用"]},
    {"clip": c058_clip, "name": "C058", "start": 24948, "end": 25053, "subs": ["讓所有的設計師能夠更好的運用"]}
]

fps = 60.0 # Mars clips are 60fps!
clips_to_append = []
for idx, cut in enumerate(marketing_flow):
    clips_to_append.append({
        "mediaPoolItem": cut["clip"],
        "startFrame": cut["start"],
        "endFrame": cut["end"]
    })

print(f"🎬 Appending {len(clips_to_append)} semantic cuts into V1 timeline...")
append_success = media_pool.AppendToTimeline(clips_to_append)
if not append_success:
    print("❌ Failed to append clips!")
    sys.exit(1)
print("✅ Semantic cuts appended successfully!")

# ── 4. Apply Re-framing and Color Coding ──────────────────────────
time.sleep(0.5)
video_items = new_timeline.GetItemListInTrack("video", 1)
for idx, item in enumerate(video_items):
    # Alternating zooms to make jump cuts feel like dynamic intentional reframing (1.0 vs 1.15)
    zoom = 1.15 if idx % 2 == 1 else 1.0
    item.SetProperty("ZoomX", zoom)
    item.SetProperty("ZoomY", zoom)
    
    # Color code sections
    if idx < 2:
        item.SetClipColor("Rose") # Pain points in Rose/Pink
    elif idx < 10:
        item.SetClipColor("Teal") # Solutions in Teal
    else:
        item.SetClipColor("Green") # Benefits in Green
print("✅ Alternating zoom and Rose/Teal/Green color coding applied successfully!")

# ── 5. Overlay Background Music (BGM) ──────────────────────────
if bgm_clip:
    timeline_start = new_timeline.GetStartFrame()
    timeline_end = new_timeline.GetEndFrame()
    total_duration_frames = timeline_end - timeline_start
    print(f"⏱️ Video Total Duration: {total_duration_frames / fps:.2f} seconds ({total_duration_frames} frames)")
    
    # Ensure Track A2 exists
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

# ── 6. Generate Mapped SRT File ──────────────────────────
# Let's write the new SRT file based on cumulative cut durations
srt_lines = []
current_time = 0.0

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

sub_index = 1
for cut in marketing_flow:
    duration_secs = (cut["end"] - cut["start"]) / fps
    subs = cut["subs"]
    if not subs:
        current_time += duration_secs
        continue
        
    # Split the duration evenly among the subtitle blocks in this cut
    sub_dur = duration_secs / len(subs)
    for txt in subs:
        start_tc = format_srt_time(current_time)
        end_tc = format_srt_time(current_time + sub_dur)
        srt_lines.append(f"{sub_index}\n{start_tc} --> {end_tc}\n<b>{txt}</b>\n\n")
        sub_index += 1
        current_time += sub_dur

srt_path = r"c:\TEST\scratch\Mars_Marketing_Semantic.srt"
with open(srt_path, "w", encoding="utf-8") as f:
    f.write("".join(srt_lines))

print(f"✅ Generated marketing aligned SRT subtitle file at {srt_path}")
print("\n" + "="*60)
print("🎉 ALL SEMANTIC EDITING OPERATIONS COMPLETED SUCCESSFULLY!")
print("="*60)
print(f"Timeline: '{new_timeline.GetName()}' is now live in DaVinci Resolve.")
print("The timeline has been structured into:")
print("  - Pink (Rose): Hook & Pain Points")
print("  - Teal: Core Solutions (Cutting, Bleaching, Coloring, Gray coverage)")
print("  - Green: Marketing Benefits & Revenue results")
print(f"Subtitle: Import {srt_path} to complete the video!")
