DaVinci Resolve 21 API 方法探索報告
產生時間：2026-05-18 17:02:17
============================================================

## resolve  (24 個方法)
----------------------------------------
  DeleteLayoutPreset
  ExportBurnInPreset
  ExportLayoutPreset
  ExportRenderPreset
  Fusion
  GetCurrentPage
  GetFairlightPresets
  GetKeyframeMode
  GetMediaStorage
  GetProductName
  GetProjectManager
  GetVersion
  GetVersionString
  ImportBurnInPreset
  ImportLayoutPreset
  ImportRenderPreset
  LoadLayoutPreset
  OpenPage
  Print
  Quit
  SaveLayoutPreset
  SetHighPriority
  SetKeyframeMode
  UpdateLayoutPreset

## project_manager  (29 個方法)
----------------------------------------
  ArchiveProject
  CloseProject
  CreateCloudProject
  CreateFolder
  CreateProject
  DeleteFolder
  DeleteProject
  ExportProject
  GetCurrentDatabase
  GetCurrentFolder
  GetCurrentProject
  GetDatabaseList
  GetFolderListInCurrentFolder
  GetFoldersInCurrentFolder
  GetProjectLastModifiedTime
  GetProjectListInCurrentFolder
  GetProjectsInCurrentFolder
  GotoParentFolder
  GotoRootFolder
  ImportCloudProject
  ImportProject
  LoadCloudProject
  LoadProject
  OpenFolder
  Print
  RestoreCloudProject
  RestoreProject
  SaveProject
  SetCurrentDatabase

## current_project  (47 個方法)
----------------------------------------
  AddColorGroup
  AddRenderJob
  ApplyFairlightPresetToCurrentTimeline
  DeleteAllRenderJobs
  DeleteColorGroup
  DeleteRenderJob
  DeleteRenderPreset
  ExportCurrentFrameAsStill
  GetColorGroupsList
  GetCurrentRenderFormatAndCodec
  GetCurrentRenderMode
  GetCurrentTimeline
  GetGallery
  GetMediaPool
  GetName
  GetPresetList
  GetPresets
  GetQuickExportRenderPresets
  GetRenderCodecs
  GetRenderFormats
  GetRenderJobList
  GetRenderJobStatus
  GetRenderJobs
  GetRenderPresetList
  GetRenderPresets
  GetRenderResolutions
  GetSetting
  GetTimelineByIndex
  GetTimelineCount
  GetUniqueId
  InsertAudioToCurrentTrackAtPlayhead
  IsRenderingInProgress
  LoadBurnInPreset
  LoadRenderPreset
  Print
  RefreshLUTList
  RenderWithQuickExport
  SaveAsNewRenderPreset
  SetCurrentRenderFormatAndCodec
  SetCurrentRenderMode
  SetCurrentTimeline
  SetName
  SetPreset
  SetRenderSettings
  SetSetting
  StartRendering
  StopRendering

## media_pool  (28 個方法)
----------------------------------------
  AddSubFolder
  AppendToTimeline
  AutoSyncAudio
  CreateEmptyTimeline
  CreateStereoClip
  CreateTimelineFromClips
  DeleteClipMattes
  DeleteClips
  DeleteFolders
  DeleteTimelines
  ExportMetadata
  GetClipMatteList
  GetCurrentFolder
  GetRootFolder
  GetSelectedClips
  GetTimelineMatteList
  GetUniqueId
  ImportFolderFromFile
  ImportMedia
  ImportTimelineFromFile
  MoveClips
  MoveFolders
  Print
  RefreshFolders
  RelinkClips
  SetCurrentFolder
  SetSelectedClip
  UnlinkClips

## root_folder  (11 個方法)
----------------------------------------
  ClearTranscription
  Export
  GetClipList
  GetClips
  GetIsFolderStale
  GetName
  GetSubFolderList
  GetSubFolders
  GetUniqueId
  Print
  TranscribeAudio

