# DaVinci Resolve 21 AI Automated Rhythmic Cinematic Editor
## 📘 Project Blueprint & Developer Reference

This project is a high-performance **AI-powered rhythmic video editor** that interfaces directly with **DaVinci Resolve 21** via its Python API. It automatically cuts raw footage to the beats of a background music track, resolving critical editing challenges such as cross-framerate rendering phase differences, DSP analysis latencies, timeline cropping offsets, hand-held camera jitters, horizontal motion direction reversals, and professional brand outro packaging.

---

## 🌟 Key Features & Algorithmic Architectures

### 1. AI Camera Motion Director
* **Narrative 4-Phase Transform Packaging Model**: Leverages the Resolve API `SetProperty()` to layer dynamic zoom and rotation values on top of cuts:
  1. **【Setup】0s - 5s (Establishing & Backstage)**: Flat stable atmosphere. Holds `Zoom = 1.0`, `Rotation = 0.0`.
  2. **【Detail】5s - 12s (Hair Styling & Product Closeups)**: Dynamic push-in. Applies `Zoom = 1.05`, `Rotation = 0.0` to lock visual attention on craftsmanship.
  3. **【Catwalk Climax】12s - 20.8s (Runway Showcase & Spins)**: Alternating slash-cut. Amplifies visuals with `Zoom = 1.12` and applies **alternating tilt angles of `3.5°` and `-3.5°`** on beat points, generating an intense hand-held rhythmic slam effect.
  4. **【Finale】20.8s - 25.0s (Applauding & Brand Reveal)**: Outro focus. Applies `Zoom = 1.18`, `Rotation = 0.0` to highlight brand packaging and applause.
* **Instant Dynamic Zoom (Ken Burns)**: Select all clips (`Ctrl + A`) in the edit viewport and toggle **"Dynamic Zoom"** in the Inspector to combine rhythmic cuts with premium camera push-pull movements.

### 2. Motion Flow Smoothing & Envelope Protection
* **Motion Envelope**: Applies a **5-beat Moving Average Filter** to smooth the raw motion energy curve into a gentle, flowing sinusoidal wave.
* **Visual Inertia Defense**: Checks motion difference between adjacent cuts. If the absolute difference **`> 3.0`**, it applies a **`0.15` penalty** to discourage jarring visual transitions, ensuring smooth motion continuity.

### 3. High-Precision Transient Beat Detection
* Uses **FFmpeg** to transcode any compressed music format to standard Mono WAV in under 0.3 seconds.
* Implements a high-precision SciPy/NumPy falling-edge Short-Time Energy (RMS) sliding window onset detector to track exact music tempos and transient peaks.
* **Climax Target Alignment**: Automatically searches for the musical climax window and snaps its start frame perfectly to the timeline offset (`86400`).

### 4. Smart Padding Margin (Button Shake Mitigation)
* Implements a **15% Safety Margin Guard** on both ends of raw clips. It completely bypasses the high-shake intervals typical when pressing the record/stop buttons, cropping clips exclusively from the pristine remaining 70% middle section.

### 5. Rolling Motion Stability Scanner
* Downsamples video frame dimensions by 99% to `160x90` in memory (filtering out wind, hair movement, etc. to isolate camera motion) and runs a `downsample_step = 6` forward decoder (**5.2x speedup** over seek decodes).
* Computes rolling variance $\text{Var}(M[s : s+D])$ to detect smooth consistent pans or hovers and applies a heavy Peak Shake Penalty to filter out sudden hand bumps.

### 6. Motion Vector Monotonicity & Direction Reversal Defense
* **1D Horizontal Projection Profile Cross-Correlation**:
  Summates grayscale pixel intensities vertically to extract a 1D horizontal signature $P(x)$ for each frame. Slides adjacent profile arrays to track sub-pixel horizontal camera translation velocity $dx(t)$ at warp speed.
