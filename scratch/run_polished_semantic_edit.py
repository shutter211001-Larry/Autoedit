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

# ── 1. Create New Timeline "Mars_智能精剪行銷版" ──────────────────────────
new_timeline_name = "Mars_智能精剪行銷版"

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
        tl.SetName(f"Mars_精剪舊備份_{int(time.time())}")
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

c056_clip = find_clip(root_folder, "C056")
c057_clip = find_clip(root_folder, "C057")
c058_clip = find_clip(root_folder, "C058")
c059_clip = find_clip(root_folder, "C059")
bgm_clip = find_clip(root_folder, "Only Little")

if not all([c056_clip, c057_clip, c058_clip, c059_clip]):
    print("❌ Failed to locate all target video clips in Master pool!")
    sys.exit(1)

# ── 3. Define Cleaned Marketing Cuts (Eliminated all repetitions and stutters) ──────────────────────────
polished_flow = [
    # --- HOOK & INTRO ---
    {"clip": c058_clip, "name": "C058", "start": 28203, "end": 28290, "subs": ["大家好我是Mars，我們這堂課呢"]},
    {"clip": c058_clip, "name": "C058", "start": 28413, "end": 28519, "subs": ["分別是暹羅貓漂色"]},
    {"clip": c058_clip, "name": "C058", "start": 28575, "end": 28686, "subs": ["另外一個是不漂的霧感"]},
    
    # --- BUSINESS HOOK ---
    {"clip": c059_clip, "name": "C059", "start": 4599, "end": 4878, "subs": ["我們在現場實作帶來的業績的成長是", "80%到90%"]},
    {"clip": c059_clip, "name": "C059", "start": 4963, "end": 5164, "subs": ["每個月大概都可以成長", "大概10萬到20萬左右"]},
    {"clip": c059_clip, "name": "C059", "start": 5203, "end": 5360, "subs": ["很值得所有設計師來上的一堂課"]},
    
    # --- BRAND TRACTION CONCEPT ---
    {"clip": c058_clip, "name": "C058", "start": 28873, "end": 29042, "subs": ["暹羅貓給我的是我的版面引流的張力，90%的霧感髮色"]},
    {"clip": c058_clip, "name": "C058", "start": 29156, "end": 29443, "subs": ["90%的霧感髮色，其實都是依靠我的IG，版面的高張力引進來的"]},
    
    # --- SUBJECT 1: SIAM BLOCK COLORING & SOLUTIONS ---
    {"clip": c056_clip, "name": "C056", "start": 759, "end": 987, "subs": ["那這次課程呢，我們大概會解決幾個要點：第一個"]},
    {"clip": c058_clip, "name": "C058", "start": 665, "end": 764, "subs": ["暹羅貓的髮色"]},
    {"clip": c058_clip, "name": "C058", "start": 2124, "end": 2302, "subs": ["做出來的尾巴的那個黑色很生硬，不管是在拍照或是肉眼看的時候，硬線都是非常明顯"]},
    {"clip": c058_clip, "name": "C058", "start": 2574, "end": 2667, "subs": ["這次的課程要幫所有的設計師"]},
    {"clip": c058_clip, "name": "C058", "start": 2758, "end": 2866, "subs": ["怎麼去做到淡化的效果"]},
    {"clip": c058_clip, "name": "C058", "start": 3011, "end": 3155, "subs": ["黑色、主色，是要怎麼能夠融合在一起"]},
    
    # --- CORE FORMULATION METHOD ---
    {"clip": c058_clip, "name": "C058", "start": 3843, "end": 3922, "subs": ["區塊的公式配方，我需要飽和度高的時候"]},
    {"clip": c058_clip, "name": "C058", "start": 20981, "end": 21486, "subs": ["我需要飽和度高的時候，我的歐系染膏拿出來，我能夠做到飽和，但我需要淡化的時候，我的歐系染膏同時，也能做到一樣的效果"]},
    {"clip": c058_clip, "name": "C058", "start": 3963, "end": 4115, "subs": ["也能做到一樣的效果，做出很多不一樣的色彩的感覺"]},
    
    # --- SUBJECT 2: EFFICIENT CUT & BLEACH DETAILS ---
    {"clip": c056_clip, "name": "C056", "start": 1145, "end": 1985, "subs": ["15分鐘的高效裁剪，讓大家在現場的時候，翻桌率是能夠提升的。那在漂髮的部分呢，我們這次會帶大家去看如何漂到乾淨透亮的程度，那我們去做上色的時候，讓它更有光澤。"]},
    
    # --- SUBJECT 3: NO-BLEACH MATTE & GRAY COVERAGE ---
    {"clip": c057_clip, "name": "C057", "start": 140, "end": 897, "subs": ["第二個主題呢，我們這次會做一個不漂不退的霧感，那依照2025的趨勢的延伸，那我們這次實現所謂的一碗通刷，不退不漂，如何去做到最灰感最霧感的顏色"]},
    {"clip": c057_clip, "name": "C057", "start": 1726, "end": 1955, "subs": ["多段髮色呈現霧感、透感及灰感，針對白髮呢"]},
    {"clip": c059_clip, "name": "C059", "start": 1402, "end": 1906, "subs": ["我用最簡單的配方比例，去做到能夠實現白髮既有霧透感，它也能蓋到70% 80%的程度"]},
    {"clip": c057_clip, "name": "C057", "start": 1582, "end": 1714, "subs": ["我們只需要一碗就能夠搞定"]},
    
    # --- UNIFIED THEORIES & CTA ---
    {"clip": c058_clip, "name": "C058", "start": 23947, "end": 24796, "subs": ["你做霧感色系的客人，他終究有一天，他也可能會需要做到漂髮；你做漂髮的客人，他也有一天可能會回歸到這種霧感的生活色，所以我會把這兩種的理論，把它套在一起"]},
    {"clip": c058_clip, "name": "C058", "start": 26350, "end": 26446, "subs": ["在課堂上實作展現給各位看"]},
    {"clip": c058_clip, "name": "C058", "start": 26523, "end": 26597, "subs": ["用很精準的理論去分析出來"]},
    {"clip": c058_clip, "name": "C058", "start": 26608, "end": 26665, "subs": ["你的消費者應該更適合哪一種"]},
    {"clip": c058_clip, "name": "C058", "start": 26724, "end": 26842, "subs": ["讓所有的設計師能夠更好的運用"]}
]

