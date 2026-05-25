# 🎬 DaVinci Resolve 21 AI Automated Rhythmic & Semantic Editing System
## 📘 AI-Powered Rhythmic & Semantic Video Auto-Editor

This project is a high-performance **AI-powered rhythmic audio-matching, narrative reordering, and video auto-editing system** built on the Python API and computer vision techniques. It interfaces natively with **DaVinci Resolve 21 (Studio)** via its Python API. The system automatically aligns raw camera takes with background music (BGM) beats, speech segments, and semantic markers, resolving critical editing challenges such as cross-framerate rendering phase differences, signal processing latencies, timeline audio-video cropping offsets, hand-held wiggles, camera panning direction reversals, and subtitle synchronization.

---

## 🌟 Key Features & Algorithmic Architectures

### 1. SRT Semantic Timeline Editing & AIDA Reordering
* **Semantic Reordering**: Reads raw video takes alongside their corresponding `SRT` files. Re-arranges the clip order on the timeline based on a configured narrative structure (e.g. the marketing AIDA model: Hook ➡️ Intro ➡️ Core Curriculum ➡️ Endorsement ➡️ CTA) and segment time indices.
* **Adaptive Subtitle Sync (SRT Timecode Adaptation)**: When clips are rearranged or trimmed, the solver automatically extracts the original subtitle blocks and re-computes their start and end timecode timestamps relative to the new timeline speed and sequence order with millisecond precision, outputting a fully synchronized, updated `SRT` file.
* **Reframing Visual Zoom & Color Tagging**: Automatically applies alternating scale reframing (e.g. Zoom 1.0 and 1.18) and marks clips on the timeline with color tags (e.g. Teal) to provide clear visual boundaries in the edit page, facilitating manual quality checks.

### 2. Sizing Reframing & Symmetrical Tilts (Symmetrical Reframing & Tilts)
* **4-Phase Static Clip Reframing**:
  Due to physical limitations in the DaVinci Resolve Python API which **strictly blocks writing dynamic keyframes directly in the Edit page**, the system reframes composition states using static transformations rather than dynamic keyframes. Sizing and tilt constants are written directly to the clip properties on Video Track 1:
  1. **【Setup】(Establishing)**: `Zoom = 1.0` (or `3.16` for vertical scaling), `RotationAngle = 0.0`. Retains the original composition and horizontal frame lines for stable opening scenes.
  2. **【Detail】(Focus)**: `Zoom = 1.10` (or `3.476`), `RotationAngle = 0.0`. Magnifies the subject slightly to emphasize cosmetics details or label typography without losing focus.
  3. **【Catwalk Climax】(Action)**: `Zoom = 1.15` (or `3.634`), combined with **Alternating Symmetrical Tilts**: even-indexed clips are tilted to `RotationAngle = 4.0` while odd-indexed clips are tilted to `RotationAngle = -4.0`. The abrupt perspective jumps simulate camera motion tension snapped to beats.
  4. **【Finale】(Outro)**: `Zoom = 1.20` (or `3.792`), `RotationAngle = 0.0`. Further pulls the zoom scale closer to focus on brand logos and model freeze-frames.
* **Aspect Ratio Scaling Compensation**:
  When placing horizontal raw files (16:9) onto a vertical timeline (9:16), the engine automatically detects the aspect ratio discrepancy and applies a **`3.16`x proportional magnification multiplier** to the `Zoom` value, filling the vertical canvas cleanly without black bars.

### 3. Motion Flow Smoothing & Continuity
* **Motion Envelope**: Applies a **5-beat Moving Average Filter** to the raw motion energy values of candidate clips to smooth transitions into flowing, wave-like energy curves.
* **Visual Inertia Defense**: Computes the absolute motion variance difference between adjacent cuts. If the difference **`> 3.0`**, it applies a **`0.15` incremental penalty** to discourage jarring visual shifts, forcing the engine to prioritize smooth motion continuity.

### 4. High-Precision Transient Beat Detection
* Uses **FFmpeg** to transcode compressed music tracks into a standard Mono WAV in under 0.3 seconds.
* Implements a high-precision SciPy/NumPy onset detector analyzing Short-Time Energy (RMS) sliding window falling edges to track exact music tempos and beat points.
* **Climax Target Alignment**: Automatically scans for the highest-energy music climax segment and snaps its start frame perfectly to the timeline start offset (`86400`).

### 5. Smart Padding Margin & Triple Shaky Defense
* To purge shaky camera adjustments, autofocus wiggles, or camera button press shakes, the engine runs a triple-defense filtering pipeline:
  1. **Defense 1: 15% Smart Padding Margin**: Automatically masks out the first 15% and last 15% of each raw take (where hand-shakes from pressing button triggers usually occur), strictly limiting the rolling search window to the remaining **70% Pristine Mid-section**.
  2. **Defense 2: Rolling Motion Stability Scanner**: Downsamples frame dimensions by 99% to `160x90` in memory (filtering out high-frequency fine details, isolating macroscopic camera pans). Using a high-speed forward-only jump-frame decoder (running **5.2x faster** than traditional seek decodes), it computes camera motion vector variance. The crop In point is snapped to the lowest variance window.
  3. **Defense 3: Shaky Take Rejection**: If an entire raw clip is extremely chaotic and its lowest variance window remains above the safety threshold (`10.5`), the AI director applies a heavy **`-3.0 point penalty`**, completely discarding the file from the timeline candidate sequence.

