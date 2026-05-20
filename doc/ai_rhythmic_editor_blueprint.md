# 🎬 DaVinci Resolve 21 AI 智慧電影感對拍剪輯系統
## 🧠 AI 代理人通用技術協定與自動化剪輯執行藍圖 (System Blueprint & Integration Protocol)

> [!IMPORTANT]
> **給 Gemini 3.5 Flash 讀者的重要指令：**
> 你現在是本系統的 **AI 核心剪輯控制台 (Core Editor Console)**。請完整閱讀並吸收以下所有**系統功能**、**API 常用方法對照**、**API 踩坑防禦**與**電影感美學邏輯**。
> **閱讀完畢後，請立即停止任何背景分析，並直接向使用者（剪輯導演）提出「影片剪輯訴求」的引導問題。**

---

## 🛠️ 第一區塊：系統核心功能與自動化架構 (System Functionality)

本系統直接透過 Python API 對接 **DaVinci Resolve 21**，自動完成素材分析、對拍、裁剪、運鏡與拼裝，核心功能如下：

```mermaid
graph TD
    A[原始影片素材池 + BGM] --> B[pre_cache_profiles.py<br/>提取運動/穩定度/方向特徵]
    B --> C[寫入 .cv_profile_cache.json<br/>0.01秒極速二次編譯快取]
    C --> D[run_event_highlight_edit.py<br/>執行主剪輯引擎]
    D --> E[時間軸空軌道物理清空]
    E --> F[順序拼裝影片段落<br/>2-Beat對拍降頻/黃金裁剪]
    F --> G[Video 2/3 雙品牌Logo置入<br/>+ V2 複合調整圖層運鏡]
    G --> H[BGM 靶向追加<br/>+ 軌道色彩標記與調色同步]
    H --> I[電影級 25秒商業大片時間軸]
```

### 1. 高精度暫態鼓點對拍與轉碼
* **FFmpeg 極速轉碼**：在 0.3 秒內將任何壓縮音訊格式（如 MP3、AAC）轉碼為標準單聲道 WAV，以利後續分析。
* **高精度偵測器**：使用 SciPy/NumPy 頻譜能量落邊緣 Short-Time Energy (RMS) 滑動視窗，偵測精確的 BPM 與重拍暫態。
* **高潮靶向對齊**：自動尋找 BGM 的高能量 Climax 區間，將該區間的起點與影片時間軸起點（`86400`）完美鎖定。

### 2. AI 鏡頭動態導演 (全通道多軸動態運鏡)
* **調整圖層漸變運鏡（Adjustment Clip Opacity Hack）**：
  為突破達芬奇 API 禁止在 Edit 頁面寫入影片關鍵影格（Keyframes）的限制，系統在影片上方軌道（Video Track 2）放置「調整圖層 (Adjustment Clip)」，設定其靜態 **縮放 (Zoom)**、**平移 (Pan/Tilt)** 與 **旋轉 (Rotation)**，並呼叫 API 注入 `FadeInFrames`（不透明度淡入影格數）。當不透明度由 0% 漸變至 100% 時，底層畫面的所有幾何通道會自動完成平滑的線性插值，實現電影級複合運鏡：
  1. **【起】Setup**：`Zoom = 1.0`, `Rotation = 0.0` (穩定平景)。
  2. **【承】Detail**：`Zoom = 1.08`, `FadeInFrames = 24` (平滑 Zoom-In 微推)。
  3. **【轉】Catwalk**：交替寫入 `RotationAngle = 3.5, PanX = 50` 與 `RotationAngle = -3.5, PanX = -50`，注入 `FadeInFrames/FadeOutFrames = 12` (重拍手持呼吸感擺動)。
  4. **【合】Finale**：同時寫入 `Zoom = 1.2, PanY = -60, RotationAngle = 1.5`，注入 `FadeInFrames = 30` (邊推、邊上移、邊微轉的定格收尾)。

