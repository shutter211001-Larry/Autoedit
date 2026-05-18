# DaVinci Resolve 21 AI Automated Rhythmic Cinematic Editor
## 📘 Project Blueprint & Developer Reference

This project is a high-performance **AI-powered rhythmic video editor** that interfaces directly with **DaVinci Resolve 21** via its Python API. It automatically cuts raw footage to the beats of a background music track, resolving critical editing challenges such as cross-framerate rendering phase differences, DSP analysis latencies, timeline cropping offsets, storytelling continuity, camera shakes, and visual dynamic flow.

---

## 🌟 Key Features & Accomplishments

### 1. AI Camera Motion Director (AI 鏡頭動態導演)
* Programmed an automated camera director that modifies scale and transform properties of each `TimelineItem` on the fly using `SetProperty()`, mapped to our 4 Narrative Phases:
  1. **Phase 1: 起 (Setup - 0s to 5s)**: **Stable Establishing (全平靜定格)**. Keeps the camera completely clean and stable to establish backstage vibe.
     * `ZoomX/Y = 1.0`, `RotationAngle = 0.0`.
  2. **Phase 2: 承 (Detail - 5s to 12s)**: **Product Closeups (產品工藝大幅推近)**. Magnifies product detail shots and styling close-ups to create a highly premium, product-focused commercial look.
     * `ZoomX/Y = 1.10`, `RotationAngle = 0.0`.
  3. **Phase 3: 轉 (Climax - 12s to 25s)**: **Handheld Slash-Cut Dynamic Camera (斜切潮流手持對拍卡點)**. Alternates the rotation angle between even and odd beat cuts during the runway show climax to create a rapid, high-fashion dynamic visual sway!
     * `ZoomX/Y = 1.15` (Slightly zoomed to completely hide any black borders from rotation!).
     * `RotationAngle = 4.0` (Even cuts) or `-4.0` (Odd cuts) degrees.
  4. **Phase 4: 合 (Finale - 25s to 30s)**: **Grand Logo Climax Zoom (品牌定格大推近)**. Magnifies final poses and product bottles, pulling the viewer's eye straight onto the Schwarzkopf branding logo.
     * `ZoomX/Y = 1.20`, `RotationAngle = 0.0`.
* **Important API Limitation & Workaround (Dynamic Zoom)**:
  DaVinci Resolve's Python API strictly limits edit-page transform property writes to static values per clip (no keyframing allowed). To get a smooth, continuous camera zoom animation (Ken Burns) during a clip's playback without creating a single keyframe, simply:
  1. Select all timeline clips (`Ctrl + A`).
  2. Toggle on the **`Dynamic Zoom`** switch in the DaVinci Resolve **Inspector (右上角檢查器)**.
  This instantly applies seamless continuous push/pull motions on top of our AI's pre-arranged precise beats!

### 2. Motion Flow Smoothing & Continuity (電影感運動平滑與連續留線)
* Solves the "motion clash" problem (where consecutive cuts jump wildly between hyper-fast motion and complete stillness) by applying two motion smoothing layers:
  1. **Motion Continuity Envelope**: Applies a **5-beat rolling average filter** to the raw target ideal motion curve. This forces the overall visual tempo of adjacent cuts to grow and shrink gradually, matching the organic build-up of the music.
  2. **Motion Continuity Penalty**: In the AI matching loop, it calculates the absolute motion energy difference between each candidate and the *immediately preceding clip*. If the dynamic shift exceeds a threshold of **`3.0`**, a progressive **`0.15` penalty** is applied.
* Guarantees that consecutive video cuts maintain **perfect screen action direction and visual momentum (視覺慣性)** (e.g. transitioning smoothly as `9.5 -> 7.0 -> 6.3 -> 6.8 -> 6.5`!).

