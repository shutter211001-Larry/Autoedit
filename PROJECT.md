# DaVinci Resolve 21 AI Automated Rhythmic Cinematic Editor
## 📘 Project Blueprint & Developer Reference

This project is a high-performance **AI-powered rhythmic video editor** that interfaces directly with **DaVinci Resolve 21** via its Python API. It automatically cuts raw footage to the beats of a background music track, resolving critical editing challenges such as cross-framerate rendering phase differences, DSP analysis latencies, timeline cropping offsets, hand-held camera jitters, horizontal motion direction reversals, and professional brand outro packaging.

---

## 🌟 Key Features & Algorithmic Architectures

### 1. AI Camera Motion Director
* **4-Phase Narrative Transforming & Master-class Multi-axis Zoom/Pan/Rotation Hack**:
  To bypass Resolve's scripting API limitation which blocks writing dynamic transform keyframes in the Edit page, the system implements an industry-grade **"Multi-axis Adjustment Clip Opacity-Ramped Transform Hack"** to achieve 100% automated background multi-axis moves. By placing an Adjustment Clip on Video Track 2, setting static Zoom, Pan/Tilt, or RotationAngle, and calling API to write Fade-In/Out frames, we produce complex Hollywood-grade multi-axis movements (Push + Pan + Rotate) seamlessly:
  1. **【Setup】0s - 5s (Establishing)**: Stable atmosphere. `Zoom = 1.0`, `Rotation = 0.0`.
  2. **【Detail】5s - 12s (Craftsmanship)**: Smooth dynamic micro-push. Overlays an Adjustment Clip on Track 2, sets static `Zoom = 1.08`, and calls API to apply `FadeInFrames = 24` to smoothly push the scale forward.
  3. **【Catwalk Climax】12s - 20.8s (Runway Spins)**: Dynamic kinetic sway. Overlays Adjustment Clips on V2 alternating between static `RotationAngle = 3.5`, `PanX = 50` and `RotationAngle = -3.5`, `PanX = -50` with `FadeInFrames = 12` and `FadeOutFrames = 12` to trigger intense dynamic handheld action sweeps snapped to beats.
  4. **【Finale】20.8s - 25.0s (Brand Reveal)**: Master-class multi-axis outro. Places an Adjustment Clip on V2, **simultaneously writing** static `Zoom = 1.2`, `PanY = -60` (vertical tilt), and `RotationAngle = 1.5`, and calls `FadeInFrames = 30` (1.25s), producing a smooth, high-end composite push-up-and-tilt conclusion.

### 2. Motion Flow Smoothing & Envelope Protection
* **Motion Envelope**: Applies a **5-beat Moving Average Filter** to smooth the raw motion energy curve into a gentle, flowing sinusoidal wave.
* **Visual Inertia Defense**: Checks motion difference between adjacent cuts. If the absolute difference **`> 3.0`**, it applies a **`0.15` penalty** to discourage jarring visual transitions, ensuring smooth motion continuity.

### 3. High-Precision Transient Beat Detection
* Uses **FFmpeg** to transcode any compressed music format to standard Mono WAV in under 0.3 seconds.
* Implements a high-precision SciPy/NumPy falling-edge Short-Time Energy (RMS) sliding window onset detector to track exact music tempos and transient peaks.
* **Climax Target Alignment**: Automatically searches for the musical climax window and snaps its start frame perfectly to the timeline offset (`86400`).

