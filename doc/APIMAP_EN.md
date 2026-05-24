# 🎬 DaVinci Resolve 21 API Method Reference & Troubleshooting Guide (APIMAP - EN)

This document lists all available DaVinci Resolve 21 (Studio) Python API classes and methods, providing practical solutions for scripting limitations and bugs encountered in automated editing workflows.

---

## 📂 DaVinci Resolve API Methods List

### 1. `resolve` Global Entry Class (24 Methods)
```text
DeleteLayoutPreset, ExportBurnInPreset, ExportLayoutPreset, ExportRenderPreset, Fusion, GetCurrentPage, GetFairlightPresets, GetKeyframeMode, GetMediaStorage, GetProductName, GetProjectManager, GetVersion, GetVersionString, ImportBurnInPreset, ImportLayoutPreset, ImportRenderPreset, LoadLayoutPreset, OpenPage, Print, Quit, SaveLayoutPreset, SetHighPriority, SetKeyframeMode, UpdateLayoutPreset
```

### 2. `project_manager` Project Manager Class (29 Methods)
```text
ArchiveProject, CloseProject, CreateCloudProject, CreateFolder, CreateProject, DeleteFolder, DeleteProject, ExportProject, GetCurrentDatabase, GetCurrentFolder, GetCurrentProject, GetDatabaseList, GetFolderListInCurrentFolder, GetFoldersInCurrentFolder, GetProjectLastModifiedTime, GetProjectListInCurrentFolder, GetProjectsInCurrentFolder, GotoParentFolder, GotoRootFolder, ImportCloudProject, ImportProject, LoadCloudProject, LoadProject, OpenFolder, Print, RestoreCloudProject, RestoreProject, SaveProject, SetCurrentDatabase
```

### 3. `current_project` Active Project Class (47 Methods)
```text
AddColorGroup, AddRenderJob, ApplyFairlightPresetToCurrentTimeline, DeleteAllRenderJobs, DeleteColorGroup, DeleteRenderJob, DeleteRenderPreset, ExportCurrentFrameAsStill, GetColorGroupsList, GetCurrentRenderFormatAndCodec, GetCurrentRenderMode, GetCurrentTimeline, GetGallery, GetMediaPool, GetName, GetPresetList, GetPresets, GetQuickExportRenderPresets, GetRenderCodecs, GetRenderFormats, GetRenderJobList, GetRenderJobStatus, GetRenderJobs, GetRenderPresetList, GetRenderPresets, GetRenderResolutions, GetSetting, GetTimelineByIndex, GetTimelineCount, GetUniqueId, InsertAudioToCurrentTrackAtPlayhead, IsRenderingInProgress, LoadBurnInPreset, LoadRenderPreset, Print, RefreshLUTList, RenderWithQuickExport, SaveAsNewRenderPreset, SetCurrentRenderFormatAndCodec, SetCurrentRenderMode, SetCurrentTimeline, SetName, SetPreset, SetRenderSettings, SetSetting, StartRendering, StopRendering
```

### 4. `media_pool` Media Pool Class (28 Methods)
```text
AddSubFolder, AppendToTimeline, AutoSyncAudio, CreateEmptyTimeline, CreateStereoClip, CreateTimelineFromClips, DeleteClipMattes, DeleteClips, DeleteFolders, DeleteTimelines, ExportMetadata, GetClipMatteList, GetCurrentFolder, GetRootFolder, GetSelectedClips, GetTimelineMatteList, GetUniqueId, ImportFolderFromFile, ImportMedia, ImportTimelineFromFile, MoveClips, MoveFolders, Print, RefreshFolders, RelinkClips, SetCurrentFolder, SetSelectedClip, UnlinkClips
```

### 5. `folder` (e.g. `root_folder`) Media Folder Class (11 Methods)
```text
ClearTranscription, Export, GetClipList, GetClips, GetIsFolderStale, GetName, GetSubFolderList, GetSubFolders, GetUniqueId, Print, TranscribeAudio
```

### 6. `current_timeline` Timeline Class (60 Methods)
```text
AddMarker, AddTrack, AnalyzeDolbyVision, ClearMarkInOut, ConvertTimelineToStereo, CreateCompoundClip, CreateFusionClip, CreateSubtitlesFromAudio, DeleteClips, DeleteMarkerAtFrame, DeleteMarkerByCustomData, DeleteMarkersByColor, DeleteTrack, DetectSceneCuts, DuplicateTimeline, Export, GetCurrentClipThumbnailImage, GetCurrentTimecode, GetCurrentVideoItem, GetEndFrame, GetIsTrackEnabled, GetIsTrackLocked, GetItemListInTrack, GetItemsInTrack, GetMarkInOut, GetMarkerByCustomData, GetMarkerCustomData, GetMarkers, GetMediaPoolItem, GetName, GetNodeGraph, GetSetting, GetStartFrame, GetStartTimecode, GetTrackCount, GetTrackName, GetTrackSubType, GetUniqueId, GetVoiceIsolationState, GrabAllStills, GrabStill, ImportIntoTimeline, InsertFusionCompositionIntoTimeline, InsertFusionGeneratorIntoTimeline, InsertFusionTitleIntoTimeline, InsertGeneratorIntoTimeline, InsertOFXGeneratorIntoTimeline, InsertTitleIntoTimeline, Print, SetClipsLinked, SetCurrentTimecode, SetMarkInOut, SetName, SetSetting, SetStartTimecode, SetTrackEnable, SetTrackLock, SetTrackName, SetVoiceIsolationState, UpdateMarkerCustomData
```