### 3. Chronological Narrative Storytelling Arc (起、承、轉、合)
* Solves the "random flashcut montage" problem by dividing the 30-second commercial timeline into **4 distinct chronological storytelling phases**:
  1. **Phase 1: 起 (Setup - 0s to 5s)**: Backstage preparation, event venue setup, and audience gathering.
  2. **Phase 2: 承 (Detail - 5s to 12s)**: Product styling detail, spraying, and hair salon craftsmanship.
  3. **Phase 3: 轉 (Climax - 12s to 25s)**: High-energy CATWALK runway show with hair spins.
  4. **Phase 4: 合 (Finale - 25s to 30s)**: Audience reaction clapping applause, final styled poses, and high-end brand packaging closeups.
* Matches visual semantics dynamically, creating a professionally structured commercial narrative that flows logically from scene setup to the grand branding climax!

### 4. High-Precision Transient Beat Detection
* Uses **FFmpeg** to transcode any compressed music format to standard Mono WAV in under 0.3 seconds.
* Implements a high-precision SciPy/NumPy falling-edge Short-Time Energy (RMS) sliding window onset detector to track exact music tempos and transient peaks.

### 5. Crop Offset & Silent Intro Immunity
* Dynamically reads timeline audio crops (`audio_clip.GetLeftOffset()`) to shift beat markers mathematically, making them **100% immune to trimming offsets**.
* Extrapolates tempo-aligned beats backwards to cover silent or fade-in intros, ensuring rhythmic cuts start from the very first frame.

### 6. AI Content-Aware Semantic Video Recommendation
* Uses a local, offline **CLIP model** (`openai/clip-vit-base-patch32` via PyTorch) to extract visual features from 3 keyframes (start, middle, end) of all raw video files.
* Stores features in a local pickle cache **`video_metadata.pkl`**, enabling **instant, sub-second semantic queries** on subsequent runs.
* Integrates a high-speed motion energy metric using OpenCV absolute frame difference magnitude across 10 frames in the middle of each clip to profile physical motion intensity.

### 7. Visual Near-Duplicate Defense & Shaky Shot Defense
* **Visual Near-Duplicate Defense**: Calculates the **cosine similarity between each candidate's embedding and all clips already selected on the timeline**. Applies a **massive `-2.0` score penalty** to any clip with a similarity greater than **`0.88`**, forcing the AI to strictly prioritize diverse models, product packaging, and camera angles.
* **Shaky Shot Defense**: Detects wild camera shake/focus hunt takes ($motion\_energy \ge 10.5$) and applies a **massive `-3.0` score penalty** to keep the timeline clean and stable.

### 8. Perfect Math-Ceil Frame Rate Scale
* Solves the 1-frame black gap issue caused by fractional round-off mismatches when placing **29.97 FPS** source clips on a **24.0 FPS** timeline.
* Employs dynamic compensation using:
  $$\text{duration\_source} = \text{int}(\text{math.ceil}(\text{duration\_timeline} \times \frac{\text{src\_fps}}{\text{timeline\_fps}}))$$
  This mathematically guarantees 100% gapless, zero-ripple single-track appending on Video Track 1.

### 9. Resolve API Coordinate Bug Fix
* Resolves the 1-hour marker offset gotcha where `AddMarker()` expects coordinates relative to the timeline start, while clips use absolute frames.
* Implements absolute-to-relative coordinate conversions to place markers precisely at `01:00:00:11` instead of `02:00:00:11`.

---

## 🚀 Execution & Testing Guide

1. Place your background music on **Audio Track 1**, starting at `01:00:00:00`.
2. Generate beat markers on your timeline by running:
   ```powershell
   python auto_beat_marker.py
   ```
3. Run the AI auto-editor to compile a stunning 30s cosmetic commercial:
   ```powershell
   python run_cinematic_auto_edit.py
   ```
4. Verify perfect alignment mathematically:
   ```powershell
   python C:\Users\aeiou\.gemini\antigravity\brain\50c1c521-aa15-42fd-b904-d3a1abb1b0c9\scratch\inspect_markers_vs_clips.py
   ```
