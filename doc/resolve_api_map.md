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

### Gotcha #9: 達芬奇 API 轉場特效 (Transitions) 的靜默缺失限制
* **問題描述**：
  許多剪輯師希望使用 API 自動在所有剪點上添加「交叉溶解 (Cross Dissolve)」等轉場特效。然而，截止到 **DaVinci Resolve 21**，官方 Python API **完全沒有開放對 TimelineItem 套用轉場特效**的介面，Effects Library 在腳本中是不可見的。
* **解決方案 (1-Second Workaround)**：
  雖然無法用腳本套用，但我們的剪輯腳本在計算 `startFrame` 和 `endFrame` 時，**已經自動在視訊開頭與結尾留足了富餘的「素材長度（Handles Room）」**！
  使用者只需在達芬奇中：
  1. 點擊時間軸，按下 `Ctrl + A` (全選所有影片)。
  2. 按下 `Ctrl + T` (或 macOS 的 `Cmd + T`)。
  這能在一秒鐘內**瞬間為全片所有 61 個剪點套用預設轉場**，且 100% 成功，絕不會因為 Handles 不足而報錯！

### Gotcha #10: 變速與速度曲線 (Speed Ramping) 的腳本限制與極致替代方案
* **問題描述**：
  達芬奇 Python API 僅開放了讀寫 `RetimeProcess` (0=項目, 1=最近幀, 2=幀混合, 3=光流法) 與 `MotionEstimation`，但**並未開放修改 TimelineItem 的 Speed (變速百分比) 或繪製 Speed Curve 變速曲線**。直接嘗試 SetProperty("Speed", ...) 屬性是無效的。
* **解決方案 (AI Jump-Cut Montage / 快切快進蒙太奇)**：
  如果想要達到「快進/快速閃切」的動態變速效果，我們可以使用 **AI 閃切 (Jump Cut) 演算法**：
  將同一個原始視訊片段，在時間軸上連續剪接 3 次（每次擷取其不同時間點的 0.3 秒短畫面）。這能在不依賴變速 API 的情況下，創造出極具視覺張力的「快進/閃切跳接」效果，非常適合卡點大秀的黃金 Climax 段落！

### Gotcha #11: 獲取時間軸片段完整屬性字典的無參數隱藏 API
* **問題描述**：
  在 Resolve API 中，官方文件並未明確列出 `TimelineItem.GetProperty(key)` 支持哪些屬性字串，嘗試傳入很多標準鍵值（如 `"speed"`, `"rotation"`）經常返回 `None`，讓開發者難以得知支持哪些變形屬性。
* **解決方案**：
  **直接呼叫無參數的 `item.GetProperty()`**（不傳入任何 Key 字串）。Resolve 會非常慷慨地回傳一個完整的 **Python 屬性字典**，包含所有支持的可修改鍵值！
  ```python
  # 實測回傳結果範例
  props = item.GetProperty()
  # 結果：{'Pan': 0.0, 'Tilt': 0.0, 'ZoomX': 1.0, 'ZoomY': 1.0, 'ZoomGang': True, 'RotationAngle': 0.0, 'AnchorPointX': 0.0, 'AnchorPointY': 0.0, 'Pitch': 0.0, 'Yaw': 0.0, 'FlipX': False, 'FlipY': False, 'CropLeft': 0.0, 'CropRight': 0.0, 'CropTop': 0.0, 'CropBottom': 0.0, 'CropSoftness': 0.0, 'CropRetain': False, 'DynamicZoomEase': 0, 'CompositeMode': 0, 'Opacity': 100.0, 'Distortion': 0.0, 'RetimeProcess': 0, 'MotionEstimation': 0, 'Scaling': 0, 'ResizeFilter': 0}
  ```

### Gotcha #12: AI 鏡頭動態導演與斜切旋轉邊界黑影 Bug (AI Camera Motion Director)
* **問題描述**：
  當使用 API `item.SetProperty("RotationAngle", 2.0)` 對片段施加旋轉以模擬手持斜切卡點效果時，由於畫面轉動，四個角落會露出底層的 **黑色背景邊框 (Black Borders)**，嚴重影響大片美觀。
* **解決方案**：
  在進行旋轉歪斜的同時，必須同步配合縮放提升，強制畫面進行 **1.08倍的縮放** 進行畫面填充，消除所有黑色死角：
  ```python
  item.SetProperty("ZoomX", 1.08)
  item.SetProperty("ZoomY", 1.08)
  item.SetProperty("RotationAngle", 2.0 if is_even else -2.0)
  ```

### Gotcha #13: 編輯頁面關鍵影格屬性 (Transform Keyframes) 寫入限制與動態推拉 Workaround
* **問題描述**：
  透過 Python 呼叫 `item.SetProperty("ZoomX", 1.15)` 只能將該片段整個期間設置為單一的**靜態縮放數值**。達芬奇 Python API 嚴格禁止了在 Edit 頁面對 `TimelineItem` 的屬性進行關鍵影格（Keyframe）的動態寫入或時間曲線插值，無法直接用腳本實現「單個片段播放期間的漸進縮放動畫（Ken Burns）」。
