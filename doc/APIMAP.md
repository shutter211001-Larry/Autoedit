# 🎬 DaVinci Resolve 21 API 方法對照與實戰踩坑指南 (APIMAP)

本文件完整列出 DaVinci Resolve 21 (Studio) Python API 所有可用類別及方法，並針對自動化剪輯實務中遭遇的 API 限制與 Bug 提供解決方案。

---

## 📂 DaVinci Resolve API 方法清單

### 1. `resolve` 全域入口類別 (24 個方法)
```text
DeleteLayoutPreset, ExportBurnInPreset, ExportLayoutPreset, ExportRenderPreset, Fusion, GetCurrentPage, GetFairlightPresets, GetKeyframeMode, GetMediaStorage, GetProductName, GetProjectManager, GetVersion, GetVersionString, ImportBurnInPreset, ImportLayoutPreset, ImportRenderPreset, LoadLayoutPreset, OpenPage, Print, Quit, SaveLayoutPreset, SetHighPriority, SetKeyframeMode, UpdateLayoutPreset
```

### 2. `project_manager` 專案管理器類別 (29 個方法)
```text
ArchiveProject, CloseProject, CreateCloudProject, CreateFolder, CreateProject, DeleteFolder, DeleteProject, ExportProject, GetCurrentDatabase, GetCurrentFolder, GetCurrentProject, GetDatabaseList, GetFolderListInCurrentFolder, GetFoldersInCurrentFolder, GetProjectLastModifiedTime, GetProjectListInCurrentFolder, GetProjectsInCurrentFolder, GotoParentFolder, GotoRootFolder, ImportCloudProject, ImportProject, LoadCloudProject, LoadProject, OpenFolder, Print, RestoreCloudProject, RestoreProject, SaveProject, SetCurrentDatabase
```

### 3. `current_project` 活動專案類別 (47 個方法)
```text
AddColorGroup, AddRenderJob, ApplyFairlightPresetToCurrentTimeline, DeleteAllRenderJobs, DeleteColorGroup, DeleteRenderJob, DeleteRenderPreset, ExportCurrentFrameAsStill, GetColorGroupsList, GetCurrentRenderFormatAndCodec, GetCurrentRenderMode, GetCurrentTimeline, GetGallery, GetMediaPool, GetName, GetPresetList, GetPresets, GetQuickExportRenderPresets, GetRenderCodecs, GetRenderFormats, GetRenderJobList, GetRenderJobStatus, GetRenderJobs, GetRenderPresetList, GetRenderPresets, GetRenderResolutions, GetSetting, GetTimelineByIndex, GetTimelineCount, GetUniqueId, InsertAudioToCurrentTrackAtPlayhead, IsRenderingInProgress, LoadBurnInPreset, LoadRenderPreset, Print, RefreshLUTList, RenderWithQuickExport, SaveAsNewRenderPreset, SetCurrentRenderFormatAndCodec, SetCurrentRenderMode, SetCurrentTimeline, SetName, SetPreset, SetRenderSettings, SetSetting, StartRendering, StopRendering
```

### 4. `media_pool` 媒體庫類別 (28 個方法)
```text
AddSubFolder, AppendToTimeline, AutoSyncAudio, CreateEmptyTimeline, CreateStereoClip, CreateTimelineFromClips, DeleteClipMattes, DeleteClips, DeleteFolders, DeleteTimelines, ExportMetadata, GetClipMatteList, GetCurrentFolder, GetRootFolder, GetSelectedClips, GetTimelineMatteList, GetUniqueId, ImportFolderFromFile, ImportMedia, ImportTimelineFromFile, MoveClips, MoveFolders, Print, RefreshFolders, RelinkClips, SetCurrentFolder, SetSelectedClip, UnlinkClips
```

### 5. `folder` (如 `root_folder`) 媒體資料夾類別 (11 個方法)
```text
ClearTranscription, Export, GetClipList, GetClips, GetIsFolderStale, GetName, GetSubFolderList, GetSubFolders, GetUniqueId, Print, TranscribeAudio
```