---

## 🔧 Core API Syntax & Call Blueprints

This section provides AI agents with precise scripting syntax templates for the most commonly used DaVinci Resolve Python APIs to prevent syntax errors and incorrect arguments.

### 1. Project & Timeline Initialization (Lifecycle)
```python
# 1. Access active project & media pool
project_manager = resolve.GetProjectManager()
current_project = project_manager.GetCurrentProject()
media_pool = current_project.GetMediaPool()

# 2. Create a fresh empty timeline
timeline_name = "AI_Auto_Edit"
timeline = media_pool.CreateEmptyTimeline(timeline_name)

# 3. Retrieve timeline bounds and settings
timeline_start = timeline.GetStartFrame() # Typically returns absolute index 86400 (representing 01:00:00:00)
timeline_end = timeline.GetEndFrame()
fps = float(current_project.GetSetting("timelineFrameRate")) # Retrieve framerate float
```

### 2. Media Search & Import
```python
# 1. Recursively search for a MediaPoolItem in subfolders
def find_clip_by_name(folder, name_query):
    for clip in folder.GetClipList() or []:
        if name_query.lower() in clip.GetName().lower():
            return clip
    for sub_folder in folder.GetSubFolderList() or []:
        res = find_clip_by_name(sub_folder, name_query)
        if res:
            return res
    return None

# 2. Import local files recursively into a media folder
root_folder = media_pool.GetRootFolder()
media_pool.SetCurrentFolder(root_folder)
imported_clips = media_pool.ImportMedia(["C:\\videos\\clip_01.mp4", "C:\\music\\bgm.mp3"])
```

### 3. Timeline Appending & Sewing
```python
# 1. Contiguous sequential append (most stable video sewing method)
clips_to_append = [
    {
        "mediaPoolItem": clip1_item,
        "startFrame": 0,          # Relative start frame of clip
        "endFrame": 120           # Relative end frame (120 frames total)
    },
    {
        "mediaPoolItem": clip2_item,
        "startFrame": 24,
        "endFrame": 72
    }
]
# Appends sequentially to the tail of Video Track 1
media_pool.AppendToTimeline(clips_to_append)

# 2. Targeted append to specific coordinate (useful for BGM or outro logo overlays)
bgm_append_data = [{
    "mediaPoolItem": bgm_clip_item,
    "startFrame": int(start_sec * fps),
    "endFrame": int(end_sec * fps),
    "recordFrame": int(timeline_start),  # Absolute timeline coordinate (86400)
    "trackIndex": 2,                     # Audio Track 2
    "mediaType": 2                       # 1 = Video, 2 = Audio
}]
media_pool.AppendToTimeline(bgm_append_data)
```

### 4. Timeline Query & Deletion
```python
# 1. Retrieve all items in a specific track (indices are 1-based integers)
placed_video_clips = timeline.GetItemListInTrack("video", 1) or [] # V1 track
placed_audio_clips = timeline.GetItemListInTrack("audio", 2) or [] # A2 track

# 2. Delete clips physically from the timeline
timeline.DeleteClips(placed_audio_clips)
```

### 5. Clip Properties & Color Tagging
```python
# Fetch V1 track and modify geometry settings
placed_clips = timeline.GetItemListInTrack("video", 1)
if placed_clips:
    clip_item = placed_clips[0]
    
    # Set static sizing and rotations (adding a 1.08x zoom buffer to crop black border wiggles)
    clip_item.SetProperty("ZoomX", 1.08)
    clip_item.SetProperty("ZoomY", 1.08)
    clip_item.SetProperty("RotationAngle", 4.0)
    
    # Tag clip visual color (Navy / Teal / Yellow / Orange / Red / Pink)
    clip_item.SetClipColor("Teal")
```

### 6. Timeline Markers
```python
# Write marker onto timeline (Note: frameId must be relative to the timeline start)
relative_marker_frame = absolute_marker_frame - timeline_start
timeline.AddMarker(
    frameId=int(relative_marker_frame),
    color="Blue",
    name="Beat Marker",
    note="AI Beat Cut Snapped",
    duration=1
)
```

### 7. Color Node Graph Grading Copy (CopyGrades)
```python
# Clone node graph settings from first clip to all subsequent timeline clips
placed_video_clips = timeline.GetItemListInTrack("video", 1)
if len(placed_video_clips) > 1:
    source_clip = placed_video_clips[0]
    target_clips = list(placed_video_clips[1:])
    source_clip.CopyGrades(target_clips) # Returns boolean
```

---

## 🚨 API Troubleshooting, Gotchas & Solutions