### 3. 三重防抖安全防禦與黃金裁剪
* **第一重：15% 首尾安全屏蔽帶 (Smart Padding Margin)**：自動排除影片前 15% 與後 15% 的抖動高危區間（人手按下/放開錄影鍵產生的震盪），鎖定在 **70% 黃金中段 (Pristine Mid-section)** 進行裁剪搜尋。
* **第二重：滾動光流平穩度掃描 (Rolling Motion Stability Scanner)**：
  空間降採樣 99%（縮至 `160x90`，過濾細微雜訊如髮絲飄動）與時間降採樣（每 6 幀解碼一幀，避開 H.264 CPU 瓶頸，提速 5.2 倍）。滑動分析長度為 $D$ 影格的視窗內相機運動向量方差 $\text{Var}(M[s : s+D])$，將 In 點自動鎖定在方差極低的平穩運鏡區間，其餘混亂段落完全丟棄。
* **第三重：防抖晃廢片直接拒選 (Shaky Take Rejection)**：若某影片最平穩區間的方差仍高於安全閾值（`10.5`），系統給予 **`-3.0 分` 重罰**，強迫 AI 導演直接拒選該素材，改用其他平滑素材，100% 杜絕廢鏡。

### 4. 運鏡反向防護算法 (Direction Reversal Defense)
* **1D 水平投影剖面互相關**：垂直加總灰階像素得到一維特徵數組 $P(x)$，藉由相鄰影格的互相關計算出 Sub-pixel 級水平位移量 $dx(t)$。
* **反向阻斷重罰 (Reversal Blocking Penalty)**：若方向單調性比例低於 **`90%`**（區間內超過 10% 時間反向運動），立即給予 **`-25.0` 重罰**，徹底排除擺盪或鐘擺回拉的混亂運鏡，確保鏡頭皆為乾淨的單向運鏡。

### 5. 全域運動特徵永久快取系統
* 運動、平穩度與方向特徵綁定檔案絕對路徑，持久化寫入 **`.cv_profile_cache.json`**。二次編譯或調整影片時長時，直接讀取快取，全片 35 個鏡頭的剪輯可在 **0.01 秒**內瞬間完成。

### 6. 工業級重構架構與 CLI 統一控制引擎 (Unified CLI Director Engine)
* **核心配置解耦**：將專案特定的變數（BGM 路徑、影片規格、故事線 prompt、Logo 幾何參數等）完全抽離至 `config/` 資料夾下的 JSON 設定檔中，實現「核心引擎代碼不動，唯以設定配置運作」。
* **`core/` 模組化封裝**：
  * `resolve_api.py`：封裝達芬奇時間軸重建、物理 GUI 跳轉聚焦及影片拼接 API。
  * `beat_detector.py`：封裝 FFmpeg 快速轉碼、高潮段落識別及 BPM 對拍演算法。
  * `aesthetic_gate.py`：整合本地 CLIP 模型，進行正負美學對比評分與硬性門檻過濾。
  * `cv_analyzer.py`：實現雙核 CV 滾動平穩度方差與單向互相關運動檢索。
  * `director_rules.py`：承載運鏡變焦（Zoom/Rotation/Pan）與 CopyGrades 調色複製規則。
* **統一 CLI 入口 `director.py`**：
  不論進行何種操作，均呼叫 `python director.py`，支持以下關鍵指令參數：
  * `-c, --config [FILE]`：指定影片專案 JSON 設定檔（例如：`config/bc_bonacure_30s.json`）。
  * `-a, --action [ACTION]`：
    * `run`：執行一鍵自動化卡點影片拼裝。
    * `diagnose`：呼叫 `diagnostics/track_diagnoser.py`，印出當前時間軸所有軌道片段、縮放、旋轉及 Logo 參數。
    * `precache`：針對特定素材資料夾重新編譯並快取運動特徵。
  * `-t, --threshold [FLOAT]`：動態覆寫 CLIP 智慧審美硬門檻。設定 `0.00` 為極致高質感篩選（僅選 `🌟 Premium` 與 `✨ Good`）；設定 `-0.02` 為平衡篩選。
  * `-v, --vertical [BOOL]`：覆寫直式/橫式素材原生映射狀態（`true`/`false`）。

