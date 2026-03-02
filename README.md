# ContentAgent

Autonomous video creation agent — analyzes reference videos and recreates them as motion infographics using a skills-driven Python pipeline.

## Architecture

The pipeline renders 1080×1920 vertical video at 30fps using a pure Python stack (PIL/Pillow + numpy + OpenCV). Design decisions are encoded as importable skill modules rather than hardcoded in render scripts.

```
reference-lock → styleframe-gate → animation → QC
```

### Skills (at `~/.claude/skills/`)

| Skill | Type | Purpose |
|---|---|---|
| `motion_engine` | core | Scene-based timeline, elements, easings, MP4 renderer |
| `motion_templates` | core | Slide decks, kinetic typography, transitions |
| `lottie_engine` | core | Keyframe animation, JSON timelines, HTML export |
| `motion_tokens` | design system | Timing, easing, spacing, type scale, color palette |
| `pro_effects` | effects | CachedGlowRect, vignette, grain, floating orbs |
| `typography_direction` | typography | Font system, SafeText, WCAG contrast checking |
| `transition_choreographer` | transitions | Narrative-mapped presets, streak flourishes |
| `styleframe_lab` | QA | Still frame capture, comparison grids, scoring |
| `motion_quality_gate` | QA | Video metadata, text budget, contrast, timing, pacing |
| `reference_lock` | protocol | Collect and freeze visual references before design |
| `styleframe_gate` | protocol | Validate still frames before committing to animation |

### Render Scripts

- `work/mastering_claude_code_v3_1.py` — v3.1 (814 lines, hardcoded design tokens)
- `work/mastering_claude_code_v4.py` — v4 (550 lines, imports from skills)

Both produce identical output. v4 replaces all magic numbers with token references.

## Quick Start

```bash
# Install dependencies
pip install pillow numpy opencv-python

# Render v4 video
python work/mastering_claude_code_v4.py

# Styleframes only (no video render)
python work/mastering_claude_code_v4.py --styleframes-only

# Skip quality gate
python work/mastering_claude_code_v4.py --skip-qc

# Custom output path
python work/mastering_claude_code_v4.py --output path/to/output.mp4
```

## Output

The render produces three files:

- `.mp4` — the video (1080×1920, 30fps, ~7 MB for 34.5s)
- `.manifest.json` — slide metadata and contrast pairs
- `.qc.json` — quality gate results

## Quality Gate

The QC pipeline checks:

- Video file existence and metadata (resolution, fps, duration)
- Text budget (≤12 words per block)
- WCAG contrast ratios (4.5:1 body, 3:1 labels)
- Safe margins (edge vs center brightness)
- Timing consistency (animation durations above minimum threshold)
- Pacing rhythm (slide duration variance)

## Project Structure

```
work/
├── mastering_claude_code_v4.py    # v4 render script
├── mastering_claude_code_v3_1.py  # v3.1 render script
└── skills/                        # proto-skills (reference)
    ├── motion-art-direction/
    ├── motion-engine-pro/
    └── motion-quality-gate/
```

## License

Private project.
