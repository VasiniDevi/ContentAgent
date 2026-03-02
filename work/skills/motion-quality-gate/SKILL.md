---
name: motion-quality-gate
description: Validate motion infographic outputs against objective quality thresholds. Use when checking render readiness, text budget, contrast, pacing, and delivery metadata before publishing an MP4.
---

# Motion Quality Gate

Run deterministic checks before approving final output.

## Workflow

1. Prepare a manifest.
- Include slide text snippets.
- Include expected width, height, fps, and duration range.
- Include contrast pairs to validate text readability.

2. Run the gate script.
- Execute `python3 scripts/qc_motion_video.py --video <mp4> --manifest <json>`.
- Keep `--max-words 12` unless explicitly overridden.

3. Fix failing checks before sign-off.
- If text fails, trim wording.
- If contrast fails, increase foreground luminance or darken background.
- If timing fails, adjust scene duration or fps.

4. Save gate output.
- Keep the pass/fail report with the render artifact.

## Minimum Pass Criteria

1. All visible copy blocks are 12 words or fewer.
2. Metadata matches expected render format.
3. Video duration falls within planned range.
4. Contrast meets thresholds in manifest.

## References

1. Read `references/thresholds.md` for default values.
2. Use `scripts/qc_motion_video.py` as the source of truth for automated validation.