## current_timeline  (60 個方法)
----------------------------------------
  AddMarker
  AddTrack
  AnalyzeDolbyVision
  ClearMarkInOut
  ConvertTimelineToStereo
  CreateCompoundClip
  CreateFusionClip
  CreateSubtitlesFromAudio
  DeleteClips
  DeleteMarkerAtFrame
  DeleteMarkerByCustomData
  DeleteMarkersByColor
  DeleteTrack
  DetectSceneCuts
  DuplicateTimeline
  Export
  GetCurrentClipThumbnailImage
  GetCurrentTimecode
  GetCurrentVideoItem
  GetEndFrame
  GetIsTrackEnabled
  GetIsTrackLocked
  GetItemListInTrack
  GetItemsInTrack
  GetMarkInOut
  GetMarkerByCustomData
  GetMarkerCustomData
  GetMarkers
  GetMediaPoolItem
  GetName
  GetNodeGraph
  GetSetting
  GetStartFrame
  GetStartTimecode
  GetTrackCount
  GetTrackName
  GetTrackSubType
  GetUniqueId
  GetVoiceIsolationState
  GrabAllStills
  GrabStill
  ImportIntoTimeline
  InsertFusionCompositionIntoTimeline
  InsertFusionGeneratorIntoTimeline
  InsertFusionTitleIntoTimeline
  InsertGeneratorIntoTimeline
  InsertOFXGeneratorIntoTimeline
  InsertTitleIntoTimeline
  Print
  SetClipsLinked
  SetCurrentTimecode
  SetMarkInOut
  SetName
  SetSetting
  SetStartTimecode
  SetTrackEnable
  SetTrackLock
  SetTrackName
  SetVoiceIsolationState
  UpdateMarkerCustomData


============================================================
## 🚨 達芬奇 API 實戰踩坑與終極解決方案 (Troubleshooting & Gotchas)

### Gotcha #1: SetCurrentTimeline 焦點失效 Bug (視訊被 append 到錯誤時間軸)
* **問題描述**：
  在 Python 中執行 `current_project.SetCurrentTimeline(target_timeline)` 時，雖然背景資料已切換，但達芬奇的畫面（GUI）如果沒有更新，隨後執行的 `media_pool.AppendToTimeline()` **依然會固執地把素材塞入你螢幕上當前正開著的那個時間軸**（例如：將素材全塞進了「北區」而非「南區工作」）。
* **解決方案**：
  在代碼中呼叫物理級的「GUI 頁面雙重跳轉」強制刷新 Resolve 焦點，實測 100% 能成功喚醒 GUI 的時間軸焦點：
  ```python
  import time
  current_project.SetCurrentTimeline(target_timeline)
  resolve.OpenPage("media")
  time.sleep(0.3)
  resolve.OpenPage("edit")
  time.sleep(0.3)
  ```

### Gotcha #2: AppendToTimeline 傳入 recordFrame 回傳 [None] 的失敗 Bug
* **問題描述**：
  在 `AppendToTimeline` 的傳入字典中，若指定了 `"recordFrame"` 參數，API 會在 Resolve 內部靜默失敗，回傳一個包含 None 的列表 `[None]`（外層看起來像成功，但實際上沒有寫入任何片段）。這是因為音訊軌混合、時間碼起點（Timecode Offset）不對齊或軌道鎖定導致的 API 相容性 Bug。
* **解決方案**：
  如果目的是將影片片段按節奏一個接一個「順序拼接播放」，**完全不要傳入 `"recordFrame"` 與 `"trackIndex"`**！
  使用**「順序追加 (Sequential Append)」**，只傳入剪好的 `mediaPoolItem`、`startFrame` 和 `endFrame`，Resolve 就會以 100% 的極致穩定度，自動順序把所有鏡頭無縫拼裝！
  ```python
  clips_to_append.append({
      "mediaPoolItem": clip_item,
      "startFrame": int(src_start),
      "endFrame": int(src_end)
  })
  media_pool.AppendToTimeline(clips_to_append)
  ```

### Gotcha #3: 素材 Start Frame 的時間碼偏移陷阱
* **問題描述**：
  呼叫 `clip.GetClipProperty("Start")` 雖然回傳 `'0'`（字串），但很多專業相機素材的真實起點是有時間碼（Timecode Offset）的（例如：`Start TC` 顯示 `05:28:25;22`）。在指定剪接起點時，如果直接傳入整數 `0`，有可能會因為小於素材的真實起居影格而導致寫入失敗。
* **解決方案**：
  若要截取素材某個部分，需從 `Start` 到 `End` 的相對區間進行 `int` 轉型，並只在素材本身的相對合法格數範圍內做擷取；或使用**順序追加方式**讓 Resolve 自動抓取最安全。