### 4. Surgical Golden-Crop & Triple Shaky Defense Architecture
* To isolate and filter out high-shake intervals, camera repositioning adjustments, or out-of-focus wiggles, the system implements a highly rigorous triple-defense filtering pipeline:
  1. **Phase 1: 15% Smart Padding Margin**: Automatically masks out the first 15% and last 15% of each raw take (where button press impacts or release jitters usually occur). The search engine is strictly confined to the remaining **70% Pristine Mid-section**.
  2. **Phase 2: Rolling Motion Stability Scanner**: Downsamples frame dimensions by 99% to `160x90` in memory (filtering out fine-frequency high-detail movements like wind or hair, isolating macroscopic camera pans). Using a high-speed forward decoder (running **5.2x faster** than traditional seek decodes), it computes the rolling variance of camera motion vectors $\text{Var}(M[s : s+D])$ across a sliding window of size $D$. The optimization engine snaps the crop's In point to the absolute minimum variance window, placing only this rock-solid segment onto the timeline while **completely discarding the chaotic parts of the raw clip**.
  3. **Phase 3: Shaky Take Rejection (Bad Take Defense)**：If an entire raw file is extremely chaotic (e.g. running hand-held shots with no stable window whatsoever), and its lowest rolling variance remains above the safety threshold (`10.5`), the AI Director triggers a heavy **`-3.0 point penalty`** on that file, forcing the selector to **completely reject the chaotic asset** and choose a stable alternative from the pool, keeping bad takes 100% off the timeline.

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

### 11. AI-Driven Fusion Typography & Aesthetics
* **Programmatic Integration**: Leveraging Resolve's internal Fusion scripting namespace, an AI editor can dynamically instantiate Fusion compositions (Title Cards) on top of timeline clips and call `SetInput` programmatically to write high-end visual styles.
* **Aesthetic Presets for Robots**:
  To prevent raw or cheap looking fonts, the system defines three high-end design presets with exact node parameters to allow incoming bots to load premium typography styling instantly:

  #### ⚜️ Preset 1: Minimalist Luxury (The "Vogue" Serif)
  * **Aesthetic Tone**: Graceful, high-fashion, ultra-clean serif layout with generous breathing room. Ideal for premium cosmetics, luxury goods, fashion, or salon intros.
  * **Node Attributes**:
    * `Font` (English): `"Playfair Display"` or `"Didot"` or `"Cinzel"` (Premium Serifs)
    * `Font` (Chinese Compatible): **`"Noto Serif CJK TC"`** (思源宋體 - Light/Thin) or **`"Microsoft JhengHei"`** (微軟正黑體 - Light)
    * `Style`: `"Regular"` or `"Light"`
    * `Size`: `0.062` (Elegant small scaling with massive negative space)
    * `Tracking` (Character Spacing): `2.2` to `2.4` (Generous spacing produces an exquisite, magazine-like editorial presence)
    * `Line Spacing`: `1.2`
    * `Color` (Soft Warm White): `Red = 0.98`, `Green = 0.97`, `Blue = 0.95`
    * `HAnchor` (Alignment): `1` (Center Aligned)
    * `Soft Shadow` (Shadow Node): `SoftnessX = 8.0`, `SoftnessY = 8.0`, `Alpha = 0.15` (Whisper-thin shadow for soft depth)

  #### ⚡ Preset 2: Neo-Noir Tech (The "Cyber-Tech" Bold)
  * **Aesthetic Tone**: Aggressive, geometric sans-serif with vibrant glows. Perfect for dynamic tech showcase, streetwear promos, high-energy clips, or EDM visualizers.
  * **Node Attributes**:
    * `Font` (English): `"Outfit"` or `"Montserrat"` or `"Space Grotesk"` (Geometric Sans-Serif)
    * `Font` (Chinese Compatible): **`"Noto Sans CJK TC"`** (思源黑體 - Heavy/Black/Bold) or **`"Microsoft JhengHei"`** (微軟正黑體 - Bold)
    * `Style`: `"Extra Bold"` or `"Black"`
    * `Size`: `0.11` (Strong focal footprint)
    * `Tracking`: `1.05` (Tight modern spacing)
    * `Color` (Pure Stark White): `Red = 1.0`, `Green = 1.0`, `Blue = 1.0`
    * `Glow1` (Glow Node):
      * `Filter`: `"Glow"`
      * `GlowSize`: `12.0` (Soft scatter scale)
      * `Blend`: `0.45` (Vibrant neon blend magnitude)
      * *Neon Teal Variation*: `GlowRed = 0.0`, `GlowGreen = 0.95`, `GlowBlue = 0.85`
      * *Acid Pink Variation*: `GlowRed = 1.0`, `GlowGreen = 0.05`, `GlowBlue = 0.45`

  #### 📐 Preset 3: Modern Editorial (The "Swiss Editorial")
  * **Aesthetic Tone**: Stark, asymmetric, left-aligned sans-serif layout. Emulates high-end print design editorial magazines.
  * **Node Attributes**:
    * `Font` (English): `"Inter"` or `"Helvetica Neue"` or `"DM Sans"` (Neutral Sans-Serif)
    * `Font` (Chinese Compatible): **`"Noto Sans CJK TC"`** (思源黑體 - Medium/Regular) or **`"Microsoft JhengHei"`** (微軟正黑體 - Regular)
    * `Style`: `"Medium"` or `"Bold"`
    * `Size`: `0.082`
    * `Tracking`: `1.0` (Standard crisp spacing)
    * `HAnchor`: `0` (Force Left Aligned)
    * `Color` (Matte Charcoal): `Red = 0.12`, `Green = 0.12`, `Blue = 0.12` (Commonly overlayed on flat cream/beige cards)
    * `Decoration`: Zero artificial glows or shadows. Pure flat layout.