### 6. `current_timeline` 時間軸類別 (60 個方法)
```text
AddMarker, AddTrack, AnalyzeDolbyVision, ClearMarkInOut, ConvertTimelineToStereo, CreateCompoundClip, CreateFusionClip, CreateSubtitlesFromAudio, DeleteClips, DeleteMarkerAtFrame, DeleteMarkerByCustomData, DeleteMarkersByColor, DeleteTrack, DetectSceneCuts, DuplicateTimeline, Export, GetCurrentClipThumbnailImage, GetCurrentTimecode, GetCurrentVideoItem, GetEndFrame, GetIsTrackEnabled, GetIsTrackLocked, GetItemListInTrack, GetItemsInTrack, GetMarkInOut, GetMarkerByCustomData, GetMarkerCustomData, GetMarkers, GetMediaPoolItem, GetName, GetNodeGraph, GetSetting, GetStartFrame, GetStartTimecode, GetTrackCount, GetTrackName, GetTrackSubType, GetUniqueId, GetVoiceIsolationState, GrabAllStills, GrabStill, ImportIntoTimeline, InsertFusionCompositionIntoTimeline, InsertFusionGeneratorIntoTimeline, InsertFusionTitleIntoTimeline, InsertGeneratorIntoTimeline, InsertOFXGeneratorIntoTimeline, InsertTitleIntoTimeline, Print, SetClipsLinked, SetCurrentTimecode, SetMarkInOut, SetName, SetSetting, SetStartTimecode, SetTrackEnable, SetTrackLock, SetTrackName, SetVoiceIsolationState, UpdateMarkerCustomData
```

---

## 🔧 核心 API 呼叫語法與範例藍圖 (Core API Syntax & Call Blueprints)

本節為 AI 代理人提供最常使用的 DaVinci Resolve Python API 的精確語法與程式碼範本，防止生成錯誤的呼叫參數。

### 1. 專案與時間軸初始化 (Project & Timeline Lifecycle)
```python
# 1. 取得活動專案與媒體庫
project_manager = resolve.GetProjectManager()
current_project = project_manager.GetCurrentProject()
media_pool = current_project.GetMediaPool()

# 2. 建立全新空白時間軸
timeline_name = "AI_Auto_Edit"
timeline = media_pool.CreateEmptyTimeline(timeline_name)

# 3. 取得時間軸邊界資訊
timeline_start = timeline.GetStartFrame() # 通常返回絕對格數 86400 (代表 01:00:00:00)
timeline_end = timeline.GetEndFrame()
fps = float(current_project.GetSetting("timelineFrameRate")) # 取得時間軸影格率
```

### 2. 媒體素材搜尋與導入 (Media Search & Import)
```python
# 1. 遞迴搜尋媒體庫資料夾下的 Clip
def find_clip_by_name(folder, name_query):
    for clip in folder.GetClipList() or []:
        if name_query.lower() in clip.GetName().lower():
            return clip
    for sub_folder in folder.GetSubFolderList() or []:
        res = find_clip_by_name(sub_folder, name_query)
        if res:
            return res
    return None

# 2. 導入本機視訊/音訊檔案至媒體庫
root_folder = media_pool.GetRootFolder()
media_pool.SetCurrentFolder(root_folder)
imported_clips = media_pool.ImportMedia(["C:\\videos\\clip_01.mp4", "C:\\music\\bgm.mp3"])
```

### 3. 片段時間軸追加與拼接 (Timeline Appending)
```python
# 1. 順序無指定位置拼接 (最穩定影片拼接法)
clips_to_append = [
    {
        "mediaPoolItem": clip1_item,
        "startFrame": 0,          # 素材相對起點格
        "endFrame": 120           # 素材相對終點格 (共 120 影格)
    },
    {
        "mediaPoolItem": clip2_item,
        "startFrame": 24,
        "endFrame": 72
    }
]
# 順序追加至時間軸末尾
media_pool.AppendToTimeline(clips_to_append)

# 2. 靶向指定位置追加 (適用於背景配樂或 Logo 置底)
bgm_append_data = [{
    "mediaPoolItem": bgm_clip_item,
    "startFrame": int(start_sec * fps),
    "endFrame": int(end_sec * fps),
    "recordFrame": int(timeline_start),  # 時間軸絕對影格 (86400)
    "trackIndex": 2,                     # 音軌 2
    "mediaType": 2                       # 1 = Video, 2 = Audio
}]
media_pool.AppendToTimeline(bgm_append_data)
```

### 4. 時間軸片段查詢與刪除 (Query & Delete)
```python
# 1. 取得軌道上的所有片段 (Track Index 是從 1 開始的整數)
placed_video_clips = timeline.GetItemListInTrack("video", 1) or [] # V1 軌道
placed_audio_clips = timeline.GetItemListInTrack("audio", 2) or [] # A2 軌道

# 2. 從時間軸物理刪除片段
timeline.DeleteClips(placed_audio_clips)
```