### 6. Motion Vector Monotonicity & Direction Reversal Defense
* **1D Horizontal Projection Profile Cross-Correlation**: Sums grayscale pixel intensities vertically to extract 1D horizontal signature profiles. Tracks adjacent profile shifts to measure sub-pixel translation velocity `dx(t)` at high speed.
* **Monotonicity Ratio**:
  $$\text{Monotonicity Ratio} = \frac{\max(\sum [dx > 0], \sum [dx < 0])}{\text{Total Active Frames}}$$
  If the monotonicity score is **`< 90%`** (indicating the camera is panning back-and-forth like a pendulum), the engine applies a heavy **Reversal Blocking Penalty**, filtering out pendulum motions to keep pans clean, stable, and single-directional.

### 7. Narrative Continuity & Causality Solver
* **Dual-Axis Constraints**: Uses pre-compiled annotations (`clip_annotations.json`) to classify candidates, ensuring story progression, character pacing, and actions align with cinematic storytelling rules.
* **Character Lock Bonus & Fatigue Penalty**: When a character is chosen, a Lock Bonus is applied to prioritize keeping that character on screen for at least `min_contiguous_cuts` (e.g. 3 cuts) for visual coherence. Once this threshold is crossed, a Fatigue Penalty (`-0.8`) is applied to force a character cut.
* **Action Causality Rules**: Dictates logical flows and prevents repetitive actions. For example, if a `spray` action occurs, the engine penalizes consecutive `spray` actions and prioritizes subsequent actions such as `combing` or `product_closeup` with a `prefer_bonus` (+1.2).

### 8. 25-Second Commercial Standard & Storytelling Wide Cap
* **Wide Shot Cap**: Sells wide and environment-establishing shots strictly to **exactly 2 clips** (the Setup opening cut and the Finale outro cut). Intermediate cuts are strictly restricted to CloseUp and Medium takes.
* **Zero-Repetition Math**: 25.0 seconds compiles exactly **35 beat cuts**. With an asset pool of 36 unique close-up/medium takes, this fits perfectly into the **Zero-Repetition Sweet Spot**, ensuring a completely unique clip on every single beat.

### 9. Global Motion Profile Cache (`.cv_profile_cache.json`)
* Decouples the caching layer from timeline properties. It profiles raw clips once, indexing full-length frame-by-frame motion vectors under their absolute paths.
* Any subsequent re-run, timing adjustment, or duration change loads profiles from the JSON cache, completing the entire timeline rebuild in **0.01 seconds**.

### 10. Side-by-Side Brand Outro Overlay (BC & Schwarzkopf)
* Automatically adds **Video Track 2 & 3** and overlays **BC LOGO** & **Schwarzkopf LOGO** side-by-side during the Finale section (starts at **20.8s / 86895f**).
* **Precise Geometry**:
  * Shared scaling: `Zoom = 0.35`
  * **BC Logo (V2)**: `Pan = -260.0`, `Tilt = -50.0`
  * **Schwarzkopf Logo (V3)**: `Pan = 260.0`, `Tilt = -50.0`

### 11. Coordinate Correction & Gapless math.ceil Sync
* Employs a ceiling math formula to prevent 1-frame black gap rendering glitches when placing **29.97 FPS** source files on a **24.0 FPS** timeline:
  $$\text{duration\_source} = \text{int}(\text{math.ceil}(\text{duration\_timeline} \times \frac{\text{src\_fps}}{\text{timeline\_fps}}))$$
* **Coordinate Correction**: Automatically subtracts timeline offset (`86400`) from marker coordinates to align Resolve's relative `AddMarker` input with absolute timeline coordinates.

---

## 📂 Project Structure & Directory Guide