* **🤖 Robot Python API Execution Blueprint**:
  ```python
  # 1. Instantiate Fusion composition on a TimelineItem
  comp = timeline_item.AddFusionComp()
  
  # 2. Locate the Text tool node (default named 'Text1' or Text+ inside templates)
  text_tool = comp.FindTool("Text1")
  
  # 3. Apply the Vogue Serif luxury styling programmatically
  text_tool.SetInput("Font", "Playfair Display")
  text_tool.SetInput("Style", "Regular")
  text_tool.SetInput("Size", 0.062)
  text_tool.SetInput("Tracking", 2.2)
  text_tool.SetInput("Red", 0.98)
  text_tool.SetInput("Green", 0.97)
  text_tool.SetInput("Blue", 0.95)
  text_tool.SetInput("HAnchor", 1.0) # Center
  
  # 4. Modify nested Shadow or Glow properties if present in template
  shadow_tool = comp.FindTool("Shadow1")
  if shadow_tool:
      shadow_tool.SetInput("SoftnessX", 8.0)
      shadow_tool.SetInput("SoftnessY", 8.0)
      shadow_tool.SetInput("Alpha", 0.15)
  ```

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

## 🎬 Advanced Cinematic Editing Techniques & AI Integration Guide

To break away from simple linear cuts, this editing system abstracts industry-standard cinematic editing techniques into algorithmic models that can be programmatically compiled via the DaVinci Resolve API. Below is the catalog of supported techniques and their exact integration mechanics:

### 1. J-Cuts & L-Cuts (Audio-Video Offset Transitions)
* **Definition**: Letting the audio from the next clip bleed in early before the visual cut (J-Cut, "hear it first"), or letting the audio from the current clip linger while the visual already switched to the next clip (L-Cut, "visual transition").
* **AI Algorithmic Integration**:
  * In DaVinci Resolve, Video and Audio tracks are separate entities during `AppendToTimeline`.
  * **J-Cut**: Shift the Audio Track's `startFrame` to the left (`startFrame = startFrame - offset_frames`, typically 5-10 frames) while keeping the Video Track's start frame snapped to the beat point.
  * **L-Cut**: Extend the previous clip's Audio Clip end frame into the next visual scene while cutting the video track early.

### 2. Match Cuts (Compositional & Kinetic Matching)
* **Definition**: Seamlessly transitioning between two consecutive shots that share similar motion direction, camera speeds, or visual frame compositions.
* **AI Algorithmic Integration**:
  * **Kinetic Match (Motion Match)**: Query the `.cv_profile_cache.json` for motion vectors of adjacent candidate clips. If Clip A ends with a pan right ($dx > 0$), force the selector to only pick Clip B that starts with a pan right ($dx > 0$) for a fluid kinetic sweep.
  * **Graphic Match (Compositional Match)**: Extract high-dimensional CLIP vectors of keyframes from consecutive candidate clips. Select adjacent clips that maximize cosine similarity on visual layouts (e.g., both having a circular object centered in the frame), producing a smooth transition.

