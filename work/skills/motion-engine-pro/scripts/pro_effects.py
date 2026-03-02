"""Reusable pro effects for motion_engine scenes."""

from __future__ import annotations

import math
import random
from typing import Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from motion_engine.color import ColorLike, parse_color
from motion_engine.elements import Element


class CachedGlowRect(Element):
    """Glow rectangle that caches its blurred sprite for fast repeated rendering."""

    _SPRITE_CACHE: dict[tuple, Image.Image] = {}

    def __init__(
        self,
        width: float,
        height: float,
        color: ColorLike = "#121a31",
        border_radius: int = 20,
        border_color: ColorLike | None = None,
        border_width: int = 1,
        glow_color: ColorLike = "#7c6aff",
        glow_radius: int = 36,
        glow_opacity: float = 0.35,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.width = int(width)
        self.height = int(height)
        self.color = parse_color(color)
        self.border_radius = int(border_radius)
        self.border_color = parse_color(border_color) if border_color else None
        self.border_width = int(border_width)
        self.glow_color = parse_color(glow_color)
        self.glow_radius = int(glow_radius)
        self.glow_opacity = max(0.0, min(1.0, float(glow_opacity)))
        self._sprite = self._get_or_build_sprite()

    def _cache_key(self) -> tuple:
        border_rgba = self.border_color.rgba if self.border_color else None
        return (
            self.width,
            self.height,
            self.color.rgba,
            self.border_radius,
            border_rgba,
            self.border_width,
            self.glow_color.rgba,
            self.glow_radius,
            round(self.glow_opacity, 3),
        )

    def _get_or_build_sprite(self) -> Image.Image:
        key = self._cache_key()
        sprite = self._SPRITE_CACHE.get(key)
        if sprite is None:
            sprite = self._build_sprite(
                width=self.width,
                height=self.height,
                color=self.color.rgba,
                border_radius=self.border_radius,
                border_color=self.border_color.rgba if self.border_color else None,
                border_width=self.border_width,
                glow_color=self.glow_color.rgba,
                glow_radius=self.glow_radius,
                glow_opacity=self.glow_opacity,
            )
            self._SPRITE_CACHE[key] = sprite
        return sprite

    @staticmethod
    def _build_sprite(
        width: int,
        height: int,
        color: tuple[int, int, int, int],
        border_radius: int,
        border_color: tuple[int, int, int, int] | None,
        border_width: int,
        glow_color: tuple[int, int, int, int],
        glow_radius: int,
        glow_opacity: float,
    ) -> Image.Image:
        pad = max(8, glow_radius * 3)
        sprite_w = width + pad
        sprite_h = height + pad
        ox, oy = pad // 2, pad // 2

        sprite = Image.new("RGBA", (sprite_w, sprite_h), (0, 0, 0, 0))

        glow_buffer = Image.new("RGBA", (sprite_w, sprite_h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_buffer)
        gc = (glow_color[0], glow_color[1], glow_color[2], int(255 * glow_opacity))

        rect = [ox, oy, ox + width - 1, oy + height - 1]
        if border_radius > 0:
            gd.rounded_rectangle(rect, radius=border_radius, fill=gc)
        else:
            gd.rectangle(rect, fill=gc)

        glow_buffer = glow_buffer.filter(ImageFilter.GaussianBlur(radius=glow_radius))
        sprite.paste(glow_buffer, (0, 0), glow_buffer)

        draw = ImageDraw.Draw(sprite)
        if border_radius > 0:
            draw.rounded_rectangle(rect, radius=border_radius, fill=color)
        else:
            draw.rectangle(rect, fill=color)

        if border_color and border_width > 0:
            if border_radius > 0:
                draw.rounded_rectangle(
                    rect,
                    radius=border_radius,
                    outline=border_color,
                    width=border_width,
                )
            else:
                draw.rectangle(rect, outline=border_color, width=border_width)

        return sprite

    def get_bounds(self) -> tuple[float, float]:
        return self._sprite.size

    def draw_content(self, img: Image.Image) -> Image.Image:
        img.paste(self._sprite, (0, 0), self._sprite)
        return img


def _build_vignette_overlay(
    width: int,
    height: int,
    color: ColorLike,
    strength: float,
) -> Image.Image:
    c = parse_color(color)
    y, x = np.ogrid[0:height, 0:width]
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0

    dx = (x - cx) / max(1.0, width / 2.0)
    dy = (y - cy) / max(1.0, height / 2.0)
    dist = np.sqrt(dx * dx + dy * dy)

    edge = np.clip((dist - 0.35) / 0.65, 0.0, 1.0)
    alpha = (edge ** 1.7) * 255.0 * max(0.0, min(1.0, strength))

    arr = np.zeros((height, width, 4), dtype=np.uint8)
    arr[:, :, 0] = c.r
    arr[:, :, 1] = c.g
    arr[:, :, 2] = c.b
    arr[:, :, 3] = alpha.astype(np.uint8)

    return Image.fromarray(arr, "RGBA")


def add_vignette(scene, strength: float = 0.20, color: ColorLike = "#000000") -> None:
    """Apply a precomputed vignette overlay on every frame."""
    overlay = _build_vignette_overlay(scene.width, scene.height, color, strength)

    def _apply(canvas: Image.Image, t: float, frame_num: int) -> Image.Image:
        return Image.alpha_composite(canvas, overlay)

    scene.on_frame(_apply)


def add_soft_grain(scene, opacity: float = 0.04, seed: int = 17) -> None:
    """Apply a static grain overlay to reduce flat digital appearance."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(127, 22, size=(scene.height, scene.width)).clip(0, 255).astype(np.uint8)
    alpha = np.full_like(noise, int(255 * max(0.0, min(1.0, opacity))), dtype=np.uint8)
    grain = np.dstack([noise, noise, noise, alpha])
    overlay = Image.fromarray(grain, "RGBA")

    def _apply(canvas: Image.Image, t: float, frame_num: int) -> Image.Image:
        return Image.alpha_composite(canvas, overlay)

    scene.on_frame(_apply)


def add_floating_orbs(
    scene,
    start: float,
    dur: float,
    palette: Sequence[ColorLike],
    count: int = 7,
    seed: int = 0,
    min_radius: int = 8,
    max_radius: int = 24,
    max_opacity: float = 0.10,
    drift: float = 42.0,
) -> None:
    """Draw slow-moving ambient circles in a bounded time window."""
    rnd = random.Random(seed)
    colors = [parse_color(c) for c in palette]

    orbs = []
    for idx in range(count):
        color = colors[idx % len(colors)]
        orbs.append(
            {
                "x": rnd.uniform(80, scene.width - 80),
                "y": rnd.uniform(140, scene.height - 140),
                "r": rnd.uniform(min_radius, max_radius),
                "phase": rnd.uniform(0.0, math.pi * 2.0),
                "w1": rnd.uniform(0.35, 0.95),
                "w2": rnd.uniform(0.30, 0.90),
                "opacity": rnd.uniform(0.03, max_opacity),
                "rgba": color.rgba,
            }
        )

    def _draw(canvas: Image.Image, t: float, frame_num: int) -> Image.Image:
        if t < start or t > start + dur:
            return canvas

        local_t = t - start
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for orb in orbs:
            x = orb["x"] + math.sin(orb["phase"] + local_t * orb["w1"]) * drift
            y = orb["y"] + math.cos(orb["phase"] + local_t * orb["w2"]) * (drift * 0.7)
            pulse = 0.75 + 0.25 * math.sin(local_t * 0.8 + orb["phase"])
            alpha = int(255 * orb["opacity"] * pulse)
            r = orb["r"]
            rr, gg, bb, _ = orb["rgba"]
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(rr, gg, bb, alpha))

        return Image.alpha_composite(canvas, overlay)

    scene.on_frame(_draw)