* **大師級工作流解決方案**：
  1. **快切交替卡點擺動 (Alternating Angle Sway)**：
     在極為短暫的卡點段落（如 0.25 秒一鏡），透過腳本為相鄰鏡頭交替寫入正負角度的傾斜屬性（如 `RotationAngle = 4.0` 與 `-4.0`）。雖然每鏡內部是靜態的，但隨著高頻率的剪點切換，在重拍播放時會產生極強的手持晃動卡點視覺！
  2. **一秒點亮內建動態縮放 (Dynamic Zoom Toggle)**：
     如果需要每個影片在播放時都具有平滑推近/推遠的動態感，最完美的混合工作流為：
     - 利用腳本自動完成完美的「音樂鼓點剪接、去大抖動與近重複防禦」並對齊時間軸。
     - 剪接完成後，在達芬奇中按下 `Ctrl + A` 全選所有片段。
     - 在右上角「檢查器 (Inspector)」將 **「動態縮放 (Dynamic Zoom)」** 開關直接點亮（啟用）。達芬奇會瞬間自動為所有片段套用無縫的推拉動畫，配合精準剪接，視覺效果震撼無比！

### Gotcha #14: 達芬奇 CopyGrades API 限制與調色師一秒瞬抄神技
* **問題描述**：
  在 Resolve API 中，調用 `TimelineItem.CopyGrades([targets])` 雖然會回傳 `True`，但在底層調色資料庫中，經常會因為前後片段的解析度、色彩空間或節點狀態不同而**無法將色調套用至其他片段**，導致畫面上看來沒有任何改變。
* **調色師最愛的 1 秒 GUI 解決方案**：
  在達芬奇內建的「調色 (Color) 頁面」中，可以直接使用比腳本快 100 倍、100% 穩定支持所有遮罩、追蹤、LUT 複製的快捷神技：
  1. **滑鼠中鍵瞬抄流 (最推薦)**：
     - 選取時間軸上第 2 至第 61 個需要套用調色的片段（點擊第 2 個片段，按住 `Shift`，點擊第 61 個片段）。
     - 將滑鼠游標移動到**第 1 個調好色的片段**上方，**按下您的「滑鼠中鍵（滾輪鍵）」**！
     - 瞬間，所有被框選的片段將 100% 完美套用第 1 鏡的所有調色節點！
  2. **畫廊抓取靜態影格套用**：
     - 在已調好色的第一鏡畫面上點擊右鍵，選擇 **「抓取靜態影格 (Grab Still)」**。
     - 全選其他片段，右鍵點擊左側畫廊剛剛抓下的靜態影格，選擇 **「套用調色 (Apply Grade)」**！
  3. **自動化 ApplyGradeFromDRX 替代**：
     - 透過腳本獲取 `clip.GetNodeGraph()` 後，調用 `node_graph.ApplyGradeFromDRX("/path/to/grade.drx", 0)`，可實現 100% 穩定的無 GUI 自動調色。




### Gotcha #15: AppendToTimeline 順序拼接與已有內容之時間軸起點對齊天坑 (Append Alignment Landmine)
* **問題描述**：
  In Resolve API 中，使用最穩定的「順序追加 (Sequential Append)」時（即在 `AppendToTimeline` 的傳入字典中**完全不指定 `recordFrame`**），Resolve 會預設將素材拼接至**當前時間軸內容的末尾 (Current End of Timeline)**。
  若此時時間軸上**已先被放了背景音樂 (BGM)**（例如一個 30 秒的音樂剪接），此時時間軸的「末尾」就已經被延伸到了第 30 秒。接下來順序拼接影片片段時，Resolve 會把所有影片片段**強行塞到第 30 秒（第 `87120` 影格）之後**！
  這會造成極為嚴重的錯位：前 30 秒是黑畫面+音樂，後 30 秒是影片+無音樂，音畫完全不同步！
* **解決方案**：
  採用**「空時間軸靶向定位工作流 (Empty-Timeline Targeted Workflow）」**，確保 100% 影格級音畫無縫對齊：
  1. **完全清空軌道**：在 Append 之前，利用 `timeline.DeleteClips` 將所有 Video 軌與 Audio 軌徹底刪空，將時間軸物理起點歸零。
  2. **順序拼接影片**：在時間軸全空的情況下，直接執行順序拼接（不傳入 `recordFrame`），此時影片會 100% 從時間軸的最開端（第 `86400` 影格）開始 contiguously 排版。
  3. **清除相機現場音**：清空隨著影片追加自動生成在 Audio Track 1 上的影片現場雜音。
  4. **音樂靶向追加**：定位背景音樂素材，使用 **Target Append 模式**（即傳入字典中包含 `"recordFrame": timeline_start`, `"trackIndex": 1`, `"mediaType": 2`），強行將 30 秒 BGM 置入音軌 1 起點（`86400`），完美對齊影片！
