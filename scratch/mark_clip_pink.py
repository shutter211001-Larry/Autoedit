import sys
import os

# Ensure local path is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.resolve_api import connect_to_resolve

def main():
    resolve = connect_to_resolve()
    if not resolve:
        print("❌ Cannot connect to DaVinci Resolve.")
        sys.exit(1)
        
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    if not project:
        print("❌ No active project loaded in Resolve.")
        sys.exit(1)
        
    timeline = project.GetCurrentTimeline()
    if not timeline or timeline.GetName() != "AI_Exhibition_25s":
        print("❌ Timeline 'AI_Exhibition_25s' is not active.")
        sys.exit(1)
        
    placed_clips = timeline.GetItemListInTrack("video", 1) or []
    if len(placed_clips) < 6:
        print(f"❌ Not enough clips on timeline (found {len(placed_clips)}).")
        sys.exit(1)
        
    # Mark clip at index 5 as 'Pink' for testing reroll
    target_clip = placed_clips[5]
    old_name = target_clip.GetName()
    success = target_clip.SetClipColor("Pink")
    
    if success:
        print(f"🎉 Success! Marked clip #{6} '{old_name}' as Pink on Video Track 1.")
    else:
        print("❌ Failed to set clip color in Resolve.")

if __name__ == "__main__":
    main()