### 3. Speed Ramping (Dynamic Time Remapping)
* **Definition**: Varying clip playback speeds dynamically within a single cut (e.g. Fast ➡️ Slow-Motion ➡️ Fast-Cut) to emphasize motion climax or model rotations.
* **AI Algorithmic Integration**:
  * Call Resolve API's `timelineItem.SetClipSpeed(speed, true)` or generate Retime speed points dynamically.
  * Identify high-motion segments of the clip (via rolling variance Peaks). Speed up the introduction to `200%`, ramp down the climax action to `50%` to savor details, and pull back to `100%` before the cut.

### 4. Jump Cuts (Temporal Discontinuity Editing)
* **Definition**: Deliberately jumping forward in time within the same scene/camera setup, creating a high-fashion, staccato effect of sudden subject shifts.
* **AI Algorithmic Integration**:
  * Extract a sequence of non-continuous sub-windows from a single raw take:
    $$\text{Cut}_n = [s + n \times (D + G), s + n \times (D + G) + D]$$
    (where $D$ is the cut duration, and $G$ is the skipped frame Gap).
  * Align and append these sub-windows continuously on the timeline, generating a stylized staccato progression.

### 5. Parallel Editing / Cross-Cutting (Narrative Interleaving)
* **Definition**: Interleaving two or more separate narrative threads occurring simultaneously in different spaces to show contrast or build suspense.
* **AI Algorithmic Integration**:
  * Partition the raw asset pool into distinct semantic categories (e.g., Category A for runway actions, Category B for backstage context).
  * Interleave them dynamically inside the timeline builder loop:
    $$\text{TargetCategory} = \text{Category A} \text{ if } (idx \pmod 2 == 0) \text{ else } \text{Category B}$$
    creating a perfectly interleaved narrative weave (`A ➡️ B ➡️ A ➡️ B`).

### 6. Split Screen (Multi-Window Symmetrical Layouts)
* **Definition**: Splitting the screen layout to display multiple video clips simultaneously.
* **AI Algorithmic Integration**:
  * Append multiple clips on the same timeline index across **Video Track 1 & Video Track 2**.
  * Use `timelineItem.SetProperty()` to dynamically offset geometry:
    * Left Clip (Track 1): `ZoomX = 0.5`, `ZoomY = 1.0`, `PanX = -480.0`
    * Right Clip (Track 2): `ZoomX = 0.5`, `ZoomY = 1.0`, `PanX = 480.0`
    This renders a perfectly balanced side-by-side vertical split-screen on a 1920x1080 canvas.

### 7. Association Montages (High-Density Collage Flash)
* **Definition**: Running a series of extremely fast closeups to build visual associations during a dramatic build-up or micro-beats.
* **AI Algorithmic Integration**:
  * Detect 32nd notes or rolling snare-roll drum sequences in the audio.
  * Compress the timeline cut duration down to **3-5 frames** and compile 5-8 ultra-fast macro closeups (`CloseUp`), creating a premium flash montage.

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
   * Align `{Visual Style}` and `{Focus Object}` to decoupled, generic `semantic_prompts` inside the editing engine (e.g. `run_event_highlight_edit.py`) to support any general video theme (Generic Query Expansion):
     * `"setup"` ➡️ `"{Visual Style} {Focus Object} establishing opening setup background context"`
     * `"detail"` ➡️ `"{Focus Object} macro closeup details features focus craftsmanship"`
     * `"catwalk"` ➡️ `"{Focus Object} high energy dynamic action movement climax performance"`
     * `"finale"` ➡️ `"{Focus Object} grand finale outro logo branding packaging presentation end"`

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
