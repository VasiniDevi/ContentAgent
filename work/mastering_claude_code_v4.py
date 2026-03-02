"""Mastering Claude Code v4 — skills-driven motion infographic (1080x1920, 30fps).

All design system knowledge comes from importable skills:
  motion_tokens, pro_effects, typography_direction,
  transition_choreographer, styleframe_lab, motion_quality_gate
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Skill imports
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.path.expanduser("~/.claude/skills"))

from motion_engine.elements import Circle, GradientRect, Rect
from motion_engine.scene import Scene
from motion_tokens import EASING, PALETTE, SPACING, TIMING, TYPE_SCALE
from pro_effects import CachedGlowRect, add_floating_orbs, add_soft_grain, add_vignette
from transition_choreographer import apply_narrative_transition
from typography_direction import FONTS, SafeText

# Use SafeText everywhere (prevents glyph clipping)
Text = SafeText

# Resolve token shortcuts
TOKENS = PALETTE.as_dict()
W = 1080
H = 1920
FPS = 30

DISPLAY_FONT = FONTS.get("display")
BODY_FONT = FONTS.get("body")
LABEL_FONT = FONTS.get("label")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render mastering_claude_code v4 motion infographic.")
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "work/mastering_claude_code_v4.mp4"),
        help="Output mp4 path",
    )
    parser.add_argument("--skip-qc", action="store_true", help="Skip quality gate")
    parser.add_argument("--styleframes-only", action="store_true", help="Capture styleframes and exit")
    parser.add_argument("--quiet", action="store_true", help="Disable render progress output")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Reusable composition helpers
# ---------------------------------------------------------------------------


def add_background_planes(scene: Scene, start: float, dur: float, accent: str, opposite: str) -> None:
    plane1 = Rect(int(W * 1.6), 260, color=accent, pos=(W * 0.30, H * 0.52), rotation=-21)
    plane1.opacity = 0.04
    scene.add(
        plane1, enter=start, dur=dur, exit=start + dur,
        enter_anim="fade_in", exit_anim="fade_out",
        enter_dur=TIMING.transition_base, exit_dur=TIMING.exit_base, z_index=-20,
    )
    plane2 = Rect(int(W * 1.5), 220, color=opposite, pos=(W * 0.78, H * 0.70), rotation=17)
    plane2.opacity = 0.035
    scene.add(
        plane2, enter=start + 0.2, dur=dur - 0.2, exit=start + dur,
        enter_anim="fade_in", exit_anim="fade_out",
        enter_dur=TIMING.transition_base, exit_dur=TIMING.exit_base, z_index=-19,
    )


def add_tracker(scene: Scene, start: float, dur: float, label: str, progress: float, color: str) -> None:
    x, y = W // 2, 132
    rail_w = 470
    rail = Rect(rail_w, 7, color="#1f2847", border_radius=4, pos=(x, y))
    rail.opacity = 0.95
    scene.add(
        rail, enter=start + 0.05, dur=dur - 0.20, exit=start + dur - 0.10,
        enter_anim="fade_in", exit_anim="fade_out",
        enter_dur=0.22, exit_dur=0.18, z_index=40,
    )
    fill = GradientRect(
        max(12, int(rail_w * progress)), 7,
        start_color=color, end_color=PALETTE.cyan, angle=0, border_radius=4,
        pos=(x - rail_w / 2, y), anchor=(0, 0.5),
    )
    scene.add(
        fill, enter=start + 0.12, dur=dur - 0.28, exit=start + dur - 0.10,
        enter_anim="scale_in", exit_anim="fade_out",
        enter_dur=TIMING.enter_fast, exit_dur=0.18, enter_easing=EASING.enter, z_index=41,
    )
    rule = Text(label, font=LABEL_FONT, font_size=TYPE_SCALE.label + 1, color=PALETTE.text_muted, pos=(x, y - 30))
    scene.add(
        rule, enter=start + 0.08, dur=dur - 0.25, exit=start + dur - 0.12,
        enter_anim="fade_up", exit_anim="fade_out",
        enter_dur=0.25, exit_dur=0.18, z_index=42,
    )


def add_accent_line(scene: Scene, start: float, dur: float, x: float, y: float, width: int, c1: str, c2: str) -> None:
    line = GradientRect(width, 4, start_color=c1, end_color=c2, angle=0, border_radius=2, pos=(x, y))
    scene.add(
        line, enter=start, dur=dur, exit=start + dur,
        enter_anim="scale_in", exit_anim="fade_out",
        enter_dur=TIMING.enter_fast, exit_dur=TIMING.min_animation, enter_easing=EASING.enter,
    )


def add_pill(scene: Scene, start: float, dur: float, x: float, y: float, text: str, color: str, width: int) -> None:
    bg = Rect(width, 44, color=color, border_radius=22, pos=(x, y))
    bg.opacity = 0.19
    scene.add(
        bg, enter=start, dur=dur, exit=start + dur,
        enter_anim="scale_in", exit_anim="fade_out",
        enter_dur=0.24, exit_dur=TIMING.min_animation, enter_easing=EASING.emphasis,
    )
    tx = Text(text, font=LABEL_FONT, font_size=19, color=color, pos=(x, y))
    scene.add(
        tx, enter=start + 0.08, dur=dur - 0.12, exit=start + dur,
        enter_anim="fade_in", exit_anim="fade_out",
        enter_dur=TIMING.min_animation, exit_dur=TIMING.min_animation,
    )


# ---------------------------------------------------------------------------
# Scene construction
# ---------------------------------------------------------------------------


def build_scene() -> tuple[Scene, list[dict[str, object]], list[tuple[str, float, float]]]:
    scene = Scene(W, H, fps=FPS, bg=PALETTE.bg)
    slides_manifest: list[dict[str, object]] = []
    slide_times: list[tuple[str, float, float]] = []

    add_vignette(scene, strength=0.23, color="#000000")
    add_soft_grain(scene, opacity=0.04, seed=21)

    t = 0.0

    # -- Slide 1: Title -------------------------------------------------------
    s1_dur = 6.0
    slide_times.append(("title", t, s1_dur))
    add_background_planes(scene, t, s1_dur, PALETTE.purple, PALETTE.cyan)
    add_tracker(scene, t, s1_dur, label="Rule 1/5", progress=0.20, color=PALETTE.purple)
    add_floating_orbs(scene, start=t, dur=s1_dur, palette=[PALETTE.purple, PALETTE.cyan], count=7, seed=10, max_opacity=0.08)

    hero = CachedGlowRect(
        760, 390, color=PALETTE.card_bg, border_radius=30,
        border_color=PALETTE.card_border, border_width=1,
        glow_color=PALETTE.purple, glow_radius=42, glow_opacity=0.40,
        pos=(W - 75, 705), anchor=(1, 0.5), rotation=-1.6,
    )
    scene.add(hero, enter=t + 0.22, dur=s1_dur - 0.54, exit=t + s1_dur - 0.22, enter_anim="fade_left", exit_anim="fade_out", enter_dur=TIMING.enter_base, exit_dur=TIMING.exit_base)

    title_a = Text("Mastering", font=DISPLAY_FONT, font_size=TYPE_SCALE.display_xl + 4, color=PALETTE.text, pos=(W - 700, 620), anchor=(0, 0.5), max_width=560)
    scene.add(title_a, enter=t + 0.45, dur=s1_dur - 1.0, exit=t + s1_dur - 0.28, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.42, exit_dur=0.26)

    title_b = Text("Claude Code", font=DISPLAY_FONT, font_size=TYPE_SCALE.display_xl + 8, color=PALETTE.text, pos=(W - 660, 730), anchor=(0, 0.5), max_width=580)
    scene.add(title_b, enter=t + 0.60, dur=s1_dur - 1.2, exit=t + s1_dur - 0.28, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.42, exit_dur=0.26)

    add_accent_line(scene, t + 0.88, s1_dur - 1.5, W - 610, 808, 205, PALETTE.purple, PALETTE.cyan)

    subtitle = Text("Pro workflow guide", font=BODY_FONT, font_size=36, color=PALETTE.text_secondary, pos=(W - 640, 875), anchor=(0, 0.5))
    scene.add(subtitle, enter=t + 1.04, dur=s1_dur - 1.62, exit=t + s1_dur - 0.28, enter_anim="fade_up", exit_anim="fade_out", enter_dur=TIMING.enter_fast + 0.04, exit_dur=0.24)

    side_rule = Rect(6, 230, color=PALETTE.cyan, border_radius=3, pos=(130, 740))
    side_rule.opacity = 0.25
    scene.add(side_rule, enter=t + 0.55, dur=s1_dur - 1.0, exit=t + s1_dur - 0.28, enter_anim="scale_in", exit_anim="fade_out", enter_dur=TIMING.enter_base, exit_dur=0.24)

    ring_a = Circle(radius=190, color=PALETTE.purple, pos=(210, 910))
    ring_a.opacity = 0.05
    scene.add(ring_a, enter=t + 0.35, dur=s1_dur - 0.9, exit=t + s1_dur - 0.2, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.8, exit_dur=TIMING.enter_fast)

    slides_manifest.append({"id": "title", "texts": ["Mastering Claude Code", "Pro workflow guide"]})

    t += s1_dur
    apply_narrative_transition(scene, t, "intro", accent=PALETTE.purple, accent_end=PALETTE.cyan)

    # -- Slide 2: Rule 1 - Interrogate first -----------------------------------
    s2_dur = 7.0
    slide_times.append(("rule_1", t, s2_dur))
    add_background_planes(scene, t, s2_dur, PALETTE.purple, TOKENS["bg_soft"])
    add_tracker(scene, t, s2_dur, label="Rule 1/3", progress=0.33, color=PALETTE.purple)
    add_floating_orbs(scene, start=t, dur=s2_dur, palette=[PALETTE.purple, PALETTE.cyan], count=6, seed=33, max_opacity=0.07)

    wm2 = Text("01", font=DISPLAY_FONT, font_size=250, color=PALETTE.purple, pos=(930, 300))
    wm2.opacity = 0.06
    scene.add(wm2, enter=t + 0.16, dur=s2_dur - 0.7, exit=t + s2_dur - 0.2, enter_anim="fade_in", exit_anim="fade_out", enter_dur=TIMING.transition_short, exit_dur=TIMING.enter_fast)

    card2 = CachedGlowRect(
        670, 470, color=PALETTE.card_bg, border_radius=26,
        border_color=PALETTE.card_border, border_width=1,
        glow_color=PALETTE.purple, glow_radius=36, glow_opacity=0.35,
        pos=(75, 700), anchor=(0, 0.5), rotation=-1.2,
    )
    scene.add(card2, enter=t + 0.30, dur=s2_dur - 0.82, exit=t + s2_dur - 0.24, enter_anim="slide_right", exit_anim="fade_out", enter_dur=0.5, exit_dur=0.33)

    h2 = Text("Interrogate first", font=DISPLAY_FONT, font_size=TYPE_SCALE.headline + 22, color=PALETTE.text, pos=(130, 575), anchor=(0, 0.5), max_width=560)
    scene.add(h2, enter=t + 0.48, dur=s2_dur - 1.0, exit=t + s2_dur - 0.28, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.38, exit_dur=0.24)

    add_accent_line(scene, t + 0.74, s2_dur - 1.36, 250, 640, 165, PALETTE.purple, PALETTE.cyan)

    s2_sub = Text("Ask before code.", font=BODY_FONT, font_size=38, color=PALETTE.text_secondary, pos=(130, 712), anchor=(0, 0.5), max_width=520)
    scene.add(s2_sub, enter=t + 0.86, dur=s2_dur - 1.58, exit=t + s2_dur - 0.30, enter_anim="fade_up", exit_anim="fade_out", enter_dur=TIMING.enter_fast, exit_dur=0.24)

    add_pill(scene, t + 1.42, s2_dur - 2.64, 245, 820, "Goal?", PALETTE.purple, 172)
    add_pill(scene, t + 1.66, s2_dur - 2.88, 468, 820, "Constraints?", PALETTE.purple, 218)
    add_pill(scene, t + 1.92, s2_dur - 3.14, 315, 884, "Edge cases?", PALETTE.purple, 195)
    add_pill(scene, t + 3.24, s2_dur - 4.4, 338, 980, "Clarity prevents rework", PALETTE.purple, 370)

    slides_manifest.append({"id": "rule_1", "texts": ["Interrogate first", "Ask before code.", "Goal?", "Constraints?", "Edge cases?", "Clarity prevents rework"]})

    t += s2_dur
    apply_narrative_transition(scene, t, "topic_shift", accent=PALETTE.green, accent_end=PALETTE.cyan)

    # -- Slide 3: Rule 2 - One feature at a time ------------------------------
    s3_dur = 7.0
    slide_times.append(("rule_2", t, s3_dur))
    add_background_planes(scene, t, s3_dur, PALETTE.green, PALETTE.cyan)
    add_tracker(scene, t, s3_dur, label="Rule 2/3", progress=0.66, color=PALETTE.green)
    add_floating_orbs(scene, start=t, dur=s3_dur, palette=[PALETTE.green, PALETTE.cyan, PALETTE.purple], count=7, seed=49, max_opacity=0.08)

    wm3 = Text("02", font=DISPLAY_FONT, font_size=250, color=PALETTE.green, pos=(150, 300))
    wm3.opacity = 0.055
    scene.add(wm3, enter=t + 0.16, dur=s3_dur - 0.7, exit=t + s3_dur - 0.2, enter_anim="fade_in", exit_anim="fade_out", enter_dur=TIMING.transition_short, exit_dur=TIMING.enter_fast)

    card3 = CachedGlowRect(
        700, 450, color=PALETTE.card_bg, border_radius=26,
        border_color=PALETTE.card_border, border_width=1,
        glow_color=PALETTE.green, glow_radius=36, glow_opacity=0.33,
        pos=(W - 70, 900), anchor=(1, 0.5), rotation=1.4,
    )
    scene.add(card3, enter=t + 0.32, dur=s3_dur - 0.84, exit=t + s3_dur - 0.24, enter_anim="slide_left", exit_anim="fade_out", enter_dur=0.5, exit_dur=0.33)

    h3 = Text("One feature at a time", font=DISPLAY_FONT, font_size=TYPE_SCALE.headline + 16, color=PALETTE.text, pos=(W - 115, 760), anchor=(1, 0.5), max_width=630)
    scene.add(h3, enter=t + 0.50, dur=s3_dur - 1.03, exit=t + s3_dur - 0.28, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.36, exit_dur=0.24)

    add_accent_line(scene, t + 0.78, s3_dur - 1.42, W - 325, 828, 200, PALETTE.green, PALETTE.cyan)

    s3_sub = Text("Build A. Test A. Then B.", font=BODY_FONT, font_size=35, color=PALETTE.text_secondary, pos=(W - 115, 898), anchor=(1, 0.5), max_width=620)
    scene.add(s3_sub, enter=t + 0.90, dur=s3_dur - 1.62, exit=t + s3_dur - 0.30, enter_anim="fade_up", exit_anim="fade_out", enter_dur=TIMING.enter_fast, exit_dur=0.24)

    chain = [("A", PALETTE.green, W - 600), ("B", PALETTE.cyan, W - 450), ("C", PALETTE.purple, W - 300)]
    for idx, (lbl, col, x) in enumerate(chain):
        c = Circle(radius=32, color=col, pos=(x, 1000))
        c.opacity = 0.22
        scene.add(c, enter=t + 1.38 + idx * 0.2, dur=s3_dur - 2.58, exit=t + s3_dur - 0.30, enter_anim="scale_in", exit_anim="fade_out", enter_dur=TIMING.enter_fast, exit_dur=TIMING.min_animation, enter_easing=EASING.emphasis)
        lt = Text(lbl, font=LABEL_FONT, font_size=24, color=col, pos=(x, 1000))
        scene.add(lt, enter=t + 1.48 + idx * 0.2, dur=s3_dur - 2.72, exit=t + s3_dur - 0.30, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.18, exit_dur=0.18)
        if idx < 2:
            ar = Text(">", font=LABEL_FONT, font_size=36, color=PALETTE.text_muted, pos=(x + 75, 1000))
            scene.add(ar, enter=t + 1.55 + idx * 0.2, dur=s3_dur - 2.78, exit=t + s3_dur - 0.30, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.18, exit_dur=0.18)

    add_pill(scene, t + 3.18, s3_dur - 4.36, W - 355, 1092, "Ship in stable slices", PALETTE.green, 345)

    slides_manifest.append({"id": "rule_2", "texts": ["One feature at a time", "Build A. Test A. Then B.", "Ship in stable slices"]})

    t += s3_dur
    apply_narrative_transition(scene, t, "highlight", accent=PALETTE.orange, accent_end=PALETTE.cyan)

    # -- Slide 4: Rule 3 - Refresh at 50% ------------------------------------
    s4_dur = 7.0
    slide_times.append(("rule_3", t, s4_dur))
    add_background_planes(scene, t, s4_dur, PALETTE.orange, "#ff6b6b")
    add_tracker(scene, t, s4_dur, label="Rule 3/3", progress=1.0, color=PALETTE.orange)
    add_floating_orbs(scene, start=t, dur=s4_dur, palette=[PALETTE.orange, "#ff6b6b"], count=6, seed=57, max_opacity=0.08)

    wm4 = Text("03", font=DISPLAY_FONT, font_size=250, color=PALETTE.orange, pos=(915, 290))
    wm4.opacity = 0.055
    scene.add(wm4, enter=t + 0.2, dur=s4_dur - 0.72, exit=t + s4_dur - 0.2, enter_anim="fade_in", exit_anim="fade_out", enter_dur=TIMING.transition_short, exit_dur=TIMING.enter_fast)

    card4 = CachedGlowRect(
        720, 500, color=PALETTE.card_bg, border_radius=26,
        border_color=PALETTE.card_border, border_width=1,
        glow_color=PALETTE.orange, glow_radius=38, glow_opacity=0.34,
        pos=(70, 1030), anchor=(0, 0.5), rotation=-0.8,
    )
    scene.add(card4, enter=t + 0.34, dur=s4_dur - 0.86, exit=t + s4_dur - 0.24, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.5, exit_dur=0.33)

    h4 = Text("Refresh at 50%", font=DISPLAY_FONT, font_size=TYPE_SCALE.headline + 24, color=PALETTE.text, pos=(120, 860), anchor=(0, 0.5), max_width=560)
    scene.add(h4, enter=t + 0.50, dur=s4_dur - 1.0, exit=t + s4_dur - 0.28, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.36, exit_dur=0.24)

    add_accent_line(scene, t + 0.78, s4_dur - 1.42, 285, 932, 190, PALETTE.orange, "#ff6b6b")

    s4_sub = Text("Fresh context. accurate code.", font=BODY_FONT, font_size=36, color=PALETTE.text_secondary, pos=(120, 1015), anchor=(0, 0.5), max_width=620)
    scene.add(s4_sub, enter=t + 0.94, dur=s4_dur - 1.66, exit=t + s4_dur - 0.30, enter_anim="fade_up", exit_anim="fade_out", enter_dur=TIMING.enter_fast, exit_dur=0.24)

    rail = Rect(460, 22, color="#1f2847", border_radius=11, pos=(150, 1118), anchor=(0, 0.5))
    scene.add(rail, enter=t + 1.22, dur=s4_dur - 2.16, exit=t + s4_dur - 0.35, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.24, exit_dur=TIMING.min_animation)

    fill4 = GradientRect(230, 22, start_color=PALETTE.orange, end_color="#ff6b6b", angle=0, border_radius=11, pos=(150, 1118), anchor=(0, 0.5))
    scene.add(fill4, enter=t + 1.40, dur=s4_dur - 2.34, exit=t + s4_dur - 0.35, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.4, exit_dur=TIMING.min_animation)

    pct = Text("50%", font=LABEL_FONT, font_size=24, color=PALETTE.orange, pos=(655, 1118))
    scene.add(pct, enter=t + 1.55, dur=s4_dur - 2.48, exit=t + s4_dur - 0.35, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.18, exit_dur=0.18)

    icon = Rect(34, 34, color=PALETTE.orange, border_radius=6, pos=(690, 1045), rotation=45)
    icon.opacity = 0.2
    scene.add(icon, enter=t + 1.28, dur=s4_dur - 2.25, exit=t + s4_dur - 0.35, enter_anim="scale_in", exit_anim="fade_out", enter_dur=TIMING.enter_fast, exit_dur=TIMING.min_animation)

    add_pill(scene, t + 3.20, s4_dur - 4.40, 360, 1230, "New session. better precision", PALETTE.orange, 400)

    slides_manifest.append({"id": "rule_3", "texts": ["Refresh at 50%", "Fresh context. accurate code.", "New session. better precision"]})

    t += s4_dur
    apply_narrative_transition(scene, t, "recap", accent=PALETTE.cyan, accent_end=PALETTE.purple)

    # -- Slide 5: Summary -----------------------------------------------------
    s5_dur = 7.0
    slide_times.append(("summary", t, s5_dur))
    add_background_planes(scene, t, s5_dur, PALETTE.purple, PALETTE.cyan)
    add_tracker(scene, t, s5_dur, label="Rule 3/3", progress=1.0, color=PALETTE.cyan)
    add_floating_orbs(scene, start=t, dur=s5_dur, palette=[PALETTE.purple, PALETTE.green, PALETTE.orange], count=8, seed=73, max_opacity=0.08)

    blob = Circle(radius=455, color=PALETTE.purple, pos=(330, 1080))
    blob.opacity = 0.055
    scene.add(blob, enter=t + 0.16, dur=s5_dur - 0.55, exit=t + s5_dur - 0.2, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.75, exit_dur=TIMING.enter_fast)

    h5 = Text("The 3 rules", font=DISPLAY_FONT, font_size=TYPE_SCALE.display_lg + 16, color=PALETTE.text, pos=(W - 110, 400), anchor=(1, 0.5), max_width=520)
    scene.add(h5, enter=t + 0.30, dur=s5_dur - 0.88, exit=t + s5_dur - 0.26, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.38, exit_dur=0.24)

    add_accent_line(scene, t + 0.58, s5_dur - 1.22, W - 270, 475, 150, PALETTE.cyan, PALETTE.purple)

    rows = [
        ("1", "Interrogate first", PALETTE.purple, 120),
        ("2", "One at a time", PALETTE.green, 170),
        ("3", "Refresh at 50%", PALETTE.orange, 230),
    ]

    for idx, (num, label, accent, x) in enumerate(rows):
        y = 700 + idx * 175
        enter_t = t + 0.90 + idx * 0.26

        row = CachedGlowRect(
            730, 112, color=PALETTE.card_bg, border_radius=21,
            border_color=PALETTE.card_border, border_width=1,
            glow_color=accent, glow_radius=30, glow_opacity=0.31,
            pos=(x, y), anchor=(0, 0.5), rotation=(-0.8 + idx * 0.6),
        )
        scene.add(row, enter=enter_t, dur=s5_dur - 1.75 - idx * 0.20, exit=t + s5_dur - 0.24, enter_anim="fade_right", exit_anim="fade_out", enter_dur=TIMING.enter_fast + 0.04, exit_dur=0.22)

        badge = Circle(radius=22, color=accent, pos=(x + 55, y))
        scene.add(badge, enter=enter_t + 0.08, dur=s5_dur - 1.90 - idx * 0.20, exit=t + s5_dur - 0.24, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.24, exit_dur=TIMING.min_animation)

        nt = Text(num, font=LABEL_FONT, font_size=TYPE_SCALE.label, color="#09101c", pos=(x + 55, y))
        scene.add(nt, enter=enter_t + 0.14, dur=s5_dur - 2.00 - idx * 0.20, exit=t + s5_dur - 0.24, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.16, exit_dur=0.16)

        lt = Text(label, font=BODY_FONT, font_size=39, color=PALETTE.text, pos=(x + 125, y), anchor=(0, 0.5))
        scene.add(lt, enter=enter_t + 0.15, dur=s5_dur - 2.05 - idx * 0.20, exit=t + s5_dur - 0.24, enter_anim="fade_left", exit_anim="fade_out", enter_dur=0.24, exit_dur=TIMING.min_animation)

    slides_manifest.append({"id": "summary", "texts": ["The 3 rules", "Interrogate first", "One at a time", "Refresh at 50%"]})

    scene.duration = t + s5_dur + 0.5
    return scene, slides_manifest, slide_times


# ---------------------------------------------------------------------------
# Manifest & QC
# ---------------------------------------------------------------------------


def build_manifest(slides: list[dict[str, object]]) -> dict[str, object]:
    return {
        "expected": {
            "width": W,
            "height": H,
            "fps": FPS,
            "duration_min": 33.0,
            "duration_max": 37.0,
        },
        "slides": slides,
        "contrast_pairs": [
            {"label": "headline_on_card", "fg": PALETTE.text, "bg": PALETTE.card_bg, "min_ratio": 4.5},
            {"label": "body_on_card", "fg": PALETTE.text_secondary, "bg": PALETTE.card_bg, "min_ratio": 4.5},
            {"label": "label_on_card", "fg": PALETTE.text_muted, "bg": PALETTE.card_bg, "min_ratio": 3.0},
        ],
    }


def run_styleframes(scene, slide_times: list[tuple[str, float, float]], output_dir: Path) -> None:
    from styleframe_lab import capture_styleframes, save_comparison_grid, score_sequence

    print("\nCapturing styleframes...")
    frames = capture_styleframes(scene, slide_times, output_dir=output_dir)
    grid_path = save_comparison_grid(frames, output_dir / "grid.png")
    print(f"Styleframe grid: {grid_path}")

    results = score_sequence(frames)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.slide_id}: score={r.total_score:.0%}")
        for check_name, check_data in r.checks.items():
            mark = "ok" if check_data["passed"] else "FAIL"
            print(f"    [{mark}] {check_name}")


def run_quality_gate(
    video_path: Path,
    manifest: dict[str, object],
    scene=None,
    slide_times: list[tuple[str, float, float]] | None = None,
) -> int:
    from motion_quality_gate import QualityGate

    qc_path = video_path.with_suffix(".qc.json")
    gate = QualityGate(video_path, manifest, scene=scene, slide_times=slide_times)
    passed = gate.run_and_save(qc_path)
    print(f"QC report: {qc_path}")
    return 0 if passed else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scene, slides, slide_times = build_scene()

    # Styleframes-only mode
    if args.styleframes_only:
        sf_dir = output_path.parent / "styleframes"
        run_styleframes(scene, slide_times, sf_dir)
        return 0

    print(f"Duration: {scene.duration:.2f}s | Frames: {int(scene.duration * FPS)}")
    scene.render(str(output_path), show_progress=not args.quiet)

    manifest = build_manifest(slides)
    manifest_path = output_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nRender complete: {output_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Size: {output_path.stat().st_size / (1024 * 1024):.2f} MB")

    if args.skip_qc:
        return 0

    return run_quality_gate(output_path, manifest, scene=scene, slide_times=slide_times)


if __name__ == "__main__":
    raise SystemExit(main())
