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

timeline_count = project.GetTimelineCount()
print(f"Total Timelines in Project: {timeline_count}")

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

found_any = False
for i in range(1, timeline_count + 1):
    tl = project.GetTimelineByIndex(i)
    if not tl:
        continue
    tl_name = tl.GetName()
    sub_tracks = tl.GetTrackCount("subtitle")
    
    if sub_tracks > 0:
        items = tl.GetItemListInTrack("subtitle", 1)
        if items:
            found_any = True
            print(f"\n✨ Exporting Timeline: '{tl_name}' | Subtitle Items: {len(items)}")
            fps = float(project.GetSetting("timelineFrameRate") or 60.0)
            timeline_start = tl.GetStartFrame()
            
            srt_lines = []
            for idx, item in enumerate(items):
                start_frame = item.GetStart()
                end_frame = item.GetEnd()
                
                start_sec = (start_frame - timeline_start) / fps
                end_sec = (end_frame - timeline_start) / fps
                
                start_tc = format_srt_time(start_sec)
                end_tc = format_srt_time(end_sec)
                
                text = item.GetName()
                srt_lines.append(f"{idx+1}\n{start_tc} --> {end_tc}\n<b>{text}</b>\n\n")
            
            # Clean timeline name for filename
            clean_name = "".join([c if c.isalnum() or c in "._-" else "_" for c in tl_name])
            out_path = f"c:\\TEST\\scratch\\Exported_{clean_name}.srt"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("".join(srt_lines))
            print(f"  Saved to: {out_path}")
            print(f"  First 3 lines of subtitle track:")
            for line in srt_lines[:3]:
                print(f"    {line.strip()}")

if not found_any:
    print("⚠️ No timelines in the project have any subtitle items on track 1.")
