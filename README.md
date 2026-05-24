# 🎬 DaVinci Resolve 21 AI 自動對拍與語意剪輯系統
## 📘 AI-Powered Rhythmic & Semantic Video Auto-Editor

本專案是一套基於 Python API 與電腦視覺技術的 **AI 音訊對拍、語意重剪與視訊自動剪接系統**。本系統直接與 **DaVinci Resolve 21 (Studio)** 的 Python API 進行原生對接，能自動將相機原始素材與背景音樂（BGM）的暫態鼓點、人聲對話與語意片段進行高精度對齊，有效解決了影格率轉換相位差、訊號處理延遲、音軌裁切偏移、劇烈抖動廢片、運鏡方向衝突以及字幕同步重組等專業剪輯痛點。

---

## 🌟 核心特色與演算法架構

### 1. SRT 語意對齊剪輯與 AIDA 重剪 (SRT Semantic Editing & AIDA Reordering)
* **行銷語意重組 (Semantic Reordering)**：系統能讀取長素材影片及其對應的 `SRT` 字幕檔，根據設定的行銷結構（例如 AIDA 架構：Hook 吸引注意力 ➡️ Intro 導入主題 ➡️ Core Curriculum 核心內容 ➡️ Endorsement 口碑見證 ➡️ CTA 行動呼籲），在時間軸上將原始素材段落進行重新排序與剪接。
* **字幕時間軸自適應對齊 (SRT Timecode Adaptation)**：當片段順序重組後，系統會自動解析原始 SRT 的字幕塊（Subtitle Blocks）與文字內容，依據新時間軸的切片順序與時長，以毫秒級精度精確重新計算並輸出全新、完全對齊無縫同步的 `SRT` 字幕檔，免除手動二次聽寫或重新拉字幕的繁瑣工序。
* **視覺自適應縮放與染色 (Zoom & Color Tags)**：剪輯時可套用交替縮放重構（如 Zoom 1.0 與 1.18 交替）與素材軌道染色標記（如 Teal 染色），以提供明顯的編輯頁視覺區隔，方便後期進行人工視覺校對。

### 2. 靜態重構與剪輯構圖設計 (Cinematic Clip Reframing & Symmetrical Tilts)
* **4 階段靜態多軸重構 (Multi-axis Symmetrical Clip Reframing)**：
  由於 DaVinci Resolve Python API 在 Edit 頁面具備物理限制，**無法直接透過指令碼寫入動態關鍵影格（Keyframe）以實現動態運鏡**。為解決此限制並豐富畫面層次，本系統在剪輯時將運鏡回歸本質，採用 **「靜態幾何縮放與對稱斜切設計 (Static Zoom & Symmetrical Rotation Angle Adjustments)」**，直接設定並寫入每個片段在 Track 1 上的幾何屬性：
  1. **【起】開場準備 (Setup)**：`Zoom = 1.0` (或 3.16), `RotationAngle = 0.0`。保持原始構圖與視角，平穩開場。
  2. **【承】細節工藝 (Detail)**：`Zoom = 1.10` (或 3.476), `RotationAngle = 0.0`。微幅等比拉近，凸顯產品標籤或主體造型細節。
  3. **【轉】高潮秀場 (Catwalk Climax)**：`Zoom = 1.15` (或 3.634)，並搭配 **交替對稱斜切擺動 (Alternating Symmetrical Tilts)**：偶數鏡頭寫入靜態 `RotationAngle = 4.0`，奇數鏡頭寫入靜態 `RotationAngle = -4.0`。利用傾斜角度在視覺上營造大秀躍動感。
  4. **【合】品牌謝幕 (Finale)**：`Zoom = 1.20` (或 3.792), `RotationAngle = 0.0`。將畫面進一步拉近，以穩重定格收尾。
* **橫直式像素自動適配 (Aspect Ratio Scaling Compensation)**：
  當原始相機素材為橫式（16:9）且時間軸設定為直式（9:16）時，系統會自動偵測並對 `Zoom` 值套用 **`3.16` 倍的等比物理放大補償**（例如：`1.15 * 3.16`），確保橫式素材能自動填滿直式時間軸。


