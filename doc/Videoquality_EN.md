# 🎬 Smart Automated Editing Styles & Logics Manual (Videoquality - EN)

This reference manual documents the supported editing styles, mathematical models, and backend algorithmic logics implemented in the system.

---

## 📂 Core Editing Styles & Logics

### 1. Beat-Based Rhythmic Edit
* **Design Philosophy**: Video cut points snap precisely to the rhythm and energy transients of the background music.
* **Algorithmic Logic**:
  * **Audio Onset Detection**: Uses FFmpeg to transcode the music file into a standard WAV, and employs a Short-Time Energy (RMS) sliding window via SciPy to detect energy first-order derivative falling edges, locking precise beat positions.
  * **Climax Target Alignment**: Computes the sliding window total energy of the background track, locates the window containing the maximum energy peak, and aligns the start of this climax section perfectly to the timeline start frame (`86400`).
  * **Beats Downsampling**: Applies downsampling ratios based on narrative structure. For opening and closing sections (Setup/Finale), it uses a higher downsampling rate (e.g. cutting every 4 beats to keep clip durations longer and emotions stable); for the catwalk climax, it uses a tighter downsampling rate (e.g. cutting every 2 beats to build visual tempo).

### 2. SRT Semantic Timeline Editing
* **Design Philosophy**: Performs structured narrative reordering based on dialogue and speech content, outputting millisecond-aligned subtitle files automatically.
* **Algorithmic Logic**:
  * **AIDA Narrative Reordering**: Reads the raw footage alongside its original `SRT` file, and rearranges the raw footage slices on the timeline based on a predetermined marketing AIDA model (Hook ➡️ Intro ➡️ Core Curriculum ➡️ Endorsement ➡️ CTA) sequence parameters.
  * **Adaptive Timecode Shifting**: When raw clips are rearranged, the solver extracts the original subtitle blocks and re-computes their start and end timecode timestamps relative to the new timeline speed and sequence order with millisecond precision, outputting a fully synchronized, updated `SRT` file.

### 3. Symmetrical Sizing & Transform Reframing
* **Design Philosophy**: Since the Resolve Scripting API does not support dynamic keyframing, this style uses static geometry values in combination with rapid cuts to simulate camera movement and kinetic energy.
* **Algorithmic Logic**:
  * **4-Phase Geometry Sizing**:
    * **Setup**: `Zoom = 1.0`, keeping the original frame composition.
    * **Detail**: `Zoom = 1.10`, slightly magnifying the frame to highlight product labeling and stylistic details.
    * **Catwalk Climax**: `Zoom = 1.15`.
    * **Finale**: `Zoom = 1.20`, pulling the scale close to frame branding logos and model freeze-frames.
  * **Alternating Symmetrical Tilts**: During the Catwalk Climax stage, even cuts are written with static `RotationAngle = 4.0` while odd cuts are written with static `RotationAngle = -4.0`. The abrupt perspective jump cuts create visual kinetic energy snapped to beats.
  * **Aspect Ratio Scaling Compensation**: When placing horizontal source assets (16:9) onto a vertical timeline (9:16), the engine automatically applies a **`3.16`x proportional magnification multiplier** to the `Zoom` value, seamlessly filling the canvas.

### 4. Camera Stability & Reversal Defense
* **Design Philosophy**: Purges manual camera shake wiggles, masks button-press jitters, and prevents dizziness caused by rapid back-and-forth panning.
* **Algorithmic Logic**:
  * **15% Smart Padding Margin**: Automatically masks out the first 15% and last 15% of each raw asset (where hand-shakes from button presses usually occur), strictly restricting the rolling stability window search to the remaining **70% Pristine Mid-section**.
  * **Rolling Motion Stability Scanner**: Downsamples frame dimensions by 99% to `160x90` in memory (filtering out high-frequency fine details, isolating macroscopic camera pans). Using a high-speed forward-only jump-frame decoder, it computes camera motion vector variance. The crop In point is snapped to the lowest variance window.
  * **Shaky Take Rejection**: If an entire raw clip is extremely chaotic and its lowest variance window remains above the safety threshold (`10.5`), the AI director applies a heavy **`-3.0 point penalty`**, completely discarding the file from the timeline candidate sequence.
  * **1D Horizontal Projection Profile Cross-Correlation (Direction Reversal Defense)**: Sums grayscale pixel intensities vertically to extract 1D horizontal profile arrays. Tracks adjacent profile shifts to measure sub-pixel translation velocity `dx`. If the sliding window shows motion reversals for more than 10% of the duration (monotonicity ratio `mono_ratio < 90%`), a heavy `reversal_penalty` is applied to filter out pendulum motions and keep pans clean.

### 5. Narrative Continuity & Causality Solver
* **Design Philosophy**: Directs story progression, character pacing, and actions to align with cinematic storytelling rules.
* **Algorithmic Logic**:
  * **Character Locking and Fatigue Filtering**: When a character is chosen, a Lock Bonus is applied to prioritize keeping that character on screen for at least `min_contiguous_cuts` (e.g. 3 cuts) for visual coherence. Once this threshold is crossed, a Fatigue Penalty (`-0.8`) is applied to force a character cut.
  * **Action Causality Rules**: Dictates logical flows and prevents repetitive actions. For example, if a `spray` (hair spray) action occurs, the engine penalizes consecutive `spray` actions and prioritizes subsequent actions such as `combing` or `product_closeup` with a `prefer_bonus` (+1.2), ensuring natural continuity.