* **Direction Monotonicity Score**:
  $$\text{Monotonicity Ratio} = \frac{\max(\sum [dx > 0], \sum [dx < 0])}{\text{Total Active Frames}}$$
  If the monotonicity score is **`< 90%`** (indicating back-and-forth movement), a heavy **Reversal Blocking Penalty** is applied, filtering out pendulum motions to keep pans clean, stable, and single-directional.

### 7. 25-Second Commercial Standard & Capping
* **Storytelling Wide Cap**: Caps audience and venue establishing wide-angle shots to **exactly 2 clips** (Cut #1 and Cut #25). Intermediate cuts are strictly restricted to CloseUp and Medium runway takes.
* **Zero-Repetition Math**: 25.0 seconds compiles exactly **35 beat cuts**. With an asset pool of 36 unique dynamic takes, this fits perfectly into the **Zero-Repetition Sweet Spot**, ensuring a completely unique clip on every single beat!

### 8. Global Motion Profile Cache (`.cv_profile_cache.json`)
* Decouples the caching layer from timeline properties. It profiles raw clips once, indexing full-length frame-by-frame motion vectors under their absolute paths.
* Any subsequent re-run, timing adjustment, or duration change loads profiles from the JSON cache, completing the entire timeline rebuild in **0.01 seconds**!

### 9. Side-by-Side Brand Outro Overlay (BC & Schwarzkopf)
* Automatically adds **Video Track 2 & 3** and overlays **BC LOGO** & **Schwarzkopf LOGO** side-by-side during the Finale section (starts at **20.8s / 86895f**).
* **Precise Geometry**:
  * Shared scaling: `Zoom = 0.35`
  * **BC Logo (V2)**: `Pan = -260.0`, `Tilt = -50.0`
  * **Schwarzkopf Logo (V3)**: `Pan = 260.0`, `Tilt = -50.0`

### 10. Gapless math.ceil Sync & Coordinate Offset Correction
* Employs a ceiling math formula to prevent 1-frame black gap rendering glitches when placing **29.97 FPS** source files on a **24.0 FPS** timeline:
  $$\text{duration\_source} = \text{int}(\text{math.ceil}(\text{duration\_timeline} \times \frac{\text{src\_fps}}{\text{timeline\_fps}}))$$
* **Coordinate Correction**: Automatically subtracts timeline offset (`86400`) from marker coordinates to align Resolve's relative `AddMarker` input with absolute timeline coordinates.

---

## 📂 Toolbox Directory & Reference Manual

### 🎬 Main Compilers & Editors
* **`run_event_highlight_edit.py`**:
  * **Description**: Main event highlight compiler. Orchestrates 2-beat downsampling, button shake margins, global profile cache retrieval, slash-cut tilt packing, BGM climax matching, side-by-side logo placements on V2/V3, and automatic node-graph grade cloning.
  * **Run**: `python run_event_highlight_edit.py`
* **`create_semantic_timeline.py`**:
  * **Description**: Builds and restores the `"Sam前導片_高能行銷版"` timeline, syncs music climax, and generates fully aligned subtitle SRT files.
  * **Run**: `python create_semantic_timeline.py`
* **`run_cinematic_auto_edit.py`**:
  * **Description**: Legacy 30s envelope-based automatic video generator.

### ⚡ Data & Caching Engines
* **`pre_cache_profiles.py`**:
  * **Description**: **Runs 100% independently of DaVinci Resolve**. Scans raw directories in the background, extracts motion vector signatures and directionality metrics for all 65 video assets, and compiles `.cv_profile_cache.json`.
  * **Run**: `python pre_cache_profiles.py`

### 🔍 Diagnostics & Analyzers
* **`stability_analyzer_hyper_fast.py`**:
  * **Description**: Evaluates camera stability curves on single clips via rolling optical flow.
  * **Run**: `python stability_analyzer_hyper_fast.py`
* **`direction_stability_analyzer.py`**:
  * **Description**: Computes 1D projection correlation curves on single clips to identify direction reversals.
  * **Run**: `python direction_stability_analyzer.py`
* **`diag_timelines.py`**:
  * **Description**: Diagnostics tool. Lists active timelines, tracks, clip counts, and prints which timeline currently holds GUI focus.
  * **Run**: `python diag_timelines.py`

### 🧪 Validators & Loaders
* **`inspect_nanqu_work.py`**:
  * **Description**: Database validation utility. Directly queries the active Resolve project to mathematically verify track contents, logo coordinates (Pan/Zoom/Tilt), zero-repetition percentages, and audio synchronization.
  * **Run**: `python inspect_nanqu_work.py`
* **`reimport_assets.py`**:
  * **Description**: Safety media pool asset loader. Creates the parent Master folders recursively and checks for duplicate imports.
  * **Run**: `python reimport_assets.py`

---

## 🤖 AI Rhythmic Editor System Prompt (Boot Commands)

When the user (Editing Director) sends you (AI Assistant) a command in the following format:
> **"Give me {XX} seconds of video, use {BGM Name} as music, my style is {Visual Style}, and focus on {Focus Object}"**

You must immediately act as the **Core Controller** of this editing system, read the active workspace tools, and execute the following **Standard Operating Procedure (SOP)**:

### 📥 1. Parse Input Parameters & Map Variables
1. **Target Duration**:
   * Map `{XX}` to the実體變數 `MAX_DURATION_SEC = float({XX})`.
   * Total frame constraint: `total_duration_frames = int(MAX_DURATION_SEC * fps)`.
2. **Audio Track (BGM)**:
   * Modify the search keyword in the `find_bgm(folder)` function from `indian walk` to `"{BGM Name}".lower()`.
3. **Semantics & CLIP Search Prompts**:
   * Align `{Visual Style}` and `{Focus Object}` to dynamic `semantic_prompts` inside `run_event_highlight_edit.py`:
     * `"setup"` ➡️ `"{Visual Style} {Focus Object} event venue backstage preparation"`
     * `"detail"` ➡️ `"{Focus Object} cosmetic closeups styling craftsmanship detail"`
     * `"catwalk"` ➡️ `"{Focus Object} beautiful fashion model runway catwalk spin movement closeup"`
     * `"finale"` ➡️ `"{Focus Object} grand finale applause brand packaging logo"`

### ⚡ 2. Cache & GUI Focus Pre-flight Checks (GUI Sync Gotcha)
1. **Motion Profile Cache Check**:
   * Verify if the local cache file `.cv_profile_cache.json` covers all assets. If missing or new videos are added, run `python pre_cache_profiles.py` in the background first.
2. **GUI Focus Validation**:
   * Run `python diag_timelines.py` to confirm the currently open GUI tab name in Resolve.
   * **🚨 Resolve API Focus Gotcha**: If the open tab does not match the target timeline (e.g. `'南區工作'`), you must halt and alert the user:
     *"Please double-click the timeline in your Resolve Media Pool to focus it in your GUI editor to prevent Resolve from appending clips to the wrong tab!"*

### 🚀 3. Modify Code & Compile
1. Use `replace_file_content` to edit `run_event_highlight_edit.py` with the parsed duration, BGM query name, and CLIP semantic prompts.
2. Run the main compiler in the terminal:
   ```powershell
   python run_event_highlight_edit.py
   ```
3. Monitor terminal output, checking for `🎉 All tasks completed beautifully!` with exit code 0.

### 📊 4. Database Validation & Report
1. Execute the database inspector to confirm the physical track layout:
   ```powershell
   python C:\Users\larrywu\.gemini\antigravity\brain\878978ab-d3f5-418c-88e5-9314eb79fe0f\scratch\inspect_nanqu_work.py
   ```
2. Gather metrics (total cuts, logo Pan/Zoom/Tilt properties, BGM lengths, zero-repetition percentages).
3. Report the completion state to the director in a highly professional, humble, and concise manner, avoiding overconfident or boastful vocabulary.