### 3. 電影感運動平滑與連續留線 (Motion Flow Smoothing)
* **理想運動能量包絡線 (Motion Envelope)**：對全片拍點的理想運動度套用 **5 拍滑動平均濾波器 (5-Beat Moving Average Filter)**，將鋸齒跳變平滑化為溫和起伏的正弦能量波。
* **前後幀動態留線銜接防禦**：計算當前片段與前一鏡片段的運動能量絕對差值。一旦差值 **`> 3.0`**，則給予 **`0.15` 的遞增重罰**，強迫 AI 優先挑選具備視覺物理慣性（Visual Inertia）的流暢影片，確保視覺舒適度。

### 4. 高精度暫態鼓點檢測與高潮對齊 (Beat & Climax Sync)
* 使用 **FFmpeg** 將音樂格式轉碼為標準 Mono WAV（低於 0.3 秒）。
* 內建高精度 SciPy/NumPy 頻譜能量暫態鼓點檢測演算法，精準鎖定樂曲重拍與 BPM。
* **高潮對齊**：自動尋找 BGM 的高能量高潮段落，並將其起點與影片時間軸起點（`86400`）鎖定。

### 5. 黃金中段裁剪與防震廢片三重防禦機制 (Triple Shaky Defense)
* 為了過濾按鈕按壓震盪、相機重置、或失焦手抖等混亂段落，系統設計了「黃金中段裁剪 ➡️ 滾動光流篩選 ➡️ 廢鏡頭直接拒選」的三重防禦管線：
  1. **第一重：15% 首尾安全屏蔽帶 (Smart Padding Margin)**：自動屏蔽素材前 15% 與後 15% 的高危區間（因剛按下錄影鍵或準備關閉錄影所產生的手部震動），強制只在剩餘 70% 的**「黃金中段 (Pristine Mid-section)」**內進行搜尋。
  2. **第二重：滾動光流平穩度評估 (Rolling Motion Stability Scanner)**：利用 OpenCV 將畫面在記憶體中降採樣 99% 至 `160x90` 縮圖（過濾風吹、秀髮晃動等微小高頻雜訊，鎖定宏觀相機運鏡），以前向連續跳幀解碼（比一般 seek 解碼快 5.2 倍）滑動分析該片段中長度為 $D$ 的視窗內相機運鏡方差 $\text{Var}(M[s : s+D])$。系統會自動定位出方差最低、運鏡最平穩的黃金 In 點，並只裁剪該區間放入時間軸，**將其餘混亂段落丟棄**。
  3. **第三重：防抖晃廢片直接拒選機制 (Shaky Take Rejection)**：若某個原始影片整支都處於極度混亂狀態（例如手持劇烈跑步），導致其最平穩區間的方差仍高於安全閾值（`10.5`），系統會給予該素材 **`-3.0 分` 的重罰**，**強迫 AI 導演直接捨棄該檔案**，從素材庫中換選其他平滑素材，確保廢片不會進入時間軸。

### 6. 運鏡反向防護算法 (Motion Vector Monotonicity & Direction Reversal Defense)
* **一維水平投影剖面互相關算法 (1D Horizontal Projection Profile Cross-Correlation)**：
  對灰階圖像沿垂直方向加總，得到代表畫面水平特徵剖面的一維數組 $P(x)$。藉由相鄰幀的一維滑動互相關，計算出 sub-pixel 級別的逐幀水平位移量 $dx(t)$。
* **方向單調性比例得分 (Monotonicity Ratio)**：
  $$\text{Monotonicity Ratio} = \frac{\max(\sum [dx > 0], \sum [dx < 0])}{\text{Total Active Frames}}$$
  若比例低於 **`90%`**（區間內有超過 10% 的時間在反向運鏡），系統會觸發 **`Reversal Blocking Penalty` 阻斷性重罰**，強制過濾掉任何含有運鏡方向逆轉的倒退、鐘擺搖晃段落，確保剪出來的鏡頭永遠是「單方向平滑運動」的電影感鏡頭！