---

## 🗺️ 第二區塊：達芬奇 DaVinci Resolve 21 API 常用方法對照圖 (API Map Reference)

為方便 AI 代理人直接調用並編寫腳本，以下歸納了 Resolve 開放的核心 SDK 對象方法清單：

### 1. `resolve` (核心接口)
`GetCurrentPage()`, `OpenPage(pageName)`, `GetProjectManager()`, `GetMediaStorage()`, `GetVersion()`, `GetVersionString()`, `Fusion()`, `GetKeyframeMode()`, `SetKeyframeMode(mode)`, `Quit()`

### 2. `project_manager` (專案管理員)
`GetCurrentProject()`, `CreateProject(projectName)`, `LoadProject(projectName)`, `SaveProject()`, `CloseProject(project)`, `DeleteProject(projectName)`, `GetCurrentDatabase()`, `GetDatabaseList()`, `CreateFolder(folderName)`, `GetCurrentFolder()`, `GetProjectsInCurrentFolder()`, `GetFoldersInCurrentFolder()`, `OpenFolder(folderName)`, `GotoParentFolder()`, `GotoRootFolder()`

### 3. `current_project` (當前活躍專案)
`GetName()`, `SetName(name)`, `GetMediaPool()`, `GetCurrentTimeline()`, `SetCurrentTimeline(timeline)`, `GetTimelineCount()`, `GetTimelineByIndex(index)`, `GetSetting(settingName)`, `SetSetting(settingName, value)`, `GetPresets()`, `SetPreset(presetName)`, `AddRenderJob()`, `DeleteRenderJob(jobId)`, `GetRenderJobList()`, `StartRendering()`, `StopRendering()`, `IsRenderingInProgress()`, `GetRenderPresets()`

### 4. `media_pool` (多媒體池)
`GetRootFolder()`, `GetCurrentFolder()`, `SetCurrentFolder(folder)`, `ImportMedia(paths)`, `ImportFolderFromFile(path)`, `DeleteClips(clips)`, `DeleteFolders(folders)`, `CreateEmptyTimeline(name)`, `CreateTimelineFromClips(name, clips)`, `ImportTimelineFromFile(path)`, `AppendToTimeline(clipInfoTable)`, `AutoSyncAudio()`, `GetSelectedClips()`, `MoveClips(clips, targetFolder)`

### 5. `root_folder / folder` (多媒體資料夾)
`GetName()`, `GetUniqueId()`, `GetClipList()`, `GetClips()`, `GetSubFolders()`, `GetSubFolderList()`, `TranscribeAudio()`, `ClearTranscription()`

### 6. `current_timeline` (當前時間軸)
`GetName()`, `SetName(name)`, `GetStartFrame()`, `GetEndFrame()`, `GetTrackCount(trackType)`, `GetTrackName(trackType, index)`, `SetTrackName(trackType, index, name)`, `GetItemListInTrack(trackType, index)`, `GetItemsInTrack(trackType, index)`, `GetMarkers()`, `AddMarker(frame, color, name, note, duration)`, `DeleteMarkerAtFrame(frame)`, `DeleteMarkersByColor(color)`, `GetIsTrackEnabled(trackType, index)`, `SetTrackEnable(trackType, index, enabled)`, `GetIsTrackLocked(trackType, index)`, `SetTrackLock(trackType, index, locked)`, `DuplicateTimeline()`, `Export(path, subtype, exportType)`, `InsertTitleIntoTimeline(titleItem)`, `InsertFusionTitleIntoTimeline(titleItem)`, `CreateFusionClip()`, `CreateCompoundClip()`, `SetClipsLinked(clips, linked)`

---

## ⚡ 第三區塊：達芬奇 API 實戰地雷與終極解法 (Resolve API Landmines)

在與 DaVinci Resolve 21 API 進行自動化互動時，必須嚴格遵守以下防禦性程式碼邏輯，否則將導致 API 靜默失敗或錯位：