### 5. 片段屬性設定與顏色標記 (Transform Properties & Clip Colors)
```python
# 取得 V1 第一個片段並設定幾何屬性
placed_clips = timeline.GetItemListInTrack("video", 1)
if placed_clips:
    clip_item = placed_clips[0]
    
    # 設定縮放與傾斜 (防止黑邊補償：旋轉 4 度同步縮放 1.08 倍)
    clip_item.SetProperty("ZoomX", 1.08)
    clip_item.SetProperty("ZoomY", 1.08)
    clip_item.SetProperty("RotationAngle", 4.0)
    
    # 標記素材剪輯顏色 (Navy / Teal / Yellow / Orange / Red / Pink)
    clip_item.SetClipColor("Teal")
```

### 6. 時間軸標記寫入 (Timeline Markers)
```python
# 寫入時間軸標記 (注意：frameId 必須是相對於起點的相對影格數)
relative_marker_frame = absolute_marker_frame - timeline_start
timeline.AddMarker(
    frameId=int(relative_marker_frame),
    color="Blue",
    name="Beat Marker",
    note="AI Beat Cut Snapped",
    duration=1
)
```

### 7. 調色節點同步複製 (Node Grade Cloning)
```python
# 將第一鏡的調色節點，同步抄給時間軸後續的所有片段
placed_clips = timeline.GetItemListInTrack("video", 1)
if len(placed_clips) > 1:
    source_clip = placed_clips[0]
    target_clips = list(placed_clips[1:])
    source_clip.CopyGrades(target_clips) # 回傳 boolean
```

---

## 🚨 API 實戰限制、Bug 與解決方案

### 1. `SetCurrentTimeline` 頁面聚焦失效限制
* **現象**：呼叫 `SetCurrentTimeline` 雖然會切換活動時間軸，但若達芬奇 GUI 未刷新，隨後的 `AppendToTimeline` 仍會把素材寫入螢幕上正開著的錯誤時間軸。
* **解決方案**：呼叫物理級的 GUI 頁面切換強制重新整理焦點：
  ```python
  resolve.OpenPage("media")
  time.sleep(0.3)
  resolve.OpenPage("edit")
  time.sleep(0.3)
  ```

### 2. `AppendToTimeline` 指定 `recordFrame` 與軌道導致回傳 `[None]` 的寫入失敗限制
* **現象**：傳入 `"recordFrame"` 參數在指定位置插入影片時，API 經常會靜默失敗並返回 `[None]`。
* **解決方案**：
  在拼接影片時，**完全不要指定 `"recordFrame"` 與 `"trackIndex"`**，將其改為 **「無指定位置順序追加 (Sequential Append)」**。Resolve 會自動嚴絲合縫地在末尾無縫對齊拼接影片。

### 3. `AppendToTimeline` 順序追加與已有內容時間軸起點對齊限制
* **現象**：當時間軸上已放有背景音樂（BGM）時，由於順序追加會拼接在「時間軸內容的末尾」，Resolve 會把隨後追加的所有影片強行放到 BGM 結束之後（例如第 30 秒後），造成嚴重的音畫錯位。
* **解決方案（空時間軸靶向定位工作流）**：
  1. **完全清空軌道**：在 Append 之前，利用 `timeline.DeleteClips` 清空所有影片與音訊。
  2. **順序拼接影片**：先追加影片（不帶 `recordFrame`），影片會 100% 從起點影格（`86400`）Contiguously 拼接。
  3. **清除現場音**：清除 Video Track 1 自帶的相機環境音。
  4. **音樂靶向追加**：對 BGM 執行**指定位置追加**（傳入 `"recordFrame": timeline_start`, `"trackIndex": 2`, `"mediaType": 2`），強行將 BGM 置入音軌 2 起點，實現完美對齊！

### 4. `AddMarker` 相對與絕對影格座標系座標錯位限制
* **現象**：時間軸查詢返回的均為絕對影格座標（起點為 `86400`），但 `AddMarker(frameId, ...)` 只接收相對於時間軸起點的相對座標（起點為 `0`）。直接傳入絕對影格會造成一小時的標記錯位。
* **解決方案**：寫入標記時務必減去時間軸起點影格：
  ```python
  relative_frame = absolute_frame - timeline_start
  timeline.AddMarker(relative_frame, "Blue", ...)
  ```