### 7. 敘事連續性求解器 (Narrative Continuity Solver)
* **角色與動作雙軸約束**：利用預先編譯的 `clip_annotations.json` 及語意分析模型，確保情節、角色與動作轉換符合影視敘事邏輯。
* **角色鎖定與疲勞懲罰**：AI 優先保持同一模特（角色）連續展示達 `min_contiguous_cuts` (如 3 鏡) 以維持視覺連貫性（Lock Bonus），隨後施加疲勞懲罰（Fatigue Penalty），強迫切換其他角色或空鏡，避免視覺疲勞。
* **動作因果關係限制 (Action Causality)**：支援前後置動作關聯（例如：`spray` (噴定型液) 之後優先接 `combing` (梳理) 或 `product_closeup` (產品特寫)，並自動避開同動作短時間內的重複），從數學層面保證剪輯邏輯。

### 8. 25 秒商業規格與觀眾畫面精準控鏡
* **觀眾/空鏡畫面限制為恰好 2 鏡**：全片中的 `Wide` (全景觀眾/環境空鏡) 素材被嚴格控制在恰好 2 鏡，精準地分配在**全片第 1 鏡 (Setup 開場)** 以及 **全片最後 1 鏡 (Finale 謝幕與品牌 Logo)**，其餘中間段落則聚焦模特走秀與造型工藝。
* **25秒零重複素材對齊**：在 25 秒商業廣告長度下，對拍降頻算法會精準生成 **35 個剪擊拍點**。由於我們擁有 36 個獨一無二的 CloseUp 與 Medium 素材，此時長剛好落在**零重複素材（Zero-Repetition）的數學甜點區**！

### 9. 全域運動特徵快取系統 (`.cv_profile_cache.json`)
* 將原先與「時長、拍點位置」綁定的快取，升級為與「檔案絕對路徑」綁定的 **全域特徵資料庫**，儲存整支影片逐幀的運動向量與平穩度曲線。
* 二次微調、重新剪接或改變時長時，系統直接從快取讀取特徵曲線，**全片 35 個鏡頭的二次編譯與剪輯可在 0.01 秒內完成**！

### 10. 雙品牌 Outro 結尾卡排版設計 (BC & Schwarzkopf Logos)
* 系統會自動在時間軸建立 **Video Track 2 與 Video Track 3**，並在 **Finale 謝幕段落（第 20.8 秒 / 86895 影格）** 自動寫入 **BC LOGO** 與 **施華蔻 LOGO**。
* **精準排版參數**：
  * 雙 Logo 縮放至中尺寸：`Zoom = 0.35`
  * **BC Logo (V2)** 偏左排版：`Pan = -260.0`, `Tilt = -50.0`
  * **施華蔻 Logo (V3)** 偏右排版：`Pan = 260.0`, `Tilt = -50.0`

### 11. `math.ceil` 跨影格率對齊與 API 座標系修正
* 採用向上取整動態補償公式，解決 29.97 FPS 素材在 24.0 FPS 時間軸上因浮點數捨入造成的 1 影格黑格問題：
  $$\text{duration\_source} = \text{int}(\text{math.ceil}(\text{duration\_timeline} \times \frac{\text{src\_fps}}{\text{timeline\_fps}}))$$
* **座標系修正**：達芬奇的 `AddMarker` 接收相對座標，而 `GetMarkers` 返回絕對座標。系統自動對 Marker 執行「減去起點影格（`86400`）」運算，達成高精度對齊。

### 12. AI Fusion 動態字卡美學預設 (Aesthetics Presets)
* 藉由達芬奇 API 開放的 Fusion 空間介面，直接在時間軸片段上注入動態合成字卡（Title Cards），並控制字型、字距、縮放與發光等美學屬性。
* 預先設計了三套通用美學參數矩陣：
  * **⚜️ 風格一：極簡奢華襯線風 (The "Vogue" Serif)**：高優雅高留白襯線字體，適用於高端時尚、精品。
  * **⚡ 風格二：新黑色潮流幻彩風 (The "Cyber-Tech" Bold)**：粗獷、幾何無襯線體，搭配幻彩 Neon Glow，適用於潮牌與電音片。
  * **📐 風格三：瑞士現代社論雜誌風 (The "Swiss Editorial")**：極簡、嚴謹、左對齊不對稱排版，呈現高端平面設計雜誌質感。

---

## 📂 專案架構與目錄指南