fps = 60.0
clips_to_append = []
for idx, cut in enumerate(polished_flow):
    clips_to_append.append({
        "mediaPoolItem": cut["clip"],
        "startFrame": cut["start"],
        "endFrame": cut["end"]
    })

print(f"🎬 Appending {len(clips_to_append)} polished semantic cuts into V1 timeline...")
append_success = media_pool.AppendToTimeline(clips_to_append)
if not append_success:
    print("❌ Failed to append clips!")
    sys.exit(1)
print("✅ Polished semantic cuts appended successfully!")

# ── 4. Apply Dynamic Reframing and Color Coding ──────────────────────────
time.sleep(0.5)
video_items = new_timeline.GetItemListInTrack("video", 1)
for idx, item in enumerate(video_items):
    # Alternating zooms to prevent jump cuts and look premium
    zoom = 1.14 if idx % 2 == 1 else 1.0
    item.SetProperty("ZoomX", zoom)
    item.SetProperty("ZoomY", zoom)
    
    # Section-based color coding
    if idx < 3:
        item.SetClipColor("Rose")    # Hook/Intro
    elif idx < 6:
        item.SetClipColor("Orange")  # Business Hook / Results
    elif idx < 17:
        item.SetClipColor("Teal")    # Subject 1 & Formulas
    elif idx < 22:
        item.SetClipColor("Pink")    # Subject 2 & 3
    else:
        item.SetClipColor("Green")   # Unified Theories & CTA
print("✅ Reframing zoom and color coding applied!")

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

# ── 6. Generate Polished SRT Subtitle File ──────────────────────────
srt_lines = []
current_time = 0.0

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

sub_index = 1
for cut in polished_flow:
    duration_secs = (cut["end"] - cut["start"]) / fps
    subs = cut["subs"]
    if not subs:
        current_time += duration_secs
        continue
        
    sub_dur = duration_secs / len(subs)
    for txt in subs:
        start_tc = format_srt_time(current_time)
        end_tc = format_srt_time(current_time + sub_dur)
        srt_lines.append(f"{sub_index}\n{start_tc} --> {end_tc}\n<b>{txt}</b>\n\n")
        sub_index += 1
        current_time += sub_dur

srt_path = r"c:\TEST\scratch\Mars_Marketing_Polished.srt"
with open(srt_path, "w", encoding="utf-8") as f:
    f.write("".join(srt_lines))

print(f"✅ Generated stutter-cleaned SRT subtitle file at {srt_path}")
print("\n" + "="*60)
print("🎉 Smart Polished Semantic Editing Timeline Created Successfully!")
print("="*60)
print(f"Timeline: '{new_timeline.GetName()}' is now active.")
print(f"Subtitles: c:\\TEST\\scratch\\Mars_Marketing_Polished.srt")
