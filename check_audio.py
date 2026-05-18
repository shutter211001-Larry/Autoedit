import sys

# ── Resolve 21 初始化 ────────────────────────────────────────
RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
if RESOLVE_MODULE_PATH not in sys.path:
    sys.path.append(RESOLVE_MODULE_PATH)

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
except ImportError as e:
    print(f"Error: {e}"); sys.exit(1)

project_manager = resolve.GetProjectManager()
current_project = project_manager.GetCurrentProject()

# 尋找「南區工作」時間軸
timeline_count = current_project.GetTimelineCount()
target_timeline = None
for i in range(1, timeline_count + 1):
    tl = current_project.GetTimelineByIndex(i)
    if "南區工作" in tl.GetName():
        target_timeline = tl
        break

if not target_timeline:
    print("Timeline '南區工作' not found.")
    sys.exit(0)

print(f"Analyzing Timeline: '{target_timeline.GetName()}'")

# 檢查音訊軌道 1 上的片段
audio_track_count = target_timeline.GetTrackCount("audio")
print(f"Audio track count: {audio_track_count}")

if audio_track_count > 0:
    audio_items = target_timeline.GetItemListInTrack("audio", 1)
    if audio_items:
        print(f"Found {len(audio_items)} audio clips on Track 1:")
        for idx, item in enumerate(audio_items):
            print(f"  [{idx+1}] Name: {item.GetName()}")
            mp_item = item.GetMediaPoolItem()
            if mp_item:
                print(f"      File Path: {mp_item.GetClipProperty('File Path')}")
                print(f"      Duration: {mp_item.GetClipProperty('Duration')}")
    else:
        print("No audio clips found on Track 1.")
else:
    print("No audio tracks found.")