### 1. `SetCurrentTimeline` GUI Focus Loss Gotcha
* **Problem**: Calling `SetCurrentTimeline` updates the active timeline in the background, but if the Resolve GUI does not refresh, subsequent calls to `AppendToTimeline` will still append footage onto whichever timeline tab is physically open in the editor window.
* **Solution**: Call a programmatic GUI tab jump to force timeline focus:
  ```python
  resolve.OpenPage("media")
  time.sleep(0.3)
  resolve.OpenPage("edit")
  time.sleep(0.3)
  ```

### 2. `AppendToTimeline` returns `[None]` when passing `recordFrame` or track indices
* **Problem**: Passing `"recordFrame"` to specify insert locations frequently fails silently in the Resolve API and returns `[None]` without editing anything.
* **Solution**:
  Do **NOT** specify `"recordFrame"` or `"trackIndex"` in the append dict when sewing sequential clips. Use **"Sequential Append"** by passing only `mediaPoolItem`, `startFrame`, and `endFrame`. Resolve will automatically place and snap them contiguously.

### 3. `AppendToTimeline` contiguous alignment offset when BGM is already present
* **Problem**: Since sequential append places clips at the absolute end of the timeline's contents, if a 30-second background music track is placed first, the sequential video cuts will be forced after the 30-second mark, causing a massive audio-video synchronization offset.
* **Solution (Empty-Timeline Targeted Workflow)**:
  1. **Purge Tracks**: Call `timeline.DeleteClips` to delete all video and audio clips first.
  2. **Append Video first**: Sequentially append all video cuts contiguously from the start frame (`86400`).
  3. **Clear Scratch Audio**: Remove the ambient scratch audio track automatically generated on Audio Track 1.
  4. **Target BGM Append**: Position and append the BGM clip by specifying target parameters: `"recordFrame": timeline_start`, `"trackIndex": 2`, and `"mediaType": 2` to lock BGM onto Audio Track 2.

### 4. `AddMarker` Absolute vs. Relative Coordinate Gotcha
* **Problem**: Timeline query methods return absolute frame indices (e.g. starting at `86400`). However, `AddMarker(frameId, ...)` accepts relative frame coordinates (starting at `0`). Passing absolute coordinates offsets the marker by an hour.
* **Solution**: Always subtract the timeline start frame to convert absolute frames to relative coordinates:
  ```python
  relative_frame = absolute_frame - timeline_start
  timeline.AddMarker(relative_frame, "Blue", ...)
  ```

### 5. Cross-Framerate Gapless Rendering Sync Glitches (`math.ceil`)
* **Problem**: Placing 29.97 FPS source clips on a 24.0 FPS timeline often leaves a 1-frame black gap during renders due to floating point calculation and rounding variances.
* **Solution**: Use the ceiling math formula to compute source frame durations:
  ```python
  duration_source = int(math.ceil(duration_timeline * (src_fps / timeline_fps)))
  ```
  This forces a small frame buffer, allowing Resolve to cleanly trim the excess contiguously and prevent gaps.

### 6. Edit Page Transform Keyframes Write Restriction
* **Problem**: The Resolve Python API strictly blocks scripting keyframe transitions or motion curves on Edit page `TimelineItem` geometry.
* **Solution**:
  Employ **"Static Reframing"**. Directly set static sizing properties (Zoom, RotationAngle) on Track 1, and alternate tilting values (e.g. `RotationAngle = 4.0` and `-4.0`) to synthetically simulate kinetic cuts snapped to beats.

### 7. Speed Ramping and Speed Curves Scripting Limitation
* **Problem**: Resolve API does not support dynamic speed ramping or speed curve generation on clips. Setting the "Speed" property directly is invalid.
* **Solution**:
  Use **"AI Jump-Cut Montage"** simulation: Slice a single raw source video into multiple short contiguous intervals (e.g., 0.2s - 0.3s) and append them back-to-back, creating a rapid jump-cut visual skip instead of speed ramp curves.

### 8. `TimelineItem` Geometry Properties and Black Borders
* **Problem**:
  1. The SDK documentation does not specify what property keys are supported by `GetProperty(key)`.
  2. Tilting a clip via `RotationAngle` exposes black backgrounds at the corners.
* **Solution**:
  1. **Undocumented No-Args API**: Call `item.GetProperty()` without arguments to return the full dictionary of supported properties (such as `'ZoomX'`, `'ZoomY'`, `'RotationAngle'`).
  2. **Reframing Zoom Buffer**: When setting rotation, always add a zoom scaling buffer (e.g. `ZoomX = 1.08`) to crop out black corner borders.

### 9. `CopyGrades` API Sync Limitations
* **Problem**: `TimelineItem.CopyGrades([targets])` occasionally fails due to color space or database syncing issues.
* **Solution (Middle-Click Copy Hack)**:
  In the "Color" page, highlight clips 2 to N, move your cursor over the graded first clip, and **click your mouse middle wheel-button** to instantly copy all node graph settings; or call `node_graph.ApplyGradeFromDRX("/path/to/grade.drx", 0)` in Python.
