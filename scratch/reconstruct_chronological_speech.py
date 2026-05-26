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

video_items = timeline.GetItemListInTrack("video", 1)
subtitle_items = timeline.GetItemListInTrack("subtitle", 1)

# Collect all cuts
cuts = []
for idx, item in enumerate(video_items):
    media_pool_item = item.GetMediaPoolItem()
    if not media_pool_item:
        continue
    clip_name = media_pool_item.GetName()
    t_start = item.GetStart()
    t_end = item.GetEnd()
    duration = item.GetDuration()
    src_start = item.GetSourceStartFrame()
    src_end = src_start + duration
    
    # Get overlapping subtitles
    subs = []
    for sub in subtitle_items:
        s_start = sub.GetStart()
        s_end = sub.GetEnd()
        if not (s_end <= t_start or s_start >= t_end):
            subs.append(sub.GetName())
            
    cuts.append({
        "clip": clip_name,
        "src_start": src_start,
        "src_end": src_end,
        "duration": duration,
        "subs": subs
    })

# Group and sort by clip name and source start frame
clips_dict = {}
for c in cuts:
    if c["clip"] not in clips_dict:
        clips_dict[c["clip"]] = []
    clips_dict[c["clip"]].append(c)

for name in sorted(clips_dict.keys()):
    print(f"\n==================================================")
    print(f"🎥 CLIP: {name} (Chronological Sequence)")
    print(f"==================================================")
    sorted_cuts = sorted(clips_dict[name], key=lambda x: x["src_start"])
    for idx, c in enumerate(sorted_cuts):
        subs_str = " / ".join(c["subs"])
        print(f"  [{idx+1}] Source Frame: {c['src_start']} -> {c['src_end']} | Duration: {c['duration']} f")
        print(f"      💬 Text: {subs_str}")
