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

found = False
for i in range(1, timeline_count + 1):
    tl = project.GetTimelineByIndex(i)
    if not tl:
        continue
    tl_name = tl.GetName()
    
    # Check all subtitle tracks
    sub_tracks = tl.GetTrackCount("subtitle")
    for t_idx in range(1, sub_tracks + 1):
        items = tl.GetItemListInTrack("subtitle", t_idx)
        if items:
            for idx, item in enumerate(items):
                text = item.GetName()
                if "特分立" in text or "暹羅貓" in text or "新羅貓" in text or "搭配" in text:
                    print(f"🎯 MATCH FOUND! Timeline: '{tl_name}', Subtitle Track #{t_idx}, Item #{idx+1}: '{text}'")
                    found = True

if not found:
    print("⚠️ Could not find any subtitle track in the entire project containing those terms.")
