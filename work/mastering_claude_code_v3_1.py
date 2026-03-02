"""Mastering Claude Code v3.1 - visual art direction pass (1080x1920, 30fps)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_SKILLS_ROOT = PROJECT_ROOT / ".agents/skills"
WORK_SKILLS_ROOT = PROJECT_ROOT / "work/skills"

sys.path.insert(0, os.path.expanduser("~/.claude/skills"))

PRO_EFFECTS_DIR = AGENT_SKILLS_ROOT / "motion-engine-pro/scripts"
if not PRO_EFFECTS_DIR.exists():
    PRO_EFFECTS_DIR = WORK_SKILLS_ROOT / "motion-engine-pro/scripts"
sys.path.insert(0, str(PRO_EFFECTS_DIR))

from motion_engine.elements import Circle, GradientRect, Rect, Text
from motion_engine.scene import Scene
from motion_templates.transitions import dissolve_transition, slide_transition, wipe_transition, zoom_transition
from pro_effects import CachedGlowRect, add_floating_orbs, add_soft_grain, add_vignette


W = 1080
H = 1920
FPS = 30

TOKENS = {
    "bg": "#060910",
    "bg_soft": "#0d1322",
    "card_bg": "#121a31",
    "card_border": "#2e3b67",
    "text": "#f4f7ff",
    "text_secondary": "#ccd5f3",
    "text_muted": "#aab6e6",
    "purple": "#7c6aff",
    "green": "#4ade80",
    "orange": "#ff9f43",
    "cyan": "#22d3ee",
}

FONT_CANDIDATES = {
    "display": [
        "/System/Library/Fonts/Supplemental/Didot.ttc",
        "/System/Library/Fonts/Supplemental/Bodoni 72.ttc",
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
    ],
    "body": [
        "/System/Library/Fonts/Supplemental/GillSans.ttc",
        "/System/Library/Fonts/Supplemental/Futura.ttc",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    ],
    "label": [
        "/System/Library/Fonts/Supplemental/Futura.ttc",
        "/System/Library/Fonts/Supplemental/GillSans.ttc",
    ],
}


def pick_font(paths: list[str]) -> str | None:
    for path in paths:
        if Path(path).exists():
            return path
    return None


DISPLAY_FONT = pick_font(FONT_CANDIDATES["display"])
BODY_FONT = pick_font(FONT_CANDIDATES["body"])
LABEL_FONT = pick_font(FONT_CANDIDATES["label"])


class ArtText(Text):
    """Text wrapper with extra canvas padding to avoid glyph clipping."""

    def get_bounds(self) -> tuple[float, float]:
        w, h = super().get_bounds()
        return (w + 8, h + 16)


# Use ArtText everywhere in this script without changing callsites.
Text = ArtText


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render mastering_claude_code_v3_1 motion infographic.")
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "work/mastering_claude_code_v3_1.mp4"),
        help="Output mp4 path",
    )
    parser.add_argument("--skip-qc", action="store_true", help="Skip quality gate run")
    parser.add_argument("--quiet", action="store_true", help="Disable render progress output")
    return parser.parse_args()


def add_background_planes(scene: Scene, start: float, dur: float, accent: str, opposite: str) -> None:
    plane1 = Rect(int(W * 1.6), 260, color=accent, pos=(W * 0.30, H * 0.52), rotation=-21)
    plane1.opacity = 0.04
    scene.add(
        plane1,
        enter=start,
        dur=dur,
        exit=start + dur,
        enter_anim="fade_in",
        exit_anim="fade_out",
        enter_dur=0.7,
        exit_dur=0.35,
        z_index=-20,
    )

    plane2 = Rect(int(W * 1.5), 220, color=opposite, pos=(W * 0.78, H * 0.70), rotation=17)
    plane2.opacity = 0.035
    scene.add(
        plane2,
        enter=start + 0.2,
        dur=dur - 0.2,
        exit=start + dur,
        enter_anim="fade_in",
        exit_anim="fade_out",
        enter_dur=0.7,
        exit_dur=0.35,
        z_index=-19,
    )


def add_tracker(scene: Scene, start: float, dur: float, label: str, progress: float, color: str) -> None:
    x = W // 2
    y = 132
    rail_w = 470

    rail = Rect(rail_w, 7, color="#1f2847", border_radius=4, pos=(x, y))
    rail.opacity = 0.95
    scene.add(
        rail,
        enter=start + 0.05,
        dur=dur - 0.20,
        exit=start + dur - 0.10,
        enter_anim="fade_in",
        exit_anim="fade_out",
        enter_dur=0.22,
        exit_dur=0.18,
        z_index=40,
    )

    fill = GradientRect(
        max(12, int(rail_w * progress)),
        7,
        start_color=color,
        end_color=TOKENS["cyan"],
        angle=0,
        border_radius=4,
        pos=(x - rail_w / 2, y),
        anchor=(0, 0.5),
    )
    scene.add(
        fill,
        enter=start + 0.12,
        dur=dur - 0.28,
        exit=start + dur - 0.10,
        enter_anim="scale_in",
        exit_anim="fade_out",
        enter_dur=0.32,
        exit_dur=0.18,
        enter_easing="ease_out_cubic",
        z_index=41,
    )

    rule = Text(label, font=LABEL_FONT, font_size=21, color=TOKENS["text_muted"], pos=(x, y - 30))
    scene.add(
        rule,
        enter=start + 0.08,
        dur=dur - 0.25,
        exit=start + dur - 0.12,
        enter_anim="fade_up",
        exit_anim="fade_out",
        enter_dur=0.25,
        exit_dur=0.18,
        z_index=42,
    )


def add_accent_line(scene: Scene, start: float, dur: float, x: float, y: float, width: int, c1: str, c2: str) -> None:
    line = GradientRect(width, 4, start_color=c1, end_color=c2, angle=0, border_radius=2, pos=(x, y))
    scene.add(
        line,
        enter=start,
        dur=dur,
        exit=start + dur,
        enter_anim="scale_in",
        exit_anim="fade_out",
        enter_dur=0.30,
        exit_dur=0.2,
        enter_easing="ease_out_cubic",
    )


def add_pill(scene: Scene, start: float, dur: float, x: float, y: float, text: str, color: str, width: int) -> None:
    bg = Rect(width, 44, color=color, border_radius=22, pos=(x, y))
    bg.opacity = 0.19
    scene.add(
        bg,
        enter=start,
        dur=dur,
        exit=start + dur,
        enter_anim="scale_in",
        exit_anim="fade_out",
        enter_dur=0.24,
        exit_dur=0.2,
        enter_easing="ease_out_back",
    )

    tx = Text(text, font=LABEL_FONT, font_size=19, color=color, pos=(x, y))
    scene.add(
        tx,
        enter=start + 0.08,
        dur=dur - 0.12,
        exit=start + dur,
        enter_anim="fade_in",
        exit_anim="fade_out",
        enter_dur=0.2,
        exit_dur=0.2,
    )


def add_transition_flourish(scene: Scene, t: float, variant: int, accent: str) -> None:
    if variant == 1:
        wipe_transition(scene, start=t - 0.30, dur=0.60, direction="left", color="#04060d")
        zoom_transition(scene, start=t - 0.16, dur=0.34, color="#070912")
    elif variant == 2:
        dissolve_transition(scene, start=t - 0.35, dur=0.70, color="#070912")
        slide_transition(scene, start=t - 0.24, dur=0.48, direction="right")
    elif variant == 3:
        wipe_transition(scene, start=t - 0.30, dur=0.58, direction="down", color="#05080f")
        dissolve_transition(scene, start=t - 0.18, dur=0.36, color="#070912")
    else:
        zoom_transition(scene, start=t - 0.32, dur=0.62, color="#060910")
        wipe_transition(scene, start=t - 0.20, dur=0.40, direction="up", color="#060910")

    streak_top = GradientRect(int(W * 1.5), 5, start_color=accent, end_color=TOKENS["cyan"], angle=0, pos=(W // 2, int(H * 0.25)))
    streak_top.opacity = 0.7
    scene.add(
        streak_top,
        enter=t - 0.22,
        dur=0.40,
        exit=t + 0.18,
        enter_anim="slide_left",
        exit_anim="fade_out",
        enter_dur=0.22,
        exit_dur=0.18,
        z_index=120,
    )

    streak_bot = GradientRect(int(W * 1.4), 5, start_color=TOKENS["cyan"], end_color=accent, angle=0, pos=(W // 2, int(H * 0.78)))
    streak_bot.opacity = 0.55
    scene.add(
        streak_bot,
        enter=t - 0.16,
        dur=0.36,
        exit=t + 0.2,
        enter_anim="slide_right",
        exit_anim="fade_out",
        enter_dur=0.2,
        exit_dur=0.16,
        z_index=119,
    )


def build_scene() -> tuple[Scene, list[dict[str, object]]]:
    scene = Scene(W, H, fps=FPS, bg=TOKENS["bg"])
    slides_manifest: list[dict[str, object]] = []

    add_vignette(scene, strength=0.23, color="#000000")
    add_soft_grain(scene, opacity=0.04, seed=21)

    t = 0.0

    # ------------------------------------------------------------------
    # Slide 1 - title (right-leaning hero)
    # ------------------------------------------------------------------
    s1_dur = 6.0
    add_background_planes(scene, t, s1_dur, TOKENS["purple"], TOKENS["cyan"])
    add_tracker(scene, t, s1_dur, label="Rule 1/5", progress=0.20, color=TOKENS["purple"])
    add_floating_orbs(
        scene,
        start=t,
        dur=s1_dur,
        palette=[TOKENS["purple"], TOKENS["cyan"]],
        count=7,
        seed=10,
        max_opacity=0.08,
    )

    hero = CachedGlowRect(
        760,
        390,
        color=TOKENS["card_bg"],
        border_radius=30,
        border_color=TOKENS["card_border"],
        border_width=1,
        glow_color=TOKENS["purple"],
        glow_radius=42,
        glow_opacity=0.40,
        pos=(W - 75, 705),
        anchor=(1, 0.5),
        rotation=-1.6,
    )
    scene.add(
        hero,
        enter=t + 0.22,
        dur=s1_dur - 0.54,
        exit=t + s1_dur - 0.22,
        enter_anim="fade_left",
        exit_anim="fade_out",
        enter_dur=0.48,
        exit_dur=0.34,
    )

    title_a = Text(
        "Mastering",
        font=DISPLAY_FONT,
        font_size=92,
        color=TOKENS["text"],
        pos=(W - 700, 620),
        anchor=(0, 0.5),
        max_width=560,
    )
    scene.add(
        title_a,
        enter=t + 0.45,
        dur=s1_dur - 1.0,
        exit=t + s1_dur - 0.28,
        enter_anim="fade_up",
        exit_anim="fade_out",
        enter_dur=0.42,
        exit_dur=0.26,
    )

    title_b = Text(
        "Claude Code",
        font=DISPLAY_FONT,
        font_size=96,
        color=TOKENS["text"],
        pos=(W - 660, 730),
        anchor=(0, 0.5),
        max_width=580,
    )
    scene.add(
        title_b,
        enter=t + 0.60,
        dur=s1_dur - 1.2,
        exit=t + s1_dur - 0.28,
        enter_anim="fade_up",
        exit_anim="fade_out",
        enter_dur=0.42,
        exit_dur=0.26,
    )

    add_accent_line(scene, t + 0.88, s1_dur - 1.5, W - 610, 808, 205, TOKENS["purple"], TOKENS["cyan"])

    subtitle = Text("Pro workflow guide", font=BODY_FONT, font_size=36, color=TOKENS["text_secondary"], pos=(W - 640, 875), anchor=(0, 0.5))
    scene.add(
        subtitle,
        enter=t + 1.04,
        dur=s1_dur - 1.62,
        exit=t + s1_dur - 0.28,
        enter_anim="fade_up",
        exit_anim="fade_out",
        enter_dur=0.34,
        exit_dur=0.24,
    )

    side_rule = Rect(6, 230, color=TOKENS["cyan"], border_radius=3, pos=(130, 740))
    side_rule.opacity = 0.25
    scene.add(side_rule, enter=t + 0.55, dur=s1_dur - 1.0, exit=t + s1_dur - 0.28, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.45, exit_dur=0.24)

    ring_a = Circle(radius=190, color=TOKENS["purple"], pos=(210, 910))
    ring_a.opacity = 0.05
    scene.add(ring_a, enter=t + 0.35, dur=s1_dur - 0.9, exit=t + s1_dur - 0.2, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.8, exit_dur=0.3)

    slides_manifest.append(
        {
            "id": "title",
            "texts": [
                "Mastering Claude Code",
                "Pro workflow guide",
            ],
        }
    )

    t += s1_dur
    add_transition_flourish(scene, t, variant=1, accent=TOKENS["purple"])

    # ------------------------------------------------------------------
    # Slide 2 - rule 1 (upper-left block)
    # ------------------------------------------------------------------
    s2_dur = 7.0
    add_background_planes(scene, t, s2_dur, TOKENS["purple"], TOKENS["bg_soft"])
    add_tracker(scene, t, s2_dur, label="Rule 1/3", progress=0.33, color=TOKENS["purple"])
    add_floating_orbs(
        scene,
        start=t,
        dur=s2_dur,
        palette=[TOKENS["purple"], TOKENS["cyan"]],
        count=6,
        seed=33,
        max_opacity=0.07,
    )

    wm2 = Text("01", font=DISPLAY_FONT, font_size=250, color=TOKENS["purple"], pos=(930, 300))
    wm2.opacity = 0.06
    scene.add(wm2, enter=t + 0.16, dur=s2_dur - 0.7, exit=t + s2_dur - 0.2, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.55, exit_dur=0.3)

    card2 = CachedGlowRect(
        670,
        470,
        color=TOKENS["card_bg"],
        border_radius=26,
        border_color=TOKENS["card_border"],
        border_width=1,
        glow_color=TOKENS["purple"],
        glow_radius=36,
        glow_opacity=0.35,
        pos=(75, 700),
        anchor=(0, 0.5),
        rotation=-1.2,
    )
    scene.add(card2, enter=t + 0.30, dur=s2_dur - 0.82, exit=t + s2_dur - 0.24, enter_anim="slide_right", exit_anim="fade_out", enter_dur=0.5, exit_dur=0.33)

    h2 = Text(
        "Interrogate first",
        font=DISPLAY_FONT,
        font_size=72,
        color=TOKENS["text"],
        pos=(130, 575),
        anchor=(0, 0.5),
        max_width=560,
    )
    scene.add(h2, enter=t + 0.48, dur=s2_dur - 1.0, exit=t + s2_dur - 0.28, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.38, exit_dur=0.24)

    add_accent_line(scene, t + 0.74, s2_dur - 1.36, 250, 640, 165, TOKENS["purple"], TOKENS["cyan"])

    s2_sub = Text(
        "Ask before code.",
        font=BODY_FONT,
        font_size=38,
        color=TOKENS["text_secondary"],
        pos=(130, 712),
        anchor=(0, 0.5),
        max_width=520,
    )
    scene.add(s2_sub, enter=t + 0.86, dur=s2_dur - 1.58, exit=t + s2_dur - 0.30, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.3, exit_dur=0.24)

    add_pill(scene, t + 1.42, s2_dur - 2.64, 245, 820, "Goal?", TOKENS["purple"], 172)
    add_pill(scene, t + 1.66, s2_dur - 2.88, 468, 820, "Constraints?", TOKENS["purple"], 218)
    add_pill(scene, t + 1.92, s2_dur - 3.14, 315, 884, "Edge cases?", TOKENS["purple"], 195)
    add_pill(scene, t + 3.24, s2_dur - 4.4, 338, 980, "Clarity prevents rework", TOKENS["purple"], 370)

    slides_manifest.append(
        {
            "id": "rule_1",
            "texts": [
                "Interrogate first",
                "Ask before code.",
                "Goal?",
                "Constraints?",
                "Edge cases?",
                "Clarity prevents rework",
            ],
        }
    )

    t += s2_dur
    add_transition_flourish(scene, t, variant=2, accent=TOKENS["green"])

    # ------------------------------------------------------------------
    # Slide 3 - rule 2 (lower-right block)
    # ------------------------------------------------------------------
    s3_dur = 7.0
    add_background_planes(scene, t, s3_dur, TOKENS["green"], TOKENS["cyan"])
    add_tracker(scene, t, s3_dur, label="Rule 2/3", progress=0.66, color=TOKENS["green"])
    add_floating_orbs(
        scene,
        start=t,
        dur=s3_dur,
        palette=[TOKENS["green"], TOKENS["cyan"], TOKENS["purple"]],
        count=7,
        seed=49,
        max_opacity=0.08,
    )

    wm3 = Text("02", font=DISPLAY_FONT, font_size=250, color=TOKENS["green"], pos=(150, 300))
    wm3.opacity = 0.055
    scene.add(wm3, enter=t + 0.16, dur=s3_dur - 0.7, exit=t + s3_dur - 0.2, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.55, exit_dur=0.3)

    card3 = CachedGlowRect(
        700,
        450,
        color=TOKENS["card_bg"],
        border_radius=26,
        border_color=TOKENS["card_border"],
        border_width=1,
        glow_color=TOKENS["green"],
        glow_radius=36,
        glow_opacity=0.33,
        pos=(W - 70, 900),
        anchor=(1, 0.5),
        rotation=1.4,
    )
    scene.add(card3, enter=t + 0.32, dur=s3_dur - 0.84, exit=t + s3_dur - 0.24, enter_anim="slide_left", exit_anim="fade_out", enter_dur=0.5, exit_dur=0.33)

    h3 = Text(
        "One feature at a time",
        font=DISPLAY_FONT,
        font_size=66,
        color=TOKENS["text"],
        pos=(W - 115, 760),
        anchor=(1, 0.5),
        max_width=630,
    )
    scene.add(h3, enter=t + 0.50, dur=s3_dur - 1.03, exit=t + s3_dur - 0.28, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.36, exit_dur=0.24)

    add_accent_line(scene, t + 0.78, s3_dur - 1.42, W - 325, 828, 200, TOKENS["green"], TOKENS["cyan"])

    s3_sub = Text(
        "Build A. Test A. Then B.",
        font=BODY_FONT,
        font_size=35,
        color=TOKENS["text_secondary"],
        pos=(W - 115, 898),
        anchor=(1, 0.5),
        max_width=620,
    )
    scene.add(s3_sub, enter=t + 0.90, dur=s3_dur - 1.62, exit=t + s3_dur - 0.30, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.3, exit_dur=0.24)

    chain = [("A", TOKENS["green"], W - 600), ("B", TOKENS["cyan"], W - 450), ("C", TOKENS["purple"], W - 300)]
    for idx, (label, col, x) in enumerate(chain):
        c = Circle(radius=32, color=col, pos=(x, 1000))
        c.opacity = 0.22
        scene.add(c, enter=t + 1.38 + idx * 0.2, dur=s3_dur - 2.58, exit=t + s3_dur - 0.30, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.3, exit_dur=0.2, enter_easing="ease_out_back")

        l = Text(label, font=LABEL_FONT, font_size=24, color=col, pos=(x, 1000))
        scene.add(l, enter=t + 1.48 + idx * 0.2, dur=s3_dur - 2.72, exit=t + s3_dur - 0.30, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.18, exit_dur=0.18)

        if idx < 2:
            ar = Text(">", font=LABEL_FONT, font_size=36, color=TOKENS["text_muted"], pos=(x + 75, 1000)
            )
            scene.add(ar, enter=t + 1.55 + idx * 0.2, dur=s3_dur - 2.78, exit=t + s3_dur - 0.30, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.18, exit_dur=0.18)

    add_pill(scene, t + 3.18, s3_dur - 4.36, W - 355, 1092, "Ship in stable slices", TOKENS["green"], 345)

    slides_manifest.append(
        {
            "id": "rule_2",
            "texts": [
                "One feature at a time",
                "Build A. Test A. Then B.",
                "Ship in stable slices",
            ],
        }
    )

    t += s3_dur
    add_transition_flourish(scene, t, variant=3, accent=TOKENS["orange"])

    # ------------------------------------------------------------------
    # Slide 4 - rule 3 (lower-left emphasis)
    # ------------------------------------------------------------------
    s4_dur = 7.0
    add_background_planes(scene, t, s4_dur, TOKENS["orange"], "#ff6b6b")
    add_tracker(scene, t, s4_dur, label="Rule 3/3", progress=1.0, color=TOKENS["orange"])
    add_floating_orbs(
        scene,
        start=t,
        dur=s4_dur,
        palette=[TOKENS["orange"], "#ff6b6b"],
        count=6,
        seed=57,
        max_opacity=0.08,
    )

    wm4 = Text("03", font=DISPLAY_FONT, font_size=250, color=TOKENS["orange"], pos=(915, 290))
    wm4.opacity = 0.055
    scene.add(wm4, enter=t + 0.2, dur=s4_dur - 0.72, exit=t + s4_dur - 0.2, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.55, exit_dur=0.3)

    card4 = CachedGlowRect(
        720,
        500,
        color=TOKENS["card_bg"],
        border_radius=26,
        border_color=TOKENS["card_border"],
        border_width=1,
        glow_color=TOKENS["orange"],
        glow_radius=38,
        glow_opacity=0.34,
        pos=(70, 1030),
        anchor=(0, 0.5),
        rotation=-0.8,
    )
    scene.add(card4, enter=t + 0.34, dur=s4_dur - 0.86, exit=t + s4_dur - 0.24, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.5, exit_dur=0.33)

    h4 = Text(
        "Refresh at 50%",
        font=DISPLAY_FONT,
        font_size=74,
        color=TOKENS["text"],
        pos=(120, 860),
        anchor=(0, 0.5),
        max_width=560,
    )
    scene.add(h4, enter=t + 0.50, dur=s4_dur - 1.0, exit=t + s4_dur - 0.28, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.36, exit_dur=0.24)

    add_accent_line(scene, t + 0.78, s4_dur - 1.42, 285, 932, 190, TOKENS["orange"], "#ff6b6b")

    s4_sub = Text(
        "Fresh context. accurate code.",
        font=BODY_FONT,
        font_size=36,
        color=TOKENS["text_secondary"],
        pos=(120, 1015),
        anchor=(0, 0.5),
        max_width=620,
    )
    scene.add(s4_sub, enter=t + 0.94, dur=s4_dur - 1.66, exit=t + s4_dur - 0.30, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.3, exit_dur=0.24)

    rail = Rect(460, 22, color="#1f2847", border_radius=11, pos=(150, 1118), anchor=(0, 0.5))
    scene.add(rail, enter=t + 1.22, dur=s4_dur - 2.16, exit=t + s4_dur - 0.35, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.24, exit_dur=0.2)

    fill = GradientRect(230, 22, start_color=TOKENS["orange"], end_color="#ff6b6b", angle=0, border_radius=11, pos=(150, 1118), anchor=(0, 0.5))
    scene.add(fill, enter=t + 1.40, dur=s4_dur - 2.34, exit=t + s4_dur - 0.35, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.4, exit_dur=0.2)

    pct = Text("50%", font=LABEL_FONT, font_size=24, color=TOKENS["orange"], pos=(655, 1118))
    scene.add(pct, enter=t + 1.55, dur=s4_dur - 2.48, exit=t + s4_dur - 0.35, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.18, exit_dur=0.18)

    icon = Rect(34, 34, color=TOKENS["orange"], border_radius=6, pos=(690, 1045), rotation=45)
    icon.opacity = 0.2
    scene.add(icon, enter=t + 1.28, dur=s4_dur - 2.25, exit=t + s4_dur - 0.35, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.3, exit_dur=0.2)

    add_pill(scene, t + 3.20, s4_dur - 4.40, 360, 1230, "New session. better precision", TOKENS["orange"], 400)

    slides_manifest.append(
        {
            "id": "rule_3",
            "texts": [
                "Refresh at 50%",
                "Fresh context. accurate code.",
                "New session. better precision",
            ],
        }
    )

    t += s4_dur
    add_transition_flourish(scene, t, variant=4, accent=TOKENS["cyan"])

    # ------------------------------------------------------------------
    # Slide 5 - summary (offset stack)
    # ------------------------------------------------------------------
    s5_dur = 7.0
    add_background_planes(scene, t, s5_dur, TOKENS["purple"], TOKENS["cyan"])
    add_tracker(scene, t, s5_dur, label="Rule 3/3", progress=1.0, color=TOKENS["cyan"])
    add_floating_orbs(
        scene,
        start=t,
        dur=s5_dur,
        palette=[TOKENS["purple"], TOKENS["green"], TOKENS["orange"]],
        count=8,
        seed=73,
        max_opacity=0.08,
    )

    blob = Circle(radius=455, color=TOKENS["purple"], pos=(330, 1080))
    blob.opacity = 0.055
    scene.add(blob, enter=t + 0.16, dur=s5_dur - 0.55, exit=t + s5_dur - 0.2, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.75, exit_dur=0.3)

    h5 = Text(
        "The 3 rules",
        font=DISPLAY_FONT,
        font_size=80,
        color=TOKENS["text"],
        pos=(W - 110, 400),
        anchor=(1, 0.5),
        max_width=520,
    )
    scene.add(h5, enter=t + 0.30, dur=s5_dur - 0.88, exit=t + s5_dur - 0.26, enter_anim="fade_up", exit_anim="fade_out", enter_dur=0.38, exit_dur=0.24)

    add_accent_line(scene, t + 0.58, s5_dur - 1.22, W - 270, 475, 150, TOKENS["cyan"], TOKENS["purple"])

    rows = [
        ("1", "Interrogate first", TOKENS["purple"], 120),
        ("2", "One at a time", TOKENS["green"], 170),
        ("3", "Refresh at 50%", TOKENS["orange"], 230),
    ]

    for idx, (num, label, accent, x) in enumerate(rows):
        y = 700 + idx * 175
        enter_t = t + 0.90 + idx * 0.26

        row = CachedGlowRect(
            730,
            112,
            color=TOKENS["card_bg"],
            border_radius=21,
            border_color=TOKENS["card_border"],
            border_width=1,
            glow_color=accent,
            glow_radius=30,
            glow_opacity=0.31,
            pos=(x, y),
            anchor=(0, 0.5),
            rotation=(-0.8 + idx * 0.6),
        )
        scene.add(row, enter=enter_t, dur=s5_dur - 1.75 - idx * 0.20, exit=t + s5_dur - 0.24, enter_anim="fade_right", exit_anim="fade_out", enter_dur=0.34, exit_dur=0.22)

        badge = Circle(radius=22, color=accent, pos=(x + 55, y))
        scene.add(badge, enter=enter_t + 0.08, dur=s5_dur - 1.90 - idx * 0.20, exit=t + s5_dur - 0.24, enter_anim="scale_in", exit_anim="fade_out", enter_dur=0.24, exit_dur=0.2)

        nt = Text(num, font=LABEL_FONT, font_size=20, color="#09101c", pos=(x + 55, y))
        scene.add(nt, enter=enter_t + 0.14, dur=s5_dur - 2.00 - idx * 0.20, exit=t + s5_dur - 0.24, enter_anim="fade_in", exit_anim="fade_out", enter_dur=0.16, exit_dur=0.16)

        lt = Text(label, font=BODY_FONT, font_size=39, color=TOKENS["text"], pos=(x + 125, y), anchor=(0, 0.5))
        scene.add(lt, enter=enter_t + 0.15, dur=s5_dur - 2.05 - idx * 0.20, exit=t + s5_dur - 0.24, enter_anim="fade_left", exit_anim="fade_out", enter_dur=0.24, exit_dur=0.2)

    slides_manifest.append(
        {
            "id": "summary",
            "texts": [
                "The 3 rules",
                "Interrogate first",
                "One at a time",
                "Refresh at 50%",
            ],
        }
    )

    scene.duration = t + s5_dur + 0.5
    return scene, slides_manifest


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
            {"label": "headline_on_card", "fg": TOKENS["text"], "bg": TOKENS["card_bg"], "min_ratio": 4.5},
            {"label": "body_on_card", "fg": TOKENS["text_secondary"], "bg": TOKENS["card_bg"], "min_ratio": 4.5},
            {"label": "label_on_card", "fg": TOKENS["text_muted"], "bg": TOKENS["card_bg"], "min_ratio": 3.0},
        ],
    }


def run_quality_gate(video_path: Path, manifest_path: Path) -> int:
    qc_script = AGENT_SKILLS_ROOT / "motion-quality-gate/scripts/qc_motion_video.py"
    if not qc_script.exists():
        qc_script = WORK_SKILLS_ROOT / "motion-quality-gate/scripts/qc_motion_video.py"

    qc_json = video_path.with_suffix(".qc.json")

    cmd = [
        sys.executable,
        str(qc_script),
        "--video",
        str(video_path),
        "--manifest",
        str(manifest_path),
        "--max-words",
        "12",
        "--json-output",
        str(qc_json),
    ]

    print("\nRunning quality gate...")
    result = subprocess.run(cmd, check=False)
    print(f"QC report: {qc_json}")
    return result.returncode


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scene, slides = build_scene()

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

    return run_quality_gate(output_path, manifest_path)


if __name__ == "__main__":
    raise SystemExit(main())