```text
├── config/                      # Project configuration JSON profiles
│   ├── bc_bonacure_30s.json
│   └── bc_exhibition_25s.json
├── core/                        # Core system algorithms & API wrappers
│   ├── aesthetic_gate.py        # CLIP semantic calculations and aesthetic filter
│   ├── beat_detector.py         # SciPy beat transient detection
│   ├── continuity_solver.py     # Narrative continuity & action causality solver
│   ├── cv_analyzer.py           # OpenCV optical flow stability & 1D projections
│   ├── director_rules.py        # Sizing reframing parameters & grading classes
│   └── resolve_api.py           # DaVinci Resolve Python API wrapper
├── diagnostics/                 # System diagnostics modules
│   ├── diagnose_ai2.py
│   ├── resolve_api_test.py
│   └── track_diagnoser.py       # Timeline track and GUI focus diagnostics
├── doc/                         # System technical documentation & manuals
│   ├── APIMAP.md                # Chinese API method references & gotchas manual
│   ├── APIMAP_EN.md             # English API method references & gotchas manual
│   ├── Videoquality.md          # Chinese editing styles & algorithmic logics manual
│   ├── Videoquality_EN.md       # English editing styles & algorithmic logics manual
│   ├── Agentskill.md            # Chinese AI Agent skills & identity manual
│   └── Agentskill_EN.md         # English AI Agent skills & identity manual
├── legacy/                      # Main compilers & standalone tools (Run here)
│   ├── run_event_highlight_edit.py # Main event highlight compiler engine
│   ├── pre_cache_profiles.py    # Background motion features cache pre-warmer
│   ├── reimport_assets.py       # Duplicate-free Google Drive media importer
│   ├── create_semantic_timeline.py # Sam promotional reordering timeline & SRT generator
│   ├── stability_analyzer_hyper_fast.py # Single clip optical flow scanner
│   ├── direction_stability_analyzer.py # Single clip translation direction scanner
│   └── diag_timelines.py        # Diagnostic timeline focus checker
├── scratch/                     # Temporary verification scripts
├── director.py                  # 🎬 Main system controller (CLI main entry)
└── test_copy_grades.py          # Node grade cloning test script
```

---

## ⚙️ System Requirements & Installation

### 1. DaVinci Resolve Studio Requirements
* Requires **DaVinci Resolve 21 Studio** (external Python API execution is only supported in paid versions).
* **Enable External Scripting**: Navigate to Resolve Preferences ➡️ System ➡️ General ➡️ set "External scripting using" to **"Local"** or **"Local and Network"**.
* Operating System: Windows 11 / 10.

### 2. Environment Variables Configuration (PowerShell)
To allow Python to locate Resolve's scripting Modules, set these environment variables (adjust paths according to installation location):

```powershell
$env:RESOLVE_SCRIPT_API="%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
$env:RESOLVE_SCRIPT_LIB="C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
$env:PYTHONPATH="%RESOLVE_SCRIPT_API%\Modules;$env:PYTHONPATH"
```

### 3. Install Python Dependencies
Python 3.10+ is recommended. In your terminal, run:

```bash
pip install numpy scipy opencv-python torch torchvision torchaudio transformers
```

> [!NOTE]
> The project uses CLIP models for semantic rankings. If an NVIDIA GPU with CUDA is detected, operations will automatically accelerate via GPU.

### 4. FFmpeg Requirements
* Audio beat transient detection relies on `FFmpeg`. Ensure `ffmpeg` is installed and added to your system's `PATH`.

---

## 🚀 Quick Start Guide

The system features a unified CLI main entry `director.py`. Execute core workflows by specifying the `--action` flag.

### Step 1: Pre-cache Motion Features (`precache`)
Scans directories in the background, extracts motion signatures, and indexes features under absolute paths. **(Runs independently of DaVinci Resolve at high speed)**

```bash
python director.py --config config/bc_exhibition_25s.json --action precache
```

### Step 2: Validate Timeline GUI Focus (`diagnose`)
Verifies connections to Resolve and prints which timeline currently holds focus in the editor panel.

```bash
python director.py --config config/bc_exhibition_25s.json --action diagnose
```

> [!IMPORTANT]
> **GUI Focus Safety Lock**: If the open tab in Resolve does not match the target timeline, **double-click the timeline in the media pool to focus it in your GUI editor**. This prevents Resolve from appending clips onto the wrong active tab!

### Step 3: Run the Main Auto-Edit Engine (`run`)
Performs beat detection, climax alignment, narrative continuity calculations, smart padding, stability and panning monotonicity filtering, logo placements, and node grade cloning sequentially:

```bash
python director.py --config config/bc_exhibition_25s.json --action run
```

### Step 4: Run SRT Semantic Reordering & Subtitle Alignment
To rebuild the promotional showcase clip and generate a synchronized subtitle `SRT` file, run:

```bash
python legacy/create_semantic_timeline.py
```
This script writes updated subtitle timecode alignment files onto `C:\TEST\Sam.srt` and `C:\TEST\Sam_corrected.srt`. Simply navigate to `File > Import > Subtitle` in DaVinci Resolve, select the file, and drag it onto the timeline.

### Step 5: AI Reroll Target Replacement (`reroll`)
If you watch the edit and decide to replace specific clips:
1. In Resolve's Edit page, **right-click the clip ➡️ select Clip Color ➡️ set it to Red, Pink, or Rose**.
2. Run the `reroll` action in your terminal:

```bash
python director.py --config config/bc_exhibition_25s.json --action reroll
```

The AI will **target only the marked clips**, exclude already used videos, evaluate candidate pools based on duration, stability, and continuity, swap the clips in under **0.2 seconds**, retain sizing transforms, and copy Master node grades automatically.

---

## 🛡️ License & Contributors
* This system is designed by a professional video R&D team to address visual aesthetics generation in automated cinematic clips and commercials editing.
* Submissions of custom reframing parameter sets or PRs are welcome! 🎬🍿
