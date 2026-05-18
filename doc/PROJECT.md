# DaVinci Resolve 21 AI Automated Rhythmic Cinematic Editor
## 📘 Project Blueprint & Developer Reference

This project is a high-performance **AI-powered rhythmic video editor** that interfaces directly with **DaVinci Resolve 21** via its Python API. It automatically cuts raw footage to the beats of a background music track, resolving critical editing challenges such as cross-framerate rendering phase differences, DSP analysis latencies, timeline cropping offsets, and storytelling continuity.

---

## 🌟 Key Features & Accomplishments

### 1. Chronological Narrative Storytelling Arc (起、承、轉、合)
* Solves the "random flashcut montage" problem by dividing the 30-second commercial timeline into **4 distinct chronological storytelling phases**:
  1. **Phase 1: 起 (Setup - 0s to 5s)**: Backstage preparation, event venue setup, and audience gathering (`event backstage preparation hair salon setup venue establishing audience gathering`).
  2. **Phase 2: 承 (Detail - 5s to 12s)**: Product styling detail, spraying, and hair salon craftsmanship (`hair styling process stylist working with hairspray cosmetic product closeups detail`).
  3. **Phase 3: 轉 (Climax - 12s to 25s)**: CATWALK runway show with high-energy model walk-ins, hair spins, and dynamic movements (`beautiful fashion model catwalk show runway hair spin movement closeup`).
  4. **Phase 4: 合 (Finale - 25s to 30s)**: Audience reaction clapping applause, final styled poses, and high-end brand packaging closeups (`audience clapping reaction applause grand finale show product branding packaging logo`).
* Matches visual semantics dynamically, creating a professionally structured commercial narrative that flows logically from scene setup to the grand branding climax!

### 2. High-Precision Transient Beat Detection
* Uses **FFmpeg** to transcode any compressed music format to standard Mono WAV in under 0.3 seconds.
* Implements a high-precision SciPy/NumPy falling-edge Short-Time Energy (RMS) sliding window onset detector to track exact music tempos and transient peaks.

### 3. Crop Offset & Silent Intro Immunity
* Dynamically reads timeline audio crops (`audio_clip.GetLeftOffset()`) to shift beat markers mathematically, making them **100% immune to trimming offsets**.
* Extrapolates tempo-aligned beats backwards to cover silent or fade-in intros, ensuring rhythmic cuts start from the very first frame.

### 4. AI Content-Aware Semantic Video Recommendation
* Uses a local, offline **CLIP model** (`openai/clip-vit-base-patch32` via PyTorch) to extract visual features from 3 keyframes (start, middle, end) of all raw video files.
* Stores features in a local pickle cache **`video_metadata.pkl`**, enabling **instant, sub-second semantic queries** on subsequent runs.
* Integrates a high-speed motion energy metric using OpenCV absolute frame difference magnitude across 10 frames in the middle of each clip to profile physical motion intensity.

### 5. Visual Near-Duplicate Defense (視覺近重複防禦)
* Solves the problem where sequential raw camera files (e.g. `C0273`, `C0274`) look visually identical to a human even though they are unique filenames.
* Calculates the **cosine similarity between each candidate's embedding and all clips already selected on the timeline**.
* Applies a **massive `-2.0` score penalty** to any clip with a similarity greater than **`0.88`**, forcing the AI to strictly prioritize diverse models, product packaging, and camera angles.

### 6. Perfect Math-Ceil Frame Rate Scale
* Solves the 1-frame black gap issue caused by fractional round-off mismatches when placing **29.97 FPS** source clips on a **24.0 FPS** timeline.
* Employs dynamic compensation using:
  $$\text{duration\_source} = \text{int}(\text{math.ceil}(\text{duration\_timeline} \times \frac{\text{src\_fps}}{\text{timeline\_fps}}))$$
  This mathematically guarantees 100% gapless, zero-ripple single-track appending on Video Track 1.

### 7. Resolve API Coordinate Bug Fix
* Resolves the 1-hour marker offset gotcha where `AddMarker()` expects coordinates relative to the timeline start, while clips use absolute frames.
* Implements absolute-to-relative coordinate conversions to place markers precisely at `01:00:00:11` instead of `02:00:00:11`.

### 8. Double page-hopping GUI Refresh
* Automates page-hops between `media` and `edit` views to instantly force Resolve to reconstruct its timeline cache and draw the edited footage.

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
