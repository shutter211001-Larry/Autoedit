import sys
import time

RESOLVE_MODULE_PATH = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
sys.path.append(RESOLVE_MODULE_PATH)

def sync_color_grades():
    try:
        import DaVinciResolveScript as dvr_script
        resolve = dvr_script.scriptapp("Resolve")
    except ImportError as e:
        print(f"Cannot load DaVinciResolveScript: {e}")
        sys.exit(1)

    project_manager = resolve.GetProjectManager()
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        print("❌ Error: No active project found!")
        sys.exit(1)
        
    timeline = current_project.GetCurrentTimeline()
    if not timeline:
        print("❌ Error: No active timeline found!")
        sys.exit(1)
        
    video_items = timeline.GetItemListInTrack("video", 1)
    if not video_items or len(video_items) <= 1:
        print("❌ Error: Video Track 1 does not contain enough clips to sync!")
        sys.exit(1)
        
    source_clip = video_items[0]
    target_clips = list(video_items[1:])
    
    print(f"🎨 Starting In-Place Color Grade Sync...")
    print(f"   👉 Source Master Clip (Clip #1): '{source_clip.GetName()}'")
    print(f"   👉 Targets to Sync: {len(target_clips)} clips")
    
    try:
        # 直接調用 CopyGrades API
        success = source_clip.CopyGrades(target_clips)
        if success:
            print("   👑 SUCCESS: Color Grade successfully cloned from Clip #1 to all other clips on the timeline!")
            # 雙重頁面跳轉刷新 GUI，確保調色面板與監視器更新
            resolve.OpenPage("media")
            time.sleep(0.2)
            resolve.OpenPage("color")
            time.sleep(0.3)
            resolve.OpenPage("edit")
            time.sleep(0.2)
            print("🎬 All Done! Open your DaVinci Resolve Timeline to check the synced premium colors!")
        else:
            print("❌ Error: DaVinci Resolve CopyGrades API returned False.")
    except Exception as e:
        print(f"❌ Error during color sync: {e}")

if __name__ == "__main__":
    sync_color_grades()