```text
├── config/                      # 項目設定 JSON 檔
│   ├── bc_bonacure_30s.json
│   └── bc_exhibition_25s.json
├── core/                        # 系統核心演算法與 API
│   ├── aesthetic_gate.py        # CLIP 語意計算與美學門閥
│   ├── beat_detector.py         # SciPy 音訊對拍暫態鼓點檢測
│   ├── continuity_solver.py     # 敘事連續性與動作因果求解器
│   ├── cv_analyzer.py           # OpenCV 降採樣光流穩定度與運動向量計算
│   ├── director_rules.py        # 剪輯規則與美學分級
│   └── resolve_api.py           # DaVinci Resolve Python 原生 API 對接封裝
├── diagnostics/                 # 系統診斷與分析模組
│   ├── diagnose_ai2.py
│   ├── resolve_api_test.py
│   └── track_diagnoser.py       # 時間軸軌道與焦點診斷器
├── doc/                         # 專案技術文件與手冊
│   ├── PROJECT.md               # 英文版開發手冊
│   ├── 專案.md                  # 中文版開發手冊
│   ├── ai_rhythmic_editor_blueprint.md
│   ├── video_quality_enhancement_guide.md
│   └── resolve_api_map.md       # Resolve API 連接說明
├── legacy/                      # 經典編譯腳本與獨立工具 (請在此目錄執行)
│   ├── run_event_highlight_edit.py # 商業秀場剪接主引擎
│   ├── pre_cache_profiles.py    # 獨立特徵快取生成引擎
│   ├── reimport_assets.py       # 雲端素材去重導入工具
│   ├── create_semantic_timeline.py # 還原「Sam前導片_高能行銷版」時間軸 (含 SRT 生成與對齊)
│   ├── stability_analyzer_hyper_fast.py # 單影片光流平穩度掃描器
│   ├── direction_stability_analyzer.py # 單影片單調性方向掃描器
│   └── diag_timelines.py        # 快速診斷當前聚焦時間軸
├── scratch/                     # 臨時脚本與驗證代碼
├── director.py                  # 🎬 系統核心控制台 (CLI 主入口)
└── test_copy_grades.py          # Master 調色同步節點複製測試
```

---

## ⚙️ 系統環境需求與安裝步驟

### 1. 達芬奇軟體與系統要求
* 必須安裝 **DaVinci Resolve 21 Studio** (付費版本才支援外部 Python API 呼叫)。
* **啟用外部指令碼**: 打開 Resolve 偏好設定 ➡️ 系統 ➡️ 常規 ➡️ 「外部指令碼執行使用」選擇 **「本機」** 或 **「本機與網路」**。
* 作業系統：Windows 11 / 10。

### 2. 環境變數設定 (Windows PowerShell)
為使 Python 能夠正確定位 Resolve 的 API 庫，必須將以下環境變數添加至系統（路徑依實際安裝位置微調）：

```powershell
$env:RESOLVE_SCRIPT_API="%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
$env:RESOLVE_SCRIPT_LIB="C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
$env:PYTHONPATH="%RESOLVE_SCRIPT_API%\Modules;$env:PYTHONPATH"
```

### 3. 安裝 Python 依賴套件
推薦使用 Python 3.10 以上環境。在終端機中執行：

```bash
pip install numpy scipy opencv-python torch torchvision torchaudio transformers
```

> [!NOTE]
> 專案內含 CLIP 多模態語意與美學估算，若本機配有 NVIDIA GPU 並安裝 CUDA，會自動以 GPU 加速運算。

### 4. 系統音訊解碼組件
* 系統音訊鼓點偵測依賴 `FFmpeg`，請確保系統已安裝 `ffmpeg`，且已將其執行檔路徑加入到系統的 `PATH` 環境變數中。

---

## 🚀 快速上手指南

本系統提供統一的 CLI 控制台 `director.py`，您可以透過 `--action` 參數執行所有核心流程。

### 第一步：全域運動特徵與語意快取預編譯 (`precache`)
在背景執行高速前向解碼，將影片素材的運動向量、平穩度曲線與 CLIP 嵌入特徵提取並永久保存。**（完全獨立於達芬奇運行，速度極快）**

```bash
python director.py --config config/bc_exhibition_25s.json --action precache
```