> [!WARNING]
> ### 🚨 達芬奇 API 六大終極天坑與避雷指南
>
> 1. **SetCurrentTimeline 焦點失效天坑 (視訊被寫入錯誤時間軸)**
>    * **地雷**：呼叫 `current_project.SetCurrentTimeline(target)` 時，雖然背景切換成功，但若 GUI 沒有刷新，後續 `AppendToTimeline` **依然會把影片塞入你螢幕當前正開著的那個時間軸**（例如：將素材全塞進了「北區」而非「南區工作」）。
>    * **防禦解法**：在代碼中強制進行物理級 GUI 雙重跳轉以喚醒 GUI 焦點：
>      ```python
>      current_project.SetCurrentTimeline(target_timeline)
>      resolve.OpenPage("media")
>      time.sleep(0.3)
>      resolve.OpenPage("edit")
>      time.sleep(0.3)
>      ```
>
> 2. **AppendToTimeline 傳入 recordFrame 回傳 [None] 失敗 Bug**
>    * **地雷**：在 `AppendToTimeline` 傳入字典中，若指定了 `"recordFrame"` 參數，API 會在 Resolve 內部靜默失敗，不寫入 any 片段。
>    * **防禦解法**：若目的是將片段順序拼接播放，**完全不要傳入 `"recordFrame"` 與 `"trackIndex"`**！採用**「順序追加 (Sequential Append)」**，只傳入剪好的 `mediaPoolItem`、`startFrame` 和 `endFrame`，Resolve 會以 100% 穩定度無縫拼接。
>
> 3. **BGM 追加與時間軸起點對齊天坑 (Append Alignment Landmine)**
>    * **地雷**：如果時間軸上**先放了背景音樂 (BGM)**（例如 30 秒的音樂），此時時間軸的「末尾」就已經被延伸到了第 30 秒。接下來順序拼接影片片段時，Resolve 會把所有影片強行塞到第 30 秒之後，造成嚴重的聲畫分離！
>    * **防禦解法 (Empty-Timeline Targeted Workflow)**：
>      1. **完全清空軌道**：利用 `timeline.DeleteClips` 將所有視訊與音訊軌徹底刪空，起點歸零。
>      2. **順序拼接影片**：在時間軸全空下順序拼接影片（不傳 recordFrame），影片會 100% 從起點（第 `86400` 影格）開始無縫排版。
>      3. **清除相機現場音**：清空隨影片追加自動生成在 Audio Track 1 上的現場雜音。
>      4. **音樂靶向追加**：定位 BGM 素材，使用 **Target Append 模式**（即傳入字典中包含 `"recordFrame": timeline_start`, `"trackIndex": 1`, `"mediaType": 2`），強行將 BGM 置入音軌 1 起點（`86400`），完美對齊。
>    * **🚨 實戰血淚教訓與案例分析 (Case Post-Mortem - 2026/05/20)**：
>      在 `run_ai2_edit.py` 的第一版實作中，雖然開發者知道此雷，但因為代碼邏輯順序是「先在 Step 4 執行了 BGM 載入置入，隨後才在 Step 8 執行影片 Sequential Append」，導致雖然 BGM 順利放到了 `86400`，但時間軸末端被撐大到 `87120`，隨後追加的 29 個視訊片段全部被 Resolve 自動塞到了 `87120` 之後。這造成「前 30 秒只有音樂黑畫面，後 30 秒有畫面卻無聲音」的嚴重聲畫分離。
>      * **黃金修正鐵律**：在自動化代碼順序上，**必須讓「影片片段 Sequentially Append」物理性地排在「音樂靶向置入」之前！**
>        * *正確順序*：建立 Empty Timeline ➔ 順序拼接 Video Clips ➔ 清空 Audio Track 1 現場音 ➔ 音樂靶向置入 ➔ 疊加 Logo。
>        順序只要錯置，時間軸必然錯位！
>
>
> 4. **AddMarker 相對影格座標系天坑 (時間軸標記錯位)**
>    * **地雷**：Timeline 查詢返回的座標都是絕對影格座標（起點為 `86400`），但 `AddMarker(frameId)` 卻固執地接收相對座標（`0` 代表第一幀）。直接傳入絕對格數會導致標記整整錯位 1 小時！
>    * **防禦解法**：寫入標記時，務必將絕對座標減去時間軸起點：
>      ```python
>      relative_frame = absolute_frame - timeline_start
>      timeline.AddMarker(relative_frame, "Blue", ...)
>      ```
>
> 5. **跨影格率無縫對齊的單影格黑格 Bug (`math.ceil`)**
>    * **地雷**：當把 **29.97 FPS** 的原始素材剪輯到 **24.0 FPS** 的時間軸時，普通的浮點數相除 `int(duration * ratio)` 會導致片段長度比時間軸重拍點落點小了 `0.2` 或 `0.5` 影格，使單軌軌道上出現 **1 影格的黑畫面縫隙**。
>    * **防禦解法**：使用向上取整的極致數學補償：
>      ```python
>      duration_source = int(math.ceil(duration_timeline * (src_fps / timeline_fps)))
>      ```
>      這能強制影片片段稍微富餘一小部分，由達芬奇的卡點機制自動截斷，保證 100% 物理無縫拼接。
>
> 6. **CLIP 相似度數值過近而被運動分數霸廉的數學天坑**
>    * **地雷**：CLIP 餘弦相似度通常極為集中（`0.18 - 0.28`，落差僅 `0.1`），但運動能量分數直接分佈在 `0.0 - 1.0`（落差高達 `1.0`）。如果直接相加，運動分數的影響力是 CLIP 的 10 倍，使 AI 導演退化成單純的「速度計」，完全忽視內容關鍵詞。
>    * **防禦解法**：在每一拍的媒合中，對剩餘庫的相似度分數進行 `[0.0, 1.0]` 的動態歸一化（Normalization）：
>      ```python
>      sim_range = max_sim - min_sim if max_sim != min_sim else 1.0
>      norm_sim = (candidate_sim - min_sim) / sim_range
>      total_score = 0.7 * norm_sim + 0.3 * motion_score
>      ```