### 5. 跨影格率無縫拼接的單格黑格縫隙限制
* **現象**：將 29.97 FPS 的素材剪入 24 FPS 時間軸時，由於浮點數相除的精度捨入，常使片段長度在重拍點處小了零點幾格，渲染時出現 1 格黑格畫面。
* **解決方案**：在計算 source 時長時使用 `math.ceil` 向上取整公式：
  ```python
  duration_source = int(math.ceil(duration_timeline * (src_fps / timeline_fps)))
  ```
  這能強制影片富餘，由達芬奇的卡點機制自動截斷，保證 100% 物理無縫。

### 6. 編輯頁面屬性動態關鍵影格寫入限制
* **現象**：Python API 嚴格禁止了在 Edit 頁面對 `TimelineItem` 的幾何屬性寫入關鍵影格（Keyframe），無法直接用腳本在片段播放期間產生漸進縮放或動態推拉。
* **解決方案**：
  採用 **「靜態重構 (Static Reframing)」**。直接設定幾何屬性目標值（Zoom、RotationAngle），並搭配鄰近鏡頭的交替斜切擺動（如 `RotationAngle = 4.0` 與 `-4.0` 交替），在快速卡點播放時即可利用視角跳躍營造躍動感。

### 7. 變速與速度曲線 (Speed Ramping) 限制
* **現象**：Resolve API 未開放修改 `TimelineItem` 的速度百分比或繪製 Retime 變速曲線。直接嘗試修改 "Speed" 屬性無效。
* **解決方案**：
  若要實現卡點快進或閃切，可使用 **AI 閃切 (Jump Cut) 模擬**：將同一個原始視訊在時間軸上連續剪接多次，每次截取 0.2~0.3 秒的不同時間點畫面緊密拼接，以跳幀效果代替變速 API。

### 8. `TimelineItem` 幾何變形屬性獲取與黑邊問題
* **現象**：
  1. 官方未明示 `GetProperty(key)` 所支持的屬性。
  2. 套用 `RotationAngle` 時畫面四個角落會露出黑色背景邊框。
* **解決方案**：
  1. **無參數隱藏 API**：直接呼叫無參數的 `item.GetProperty()`，即可獲得包含 `'ZoomX'`, `'ZoomY'`, `'RotationAngle'`, `'Pan'`, `'Tilt'` 等在內的完整 Python 屬性字典。
  2. **縮放適配補償**：旋轉時，必須同步配合縮放提升（如 `ZoomX = 1.08`），強行將畫面局部放大以消除所有黑色死框。

### 9. `CopyGrades` API 調色套用限制
* **現象**：調用 `TimelineItem.CopyGrades([targets])` 偶發因色彩空間或節點狀態不同而套用失敗。
* **解決方案（滑鼠中鍵抄流）**：
  在 GUI 的「調色 (Color) 頁面」中，框選第 2 至第 N 個片段，將滑鼠移至第 1 個已調色片段上，**按下滑鼠中鍵（滾輪鍵）**即可瞬間完美套用所有節點；或在 Python 中呼叫 `node_graph.ApplyGradeFromDRX("/path/to/grade.drx", 0)` 以 100% 穩定套用。

### 10. 多 Take 與重複贅詞（口吃）的無縫精剪對齊限制 (Multi-take & Speech Stitching Sync Limit)
* **現象**：在進行「語意剪輯（Semantic Editing）」時，若直接拿外部辨識的完整句子時間碼（如 Subtitle 檔）去切單一視訊片段（例如只保留該句重疊時間中最長的一段 take 畫面），經常會發生**畫面被剪掉**（例如 Mars 說「這堂課呢」的畫面不見了）與**原音被剪掉**的 Bug。這是因為說話者在原片中可能包含了口吃贅詞、長停頓，甚至分成了好幾個不同的 takes（例如「大家好我是Mars...停頓...這堂課呢」）。
* **解決方案**：
  在剪輯腳本的 `flow` 控制中，絕不能單靠單一的 `startFrame` 到 `endFrame`。必須改採 **「複合片段縫合 (Multi-segment Stitching)」** 設計：
  1. 將語音中的有用部分與各個 Takes 的原聲幀範圍（例如 `28203-28290` 與 `28323-28372`）分開定義並在腳本中依序 Append 拼接，徹底跳過中間的廢話、停頓或口吃。
  2. 字幕時間軸的時長（`duration_secs`）應設為**所有縫合子片段影格長度的加總**，然後將字幕均勻或按字數比例分配到這個總時長上，如此便能保證在去除口吃的同時，畫面上 100% 能看到對應口型且聲音完全契合，消除一切斷頭句與畫外音！
