import sys
import os

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
timeline = project.GetTimelineByIndex(1) # Timeline 1

print(f"Timeline Name: {timeline.GetName()}")

# 1. Get all video items on track 1
video_items = timeline.GetItemListInTrack("video", 1)
print(f"Total Video Items on Track 1: {len(video_items)}")

video_clips_info = []
for idx, item in enumerate(video_items):
    media_pool_item = item.GetMediaPoolItem()
    clip_name = media_pool_item.GetName() if media_pool_item else "NoMediaPoolItem"
    start_frame = item.GetStart()
    end_frame = item.GetEnd()
    duration = item.GetDuration()
    try:
        src_start = item.GetSourceStartFrame()
    except Exception:
        src_start = "N/A"
    
    video_clips_info.append({
        "idx": idx + 1,
        "name": item.GetName(),
        "clip_name": clip_name,
        "start": start_frame,
        "end": end_frame,
        "duration": duration,
        "src_start": src_start,
        "item": item
    })

# 2. Get all subtitle items on track 1
subtitle_items = timeline.GetItemListInTrack("subtitle", 1)
print(f"Total Subtitle Items on Track 1: {len(subtitle_items)}")

subtitle_info = []
for idx, item in enumerate(subtitle_items):
    start_frame = item.GetStart()
    end_frame = item.GetEnd()
    duration = item.GetDuration()
    text = item.GetName() # This is the subtitle text
    
    subtitle_info.append({
        "idx": idx + 1,
        "text": text,
        "start": start_frame,
        "end": end_frame,
        "duration": duration
    })

# 3. Correlate subtitles with video clips
# For each subtitle, see which video clip it overlaps with on the timeline
for sub in subtitle_info:
    sub_start = sub["start"]
    sub_end = sub["end"]
    
    overlapping_clips = []
    for clip in video_clips_info:
        # Check overlap
        if not (sub_end <= clip["start"] or sub_start >= clip["end"]):
            overlapping_clips.append(clip)
    
    sub["clips"] = overlapping_clips

# Print the correlated information
print("\n" + "="*80)
print("CORRELATED TIMELINE DETAILS")
print("="*80)

# Let's also group subtitles by video clip
clip_to_subs = {}
for clip in video_clips_info:
    clip_key = f"{clip['idx']}_{clip['clip_name']}"
    clip_to_subs[clip_key] = []

for sub in subtitle_info:
    for clip in sub["clips"]:
        clip_key = f"{clip['idx']}_{clip['clip_name']}"
        clip_to_subs[clip_key].append(sub["text"])

# Print grouped by clip
for clip in video_clips_info:
    clip_key = f"{clip['idx']}_{clip['clip_name']}"
    subs = clip_to_subs[clip_key]
    print(f"\n🎬 Video Clip #{clip['idx']} | Name: {clip['clip_name']}")
    print(f"   Timeline Start: {clip['start']} | End: {clip['end']} | Duration: {clip['duration']} frames")
    print(f"   Source Start Frame: {clip['src_start']}")
    print("   Subtitles spoken during this clip:")
    if subs:
        for s in subs:
            print(f"     💬 {s}")
    else:
        print("     (No subtitles)")
