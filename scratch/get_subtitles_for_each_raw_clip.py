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

# Group subtitles by raw clip name
raw_clip_subs = {
    "A001_03271229_C055.mov": [],
    "A001_03271229_C056.mov": [],
    "A001_03271230_C057.mov": [],
    "A001_03271231_C058.mov": [],
    "A001_03271242_C059.mov": []
}

# Also gather clips information on timeline
for item in video_items:
    media_pool_item = item.GetMediaPoolItem()
    if not media_pool_item:
        continue
    clip_name = media_pool_item.GetName()
    if clip_name not in raw_clip_subs:
        continue
        
    start_frame = item.GetStart()
    end_frame = item.GetEnd()
    
    # Find all subtitles that overlap with this timeline item
    item_subs = []
    for sub in subtitle_items:
        sub_start = sub.GetStart()
        sub_end = sub.GetEnd()
        
        # Check overlap
        if not (sub_end <= start_frame or sub_start >= end_frame):
            item_subs.append(sub.GetName())
            
    raw_clip_subs[clip_name].extend(item_subs)

# Clean up duplicates while preserving order
for clip_name in raw_clip_subs:
    seen = set()
    unique_subs = []
    for sub in raw_clip_subs[clip_name]:
        if sub not in seen:
            seen.add(sub)
            unique_subs.append(sub)
    raw_clip_subs[clip_name] = unique_subs

# Print the result
for clip_name, subs in raw_clip_subs.items():
    print(f"\n🎥 Raw Clip: {clip_name}")
    print(f"   Total unique subtitle blocks: {len(subs)}")
    for s in subs:
        print(f"     💬 {s}")
