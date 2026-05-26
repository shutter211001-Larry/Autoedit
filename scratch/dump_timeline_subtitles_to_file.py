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

output_lines = []

output_lines.append(f"Timeline Name: {timeline.GetName()}")

# 1. Get all video items on track 1
video_items = timeline.GetItemListInTrack("video", 1)
output_lines.append(f"Total Video Items on Track 1: {len(video_items)}")

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
output_lines.append(f"Total Subtitle Items on Track 1: {len(subtitle_items)}")

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
for sub in subtitle_info:
    sub_start = sub["start"]
    sub_end = sub["end"]
    
    overlapping_clips = []
    for clip in video_clips_info:
        if not (sub_end <= clip["start"] or sub_start >= clip["end"]):
            overlapping_clips.append(clip)
    
    sub["clips"] = overlapping_clips

output_lines.append("\n" + "="*80)
output_lines.append("CORRELATED TIMELINE DETAILS")
output_lines.append("="*80)

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
    output_lines.append(f"\n🎬 Video Clip #{clip['idx']} | Name: {clip['clip_name']}")
    output_lines.append(f"   Timeline Start: {clip['start']} | End: {clip['end']} | Duration: {clip['duration']} frames")
    output_lines.append(f"   Source Start Frame: {clip['src_start']}")
    output_lines.append("   Subtitles spoken during this clip:")
    if subs:
        for s in subs:
            output_lines.append(f"     💬 {s}")
    else:
        output_lines.append("     (No subtitles)")

# Write to file in UTF-8
with open(r"c:\TEST\scratch\timeline_details_utf8.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print("✅ Dumped correlated info to c:\\TEST\\scratch\\timeline_details_utf8.txt in UTF-8 successfully!")
