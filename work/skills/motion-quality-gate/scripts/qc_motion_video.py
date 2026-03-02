#!/usr/bin/env python3
"""Quality gate for motion infographic renders."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2


WORD_RE = re.compile(r"\S+")


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run quality checks for a rendered motion video.")
    parser.add_argument("--video", required=True, help="Path to rendered mp4 file")
    parser.add_argument("--manifest", required=True, help="Path to manifest json")
    parser.add_argument("--max-words", type=int, default=12, help="Maximum words per text block")
    parser.add_argument("--json-output", default="", help="Optional path to write JSON report")
    return parser.parse_args()


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text.strip()))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError(f"Expected #RRGGBB color, got: {value!r}")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def srgb_to_linear(channel: int) -> float:
    c = channel / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    r, g, b = hex_to_rgb(hex_color)
    return (
        0.2126 * srgb_to_linear(r)
        + 0.7152 * srgb_to_linear(g)
        + 0.0722 * srgb_to_linear(b)
    )


def contrast_ratio(fg: str, bg: str) -> float:
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    high, low = max(l1, l2), min(l1, l2)
    return (high + 0.05) / (low + 0.05)


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a JSON object")
    return data


def check_video_exists(video_path: Path) -> CheckResult:
    if not video_path.exists():
        return CheckResult("video_exists", False, f"Missing file: {video_path}")
    if video_path.stat().st_size <= 0:
        return CheckResult("video_exists", False, f"File is empty: {video_path}")
    return CheckResult("video_exists", True, f"Found file ({video_path.stat().st_size} bytes)")


def get_video_meta(video_path: Path) -> dict[str, float]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"Unable to open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()

    duration = (frames / fps) if fps > 0 else 0.0
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "frames": frames,
        "duration": duration,
    }


def check_metadata(meta: dict[str, float], expected: dict[str, Any]) -> list[CheckResult]:
    results: list[CheckResult] = []

    if "width" in expected:
        passed = int(meta["width"]) == int(expected["width"])
        results.append(CheckResult("width", passed, f"actual={meta['width']} expected={expected['width']}"))

    if "height" in expected:
        passed = int(meta["height"]) == int(expected["height"])
        results.append(CheckResult("height", passed, f"actual={meta['height']} expected={expected['height']}"))

    if "fps" in expected:
        expected_fps = float(expected["fps"])
        passed = abs(meta["fps"] - expected_fps) <= 0.25
        results.append(CheckResult("fps", passed, f"actual={meta['fps']:.2f} expected={expected_fps:.2f}"))

    if "duration_min" in expected and "duration_max" in expected:
        dmin = float(expected["duration_min"])
        dmax = float(expected["duration_max"])
        dur = float(meta["duration"])
        passed = dmin <= dur <= dmax
        results.append(CheckResult("duration", passed, f"actual={dur:.2f}s range=[{dmin:.2f}, {dmax:.2f}]"))

    frames_ok = int(meta["frames"]) > 0
    results.append(CheckResult("frames", frames_ok, f"frames={int(meta['frames'])}"))

    return results


def check_text_budget(slides: list[dict[str, Any]], max_words: int) -> CheckResult:
    violations: list[str] = []

    for slide in slides:
        sid = str(slide.get("id", "slide"))
        texts = slide.get("texts", [])
        if not isinstance(texts, list):
            continue

        for idx, text in enumerate(texts):
            if not isinstance(text, str):
                continue
            wc = word_count(text)
            if wc > max_words:
                violations.append(f"{sid}[{idx}]={wc} words: {text!r}")

    if violations:
        return CheckResult("text_budget", False, "; ".join(violations))
    return CheckResult("text_budget", True, f"All text blocks <= {max_words} words")


def check_contrast(pairs: list[dict[str, Any]]) -> CheckResult:
    failures: list[str] = []

    for pair in pairs:
        label = str(pair.get("label", "pair"))
        fg = str(pair.get("fg", ""))
        bg = str(pair.get("bg", ""))
        min_ratio = float(pair.get("min_ratio", 4.5))

        try:
            ratio = contrast_ratio(fg, bg)
        except Exception as exc:
            failures.append(f"{label}: invalid color ({exc})")
            continue

        if ratio < min_ratio:
            failures.append(f"{label}: {ratio:.2f}:1 < {min_ratio:.2f}:1")

    if failures:
        return CheckResult("contrast", False, "; ".join(failures))
    return CheckResult("contrast", True, "All contrast pairs passed")


def print_report(results: list[CheckResult], meta: dict[str, float]) -> None:
    print("\nQuality Gate Report")
    print("===================")
    print(
        f"video: {int(meta.get('width', 0))}x{int(meta.get('height', 0))}, "
        f"fps={meta.get('fps', 0.0):.2f}, "
        f"frames={int(meta.get('frames', 0))}, "
        f"duration={meta.get('duration', 0.0):.2f}s"
    )

    for result in results:
        mark = "PASS" if result.passed else "FAIL"
        print(f"- [{mark}] {result.name}: {result.details}")


def main() -> int:
    args = parse_args()
    video_path = Path(args.video)
    manifest_path = Path(args.manifest)

    if not manifest_path.exists():
        print(f"FAIL: manifest does not exist: {manifest_path}")
        return 1

    manifest = load_manifest(manifest_path)
    expected = manifest.get("expected", {})
    slides = manifest.get("slides", [])
    contrast_pairs = manifest.get("contrast_pairs", [])

    checks: list[CheckResult] = [check_video_exists(video_path)]

    meta = {
        "width": 0,
        "height": 0,
        "fps": 0.0,
        "frames": 0,
        "duration": 0.0,
    }

    if checks[0].passed:
        try:
            meta = get_video_meta(video_path)
            checks.extend(check_metadata(meta, expected if isinstance(expected, dict) else {}))
        except Exception as exc:
            checks.append(CheckResult("video_metadata", False, str(exc)))

    checks.append(check_text_budget(slides if isinstance(slides, list) else [], args.max_words))
    checks.append(check_contrast(contrast_pairs if isinstance(contrast_pairs, list) else []))

    print_report(checks, meta)

    report = {
        "passed": all(item.passed for item in checks),
        "checks": [item.__dict__ for item in checks],
        "meta": meta,
    }

    if args.json_output:
        out_path = Path(args.json_output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