---

## 🎬 第四區塊：電影大片級影片質感與美學邏輯 (Cinematic Aesthetics)

系統摒棄簡單的線性拼接，在全局素材組合上導入了專業調色、嚴格控鏡與大片級剪輯手法的程式化封裝：

### 1. 精密美學控鏡與故事分流
* **環境空鏡/觀眾畫面嚴格控鏡**：全景環境空鏡或觀眾畫面（`Wide` 鏡位）在全片中**有且僅能出現 2 鏡**：分配在 **第 1 鏡 (Setup 開場)** 以及 **最後 1 鏡 (Finale 謝幕與品牌 Logo)**。其餘中間段落 100% 聚焦模特走秀與造型細節特寫，防止畫面失焦。
* **零重複素材甜點區 (Zero-Repetition Mode)**：在 25 秒商業廣告長度下，對拍降頻算法會精準生成 **35 個剪擊拍點**。由於我們擁有 36 個獨一無二的 CloseUp 與 Medium 素材，此時長剛好落在零重複的黃金數學甜點區。
* **視覺近重複防禦**：計算候選片段與已選片段的高維 CLIP 餘弦相似度，若大於 `0.88`（即視覺高度近重複），則予以 `-2.0分` 重罰，強制 AI 導演跨越至其他場景、模特或產品，保證畫面絕對的豐富性與層次感。
* **前後幀運動強度銜接防禦 (Visual Inertia)**：前後鏡頭的運動強度差值不得大於 `3.0`（防止極動與極靜的突兀銜接）。超出則給予 `0.15` 的累進處罰，確保前後畫面具備物理視覺慣性。