### 第二步：時間軸焦點與 GUI 軌道診斷 (`diagnose`)
驗證達芬奇專案與時間軸的連接，並檢查當前 GUI 視窗中聚焦的 active timeline 名稱。

```bash
python director.py --config config/bc_exhibition_25s.json --action diagnose
```

> [!IMPORTANT]
> **達芬奇 API 焦點防錯鎖定**：若 Resolve GUI 當前聚焦的分頁並非目標時間軸，請在達芬奇軟體中**雙擊該時間軸**，確保編輯頁聚焦此時間軸，以避免將素材 append 到錯誤的分頁！

### 第三步：啟動 AI 導演剪輯引擎 (`run`)
一鍵執行鼓點暫態分析、高潮靶向對齊、敘事連續性最佳化、黃金中段裁剪、運鏡防晃防逆轉過濾、雙品牌 Outro Placer，並自動將 Master 調色節點同步至所有新剪接片段。

```bash
python director.py --config config/bc_exhibition_25s.json --action run
```

### 第四步：啟動 SRT 語意剪輯與字幕時間軸重組
若要重建並還原「Sam前導片_高能行銷版」，且自動產出毫秒級對齊的對應 SRT 字幕檔，請執行：

```bash
python legacy/create_semantic_timeline.py
```
執行完畢後，系統會自動在 `C:\TEST\Sam.srt` 與 `C:\TEST\Sam_corrected.srt` 中覆寫完全對齊新時間軸播放時間點的字幕檔案。您只需在 Resolve 中選擇 `File > Import > Subtitle` 並導入該檔，即可完美播放。

### 第五步：AI 智慧單片人工重選與 Reroll 替換 (`reroll`)
若您在 Resolve 時間軸上觀看影片後，發現某個片段需要被更換：
1. 在達芬奇的 Edit 頁面上，**右鍵點擊該片段 ➡️ 選擇「剪輯顏色 (Clip Color)」 ➡️ 設定為「紅色 (Red)」、「粉紅色 (Pink)」或「玫瑰紅 (Rose)」**。
2. 回到終端機執行下方的 `reroll` 指令：

```bash
python director.py --config config/bc_exhibition_25s.json --action reroll
```

AI 會**精確鎖定**該紅色片段，剔除目前已在時間軸上被使用的影片，依據該段落的鼓點時長、語意 prompt 限制、運動平滑度以及敘事連續性，自動在素材庫中匹配替代鏡頭，並在 **0.2秒內無縫替換、保留運鏡設定並重新同步 Master 調色級別**！

---

## 📊 範例設定檔結構 (`config/bc_exhibition_25s.json`)

```json
{
  "project_name": "2605_BCbonacure",              // 達芬奇專案名稱
  "timeline_name": "AI_Exhibition_25s",            // 要自動建立/編輯的時間軸名稱
  "aspect_ratio": "9:16",                          // 時間軸比例
  "source_footage_vertical": true,                 // 原始相機素材是否為直式
  "media_folder_path": "D:\\Exhibition\\CLIP",    // 素材資料夾路徑
  "bgm_path": "D:\\Music\\Indian_Walk.mp3",        // 背景配樂路徑
  "duration_seconds": 25.0,                        // 廣告目標長度 (秒)
  "aesthetic_threshold": 0.00,                     // CLIP 美學門檻篩選
  "prompts": {                                     // 對應起承轉合 4 階段語意 Prompt
    "setup": "exquisite exhibition booth, modern luxury hair salon venue background context",
    "detail": "closeup of cosmetic product bottle packaging, luxury brand logo details",
    "catwalk": "fashion model presenting premium hair product, elegant action performance",
    "finale": "grand finale branding product presentation closeup with studio lighting"
  },
  "narrative_characters": {                        // 敘事角色定義 (用於連續性分類)
    "blonde_female": "a female model with blonde hair, beautiful blonde woman",
    "stylist": "professional hair stylist working on client hair, hair dresser"
  },
  "narrative_actions": {                           // 敘事動作定義 (用於因果約束)
    "spray": "spraying hair spray product aerosol mist on hair, hair styling spray",
    "combing": "combing or brushing hair, styling hair with hands",
    "product_holding": "holding a premium cosmetic product bottle in hand close-up"
  },
  "continuity_rules": {                            // 敘事連續性規則限制
    "character_locking": {                         // 角色鎖定規則
      "min_contiguous_cuts": 3,                    // 至少連續出現 3 鏡
      "lock_bonus": 1.8,                           // 持續加分
      "fatigue_penalty": -0.8                      // 超過後給予疲勞減分，強迫切換
    },
    "action_causality": [                          // 動作因果與重複防禦
      {
        "trigger_action": "spray",
        "prevent_repeat": true,                    // 噴完噴霧後短時間不重複
        "repeat_penalty": -3.0,
        "prefer_next_actions": ["combing", "product_holding"], // 噴完噴霧優先接梳頭或產品特寫
        "prefer_bonus": 1.2
      }
    ]
  },
  "outro_logos": [                                 // 結尾雙品牌定格 Logo 物理參數
    {
      "name": "BC_2018_LOGO.png",
      "track": 2,
      "zoom": 0.3,
      "pan": -180.0,
      "tilt": -250.0,
      "duration_frames": 120
    },
    {
      "name": "SKP_Logo.jpg",
      "track": 3,
      "zoom": 0.3,
      "pan": 180.0,
      "tilt": -250.0,
      "duration_frames": 120
    }
  ]
}
```