### Gotcha #4: AddMarker 相對影格座標系天坑 (時間軸標記錯位)
* **問題描述**：
  在 Resolve API 中，Timeline 查詢返回的座標都是**絕對影格座標**（例如，起點在 `01:00:00:00` 的時間軸，起始影格是 `86400`）。然而，`timeline.AddMarker(frameId, ...)` API 卻固執地接收**相對於時間軸起點的相對座標**（以 `0` 代表第一幀）。如果您直接傳入絕對格數 `86400`，標記會落在 `02:00:00:00`，即整整錯位 1 小時！
* **解決方案**：
  在寫入標記時，務必將絕對座標減去時間軸起點以轉換為相對座標：
  ```python
  relative_frame = absolute_frame - timeline_start
  timeline.AddMarker(relative_frame, "Blue", ...)
  ```

### Gotcha #5: 跨影格率無縫對齊的單影格黑格 Bug (`math.ceil`)
* **問題描述**：
  當您把 **29.97 FPS** 的原始素材剪輯到 **24.0 FPS** 的時間軸時，由於浮點數相除產生的捨入誤差，普通的 `int(duration * ratio)` 運算會導致片段長度比時間軸重拍點落點小了 `0.2` 或 `0.5` 影格。這會使 V1 單軌軌道上出現 **1 影格的黑畫面縫隙**（畫面閃爍黑影），無法嚴絲合縫。
* **解決方案**：
  使用向上取整的極致數學補償：
  ```python
  import math
  duration_source = int(math.ceil(duration_timeline * (src_fps / timeline_fps)))
  ```
  這能強制影片片段稍微富餘一小部分，由達芬奇的卡點機制自動截斷，保證 100% 物理無縫拼接。

### Gotcha #6: CLIP 相似度數值過近而被運動分數霸凌的數學天坑
* **問題描述**：
  CLIP 算出的餘弦相似度通常都非常集中（例如 `0.18 - 0.28`，落差極小）。但是運動能量分數是直接分佈在 `0.0 - 1.0`（落差高達 `1.0`）。如果直接相加，**運動分數的影響力是 CLIP 的 6 倍以上**，導致 AI 導演退化成單純的「速度計」，完全忽視您的內容關鍵詞。
* **解決方案**：
  在每一拍的媒合中，對剩餘庫的相似度分數進行 `[0.0, 1.0]` 的動態歸一化（Normalization），確保 CLIP 享有的絕對主導權：
  ```python
  sim_range = max_sim - min_sim if max_sim != min_sim else 1.0
  norm_sim = (candidate_sim - min_sim) / sim_range
  total_score = 0.7 * norm_sim + 0.3 * motion_score
  ```

### Gotcha #7: 靜音前奏與音軌裁切偏移免疫 (silent intro & left offset)
* **問題描述**：
  如果背景音樂開頭有淡入或靜音，鼓點檢測會漏掉前幾秒，導致開場影片沒有卡點。且如果音軌在時間軸上被手動裁切（Left Offset），標記座標會偏離音樂的物理拍子。
* **解決方案**：
  1. 使用 **BPM 規律反向外推**，將第一個偵測到的鼓點向前反推，直到補滿最前面的靜音區間。
  2. 讀取 `audio_clip.GetLeftOffset()`，自動將所有偵測到的秒數減去該裁切偏移，達成 100% 裁切免疫。

### Gotcha #8: 視覺近重複防禦機制 (Visual Near-Duplicate Defense) 
* **問題描述**：
  在專業拍攝中，同一個模特在同一背景下會連續錄製好幾個檔案（例如 `C0273.MP4`, `C0274.MP4`）。雖然檔案名稱和實體完全不同，但在視覺上它們是**幾乎一模一樣的近重複片段**。如果 AI 順序調用它們，使用者依然會覺得「畫面一直重複」。
* **解決方案**：
  在決定下一個剪點影片時，利用 CLIP 提取的高維特徵向量，計算該候選片段與**當前已選定的所有歷史片段**的 Cosine 相似度。如果大於 `0.88`（即視覺高度近重複），則跳過或予以重罰，強制 AI 導演跨越至其他場景、模特或產品，保證畫面絕對的豐富性與層次感！