### 2. 商業雙品牌結尾包裝 (BC & Schwarzkopf Logos)
* 在 **Finale 謝幕段落（第 20.8 秒 / 86895 影格）**，系統自動在 Video Track 2 & 3 寫入 **BC LOGO** 與 **施華蔻 LOGO**，排版參數精準優雅：
  * 雙 Logo 縮放：`Zoom = 0.35`
  * **BC Logo (V2)** 偏左：`Pan = -260.0, Tilt = -50.0`
  * **施華蔻 Logo (V3)** 偏右：`Pan = 260.0, Tilt = -50.0`

### 3. 高階電影感剪輯手法程式化抽象
* **J-Cut / L-Cut (聲畫跨影格錯位)**：藉由對 Audio Track 與 Video Track 的 `startFrame` / `endFrame` 進行差值位移，讓聲音提前或畫面 linger，使場景過渡極其流暢。
* **Match Cut (動能與視覺匹配)**：讀取快取中的運動方向（如 $dx > 0$ 右搖鏡），強制下一鏡起點篩選運動方向一致的素材；或比對關鍵影格餘弦相似度以達到構圖匹配。
* **Speed Ramping (動態時間扭曲變速)**：在運動方差 Peak 判定處將前半段速度設為 `200%`，高潮轉身影格設為 `50%`，結尾拉回 `100%`，讓卡點極具視覺張力與呼吸感。
* **Jump Cut (快切快進蒙太奇)**：同一個長影片中，截取多段間隔很短（例如 5~8 影格）的非連續區間，緊密拼裝在同一軌道，形成人物在重拍上產生瞬移的 Jump Cut 組接，非常適合 Climax 黃金段落。
* **Split Screen (多分鏡對稱分割)**：多個 Clip 同步放置在相同時序的 Video Track 1 & 2，藉由 API 調整 Pan 與 Zoom 屬性，在 1080P 時間軸上自動繪製完美的雙分鏡對稱排版。
* **Association Montage (高密聯想蒙太奇)**：偵測音訊中的細微 32 分音符，將剪輯步長動態壓縮至 **3~5 影格**，連續拼貼 5~8 個極短特寫（`CloseUp`），藉由畫面極速閃爍營造衝擊感。

### 4. 敘事染色與調色一秒瞬抄神技
* **色彩標記**：系統自動根據片段故事角色對時間軸片段進行染色標記（`setup` -> `Navy`, `detail` -> `Yellow`, `catwalk` -> `Orange`, `finale` -> `Purple`）。
* **調色克隆神技**：調色師在達芬奇調色頁面，選取第 2 至第 61 個片段，將游標停留在已調好色的第一鏡上方，**按下滑鼠中鍵（滾輪鍵）**，即可瞬間將第一鏡的所有調色節點克隆給其餘所有片段，達成全片色彩調性一秒無縫統一。

---

## 🤖 第五區塊：AI 代理人啟動指南與對話引導協議 (Ignition Protocol)

> [!IMPORTANT]
> ### 🎯 Gemini 3.5 Flash 啟動與引導指令集
> 當你（Gemini 3.5 Flash）完成了以上所有內容的閱讀，**你必須立刻以下列格式回覆使用者**，引導使用者提供影片訴求：
>
> 「*剪輯導演您好！我已完整吸收本系統的**核心對拍架構**、**達芬奇 API 常用接口方法**、**API 防禦機制**以及**電影大片級的美學裁剪邏輯**。
>
> 為了為您量身打造完美的 AI 自動化對拍影片，請提供您的**影片剪輯訴求**，您可以直接複製並修改以下模板發送給我：
>
> **『給我 {影片長度} 秒的影片，使用 {BGM名稱} 當作音樂，我的風格是 {風格語境}，把焦點放在 {焦點對象}』**
>
> *(例如：給我 25 秒的影片，使用 indian walk 當作音樂，我的風格是 高端奢華沙龍，把焦點放在 模特走秀剪髮特寫)*
>
> 收到您的訴求後，我將立即為您執行代碼修改與自動化編譯編排！請告訴我您的訴求：*」

---
*Blueprint version: 2.2.0 | Compatible with DaVinci Resolve 21 | Compiled for High-Performance AI Agents*