---

## 🎬 電影感剪輯手法與 AI 程式化實現

本系統將影視業界的剪輯手法進行了數學建模，並使用 DaVinci Resolve Python API 進行實體編譯：

| 剪輯手法 | 手法定義與價值 | AI 演算法程式化實現機制 |
| :--- | :--- | :--- |
| **J-Cut / L-Cut** | **聲畫跨影格過渡**<br>聲音先行或畫面先行，建立流暢的場景過渡，消弭機械卡點感。 | 在 `AppendToTimeline` 時將視訊軌與音訊軌分開操作。**J-Cut** 將音訊軌的 `startFrame` 向左偏移（5~10影格），使下鏡聲音提早切入，而畫面剪點仍保持在鼓點重拍上。 |
| **Match Cut** | **動作與視覺匹配剪輯**<br>利用前後鏡頭相同的運動方向或構圖，形成無縫順暢感。 | **動能匹配**：比對兩影片的運動向量。若前一鏡結尾為右搖（$dx > 0$），則下一鏡起點限制篩選右搖素材。<br>**構圖匹配**：比對 keyframe 的 CLIP 特徵向量，選取主體構圖與邊緣輪廓（例如主體皆居中）最相似的片段。 |
| **Speed Ramping** | **動態時間扭曲變速**<br>同一鏡頭內進行速度變化（快 ➡️ 慢 ➡️ 快），常用於人物轉身或精彩動作處。 | 偵測光流運動向量方差的峰值（Peak）。在峰值前半段將速度設為 `200%`，轉身動作最精彩影格瞬間降速至 `50%` 以慢動作呈現細節，結尾再拉回 `100%`。 |
| **Jump Cut** | **時間跳切與節奏跳躍**<br>同空間與機位下打破時間連續性快速跳切，具現代潮流感與視覺張力。 | 從同一個長原始影片中，截取多個間隔很短（例如 5~8 影格）的非連續區間，緊密 append 在同一軌道上，形成背景靜止、人物在音樂重拍上產生瞬移的特效。 |
| **Parallel Editing** | **平行交叉剪輯**<br>交替剪接兩個不同地點、同時發生的故事線，營造時空交錯感。 | 系統將素材庫依語意分類為走秀與幕後，在 `for` 迴圈中套用交替索引閘（`idx % 2 == 0`），使時間軸以 `走秀 ➡️ 幕後 ➡️ 走秀 ➡️ 幕後` 的模式交叉生成。 |
| **Split Screen** | **多分鏡畫面**<br>在畫面上同時呈現多個影像，適用於產品對稱展示。 | 將兩個素材同步 append 在 **Video Track 1 與 Video Track 2**。呼叫 API 幾何設定參數：左側視訊 `ZoomX=0.5, PanX=-480`，右側視訊 `ZoomX=0.5, PanX=480`，自動繪製對稱排版。 |
| **Association Montage**| **高密聯想蒙太奇**<br>在極短時長內伴隨鼓點或碎拍快速切換一組概念特寫，引發強烈意識聯想。 | 偵測配樂中的 32 分音符或連擊重拍，將剪輯步長（Step Duration）壓縮至 **3~5 影格**，連續拼接特寫鏡頭（`CloseUp`），營造視覺閃爍感。 |

