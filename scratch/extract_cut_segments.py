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
print(f"Total Video Items: {len(video_items)}")

with open(r"c:\TEST\scratch\video_segments.txt", "w", encoding="utf-8") as f:
    f.write("Index | Clip Name | Timeline Start | Timeline End | Duration | Source Start Frame | Source End Frame\n")
    for idx, item in enumerate(video_items):
        media_pool_item = item.GetMediaPoolItem()
        clip_name = media_pool_item.GetName() if media_pool_item else "NoMediaPoolItem"
        t_start = item.GetStart()
        t_end = item.GetEnd()
        duration = item.GetDuration()
        
        # Get source frame properties
        src_start = item.GetSourceStartFrame()
        # Source End is start + duration (since DaVinci Resolve is inclusive/exclusive, end frame is src_start + duration)
        src_end = src_start + duration
        
        # Get associated subtitles
        subtitles = []
        subtitle_items = timeline.GetItemListInTrack("subtitle", 1)
        for sub in subtitle_items:
            s_start = sub.GetStart()
            s_end = sub.GetEnd()
            if not (s_end <= t_start or s_start >= t_end):
                subtitles.append(sub.GetName())
                
        subs_str = " / ".join(subtitles)
        f.write(f"{idx+1} | {clip_name} | {t_start} | {t_end} | {duration} | {src_start} | {src_end} | Subs: {subs_str}\n")

print("✅ Dumped all video segments with source frames and subtitles to c:\\TEST\\scratch\\video_segments.txt")
