import os
import shutil

ROOT = r"c:\TEST"

# 1. 建立目標資料夾
dirs = ["config", "core", "diagnostics", "legacy", "cache"]
for d in dirs:
    path = os.path.join(ROOT, d)
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

# 2. 定義要移到 legacy/ 的檔案名單 (凡是舊版剪輯、測試、分析等)
legacy_files = [
    "ai_tagger.py", "ai_tagger_full.py", "auto_beat_marker.py",
    "auto_edit_30s.py", "auto_edit_cinematic.py", "check_audio.py",
    "check_clip_start.py", "clip_properties_dump.txt", "create_semantic_timeline.py",
    "cue_sheet.md", "diag_detailed_tracks.py", "diag_timelines.py",
    "direction_stability_analyzer.py", "edit_active_timeline.py",
    "edit_semantic_promo.py", "edit_teacher_promo.py", "export_thumbnails.py",
    "fix_timeline_mess.py", "inspect_append.py", "inspect_append_sequential.py",
    "inspect_append_simple.py", "list_audience_clips.py", "pre_cache_profiles.py",
    "print_all_clip_properties.py", "print_logs_header.py", "reapply_zooms.py",
    "reimport_assets.py", "reset_flags.py", "resolve_api_explorer.py",
    "resolve_api_map.txt", "resolve_new_project.py",
    "run_cinematic_auto_edit.py", "run_event_highlight_edit.py", "run_nanqu_edit.py",
    "run_nanqu_final_mv.py", "run_nanqu_force_edit.py", "run_nanqu_force_edit_fixed.py",
    "run_nanqu_mv_edit.py", "search_logs.py", "smart_asset_selector.py",
    "stability_analyzer_hyper_fast.py", "sync_grades.py", "test_resolution.py",
    "test_zoom.py", "Sam.srt", "Sam_corrected.srt", ".cv_edit_cache.json"
]

# 3. 定義要移到 diagnostics/ 的診斷測試名單
diagnostics_files = [
    "diagnose_ai2.py", "resolve_api_test.py", "test_copy_grades.py"
]

# 4. 定義要移到 cache/ 的快取檔案
cache_files = [
    ".cv_profile_cache.json"
]

# 執行移動
def move_files(file_list, dest_dir):
    for f in file_list:
        src = os.path.join(ROOT, f)
        dest = os.path.join(ROOT, dest_dir, f)
        if os.path.exists(src):
            try:
                shutil.move(src, dest)
                print(f"Moved {f} -> {dest_dir}/")
            except Exception as e:
                print(f"Error moving {f}: {e}")

print("--- Archiving to legacy/ ---")
move_files(legacy_files, "legacy")

print("--- Archiving to diagnostics/ ---")
move_files(diagnostics_files, "diagnostics")

print("--- Archiving to cache/ ---")
move_files(cache_files, "cache")

print("Reorganization of legacy files completed!")
