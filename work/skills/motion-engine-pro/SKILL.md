---
name: motion-engine-pro
description: Implement pro-grade motion rendering patterns on top of motion_engine. Use when adding depth effects, reusable transition grammar, atmospheric layers, and performance optimization for production-quality infographic videos.
---

# Motion Engine Pro

Upgrade base motion scenes with reusable visual effects and faster primitives.

## Workflow

1. Build with cached primitives first.
- Use `CachedGlowRect` from `scripts/pro_effects.py` for repeated glow cards.
- Avoid recomputing expensive blur operations every frame.

2. Add atmosphere layers.
- Add vignette for focus.
- Add soft grain for texture.
- Add low-opacity floating orbs for subtle motion depth.

3. Encode transition grammar.
- Mix directional wipes, dissolves, and zoom punctuations.
- Keep transition style aligned with message progression.

4. Keep decorative effects subordinate.
- Primary copy must stay the visual focus.
- Treat effects as depth cues, not content.

## Performance Rules

1. Cache static effect sprites.
2. Keep per-frame callback work bounded and deterministic.
3. Limit decorative object count to avoid frame drops.
4. Reuse precomputed overlays when possible.

## References

1. Use `scripts/pro_effects.py` for implementation primitives.
2. Read `references/patterns.md` for composition and transition recipes.