---

## 🤖 AI Rhythmic Editor System Prompt (開機指令集)

當使用者（剪輯導演）向你（AI Assistant）發送以下形式的剪輯指令時：
> **「給我 {XX} 秒的影片，使用 {BGM名稱} 當作音樂，我的風格是 {風格語境}，把焦點放在 {焦點對象}」**

你必須立即扮演本套系統的**核心控制台**，讀取當前工作區的所有工具，並按照以下**標準作業程序 (SOP)** 自動執行：

### 📥 1. 語意解析與代碼映射
1. **設定影片總長度 (秒)**：
   * 將 `{XX}` 映射為實體變數 `MAX_DURATION_SEC = float({XX})`。
   * 時長換算影格數：`total_duration_frames = int(MAX_DURATION_SEC * fps)`。
2. **定位背景配樂 (BGM)**：
   * 在程式碼中尋找 `find_bgm(folder)`，將搜尋關鍵字改為 `"{BGM名稱}".lower()`。
3. **對齊風格與檢索焦點**：
   * 根據 `{風格語境}` 與 `{焦點對象}`，動態修改剪輯引擎中的 `semantic_prompts`（例如 `run_event_highlight_edit.py`），將其解耦並重寫為適用於任何主題的通用檢索詞（Generic Query Expansion）：
     * `"setup"` ➡️ `"{風格語境} {焦點對象} establishing opening setup background context"`
     * `"detail"` ➡️ `"{焦點對象} macro closeup details features focus craftsmanship"`
     * `"catwalk"` ➡️ `"{焦點對象} high energy dynamic action movement climax performance"`
     * `"finale"` ➡️ `"{焦點對象} grand finale outro logo branding packaging presentation end"`

### ⚡ 2. 快取與焦點預檢防禦 (GUI Sync Gotcha)
1. **特徵快取檢查**：
   * 檢查本機快取 `.cv_profile_cache.json` 是否已覆蓋所有候選影片。若有新影片或缺失，立即在背景呼叫 `python pre_cache_profiles.py`。
2. **GUI 焦點防錯鎖定**：
   * 執行 `python diag_timelines.py` 檢查達芬奇 GUI 當前聚焦的時間軸是否為目標時間軸。
   * **🚨 達芬奇 GUI 焦點問題**：若當前聚焦的非目標時間軸，你必須暫停並發出警示：「**請在 Resolve 軟體中雙擊該時間軸，確保編輯頁聚焦此時間軸，避免將素材 append 到錯誤的分頁！**」

### 🚀 3. 修改代碼與執行編譯
1. 使用 `replace_file_content` 工具，精確修改 `run_event_highlight_edit.py` 中的時長限制、音樂搜尋關鍵字與 CLIP 語意 Prompt。
2. 在終端機中執行：
   ```powershell
   python run_event_highlight_edit.py
   ```
3. 監控執行狀態，確保返回 `🎉 All tasks completed beautifully!` 且 Exit code 為 0。

### 📊 4. 實體數據驗證與呈報
1. 執行實體數據驗證：
   ```powershell
   python inspect_nanqu_work.py
   ```
2. 收集並彙整驗證數據：
   * 影片主軌總卡點片段數（如 25 cuts）。
   * 雙 Logo 置入影格起點與 `Zoom`/`Pan`/`Tilt` 物理屬性。
   * BGM 對齊百分比。
   * 100% 零重複素材驗證結果。
3. 以客觀、清晰的語調向使用者呈報，不使用任何浮誇修飾詞彙。

---

## 🛡️ 開源條款與貢獻者
* 本系統由專業影音研發團隊設計，旨在解決自動化高端電影剪接與宣傳片之高維美學生成痛點。
* 如有任何建議或自訂運鏡演算法，歡迎提交 PR 貢獻！ 🎬🍿
