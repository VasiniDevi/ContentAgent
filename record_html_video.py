#!/usr/bin/env python3
"""Record an HTML motion infographic as a video using Playwright.

Captures the HTML animation frame-by-frame at 30fps, then assembles
into an MP4 video using ffmpeg.
"""

import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def record_html_to_video(
    html_path: str,
    output_path: str = "work/output/infographic.mp4",
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
):
    html_path = Path(html_path).resolve()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    frames_dir = Path("work/recording_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Clean previous frames
    for f in frames_dir.glob("*.png"):
        f.unlink()

    # Calculate total duration from slide data-duration attributes
    # Slides: 5000, 4500, 6000, 4500, 5500, 5500, 4500, 6000, 6000, 5000 = 52500ms
    total_duration_ms = 52500
    total_frames = int(total_duration_ms / 1000 * fps)

    print(f"Recording {html_path.name}")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps}")
    print(f"  Duration: {total_duration_ms/1000:.1f}s ({total_frames} frames)")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
        )
        page = context.new_page()

        # Load the HTML file
        page.goto(f"file://{html_path}")
        page.wait_for_load_state("networkidle")

        # Wait for fonts to load
        time.sleep(2)

        # Pause the auto-play so we control timing manually
        page.evaluate("isPlaying = false; clearTimeout(timer);")

        print("Capturing frames...")

        frame_num = 0

        for slide_idx in range(10):
            # Go to this slide
            page.evaluate(f"goToSlide({slide_idx})")

            # Get slide duration
            durations = [5000, 4500, 6000, 4500, 5500, 5500, 4500, 6000, 6000, 5000]
            slide_duration_ms = durations[slide_idx]
            slide_frames = int(slide_duration_ms / 1000 * fps)

            print(f"  Slide {slide_idx}: {slide_duration_ms}ms ({slide_frames} frames)")

            for f in range(slide_frames):
                # Advance time for CSS animations
                elapsed_ms = f * (1000 / fps)

                # Take screenshot
                frame_path = frames_dir / f"frame_{frame_num:05d}.png"
                page.screenshot(path=str(frame_path))
                frame_num += 1

                # Wait real time for CSS animations to progress
                page.wait_for_timeout(int(1000 / fps))

        browser.close()

    print(f"\nCaptured {frame_num} frames")
    print("Assembling video with ffmpeg...")

    # Assemble frames into video
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "slow",
        "-movflags", "+faststart",
        str(output_path),
    ]

    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}")
        sys.exit(1)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\nDone! Output: {output_path} ({size_mb:.1f} MB)")

    # Clean up frames
    for f in frames_dir.glob("*.png"):
        f.unlink()
    frames_dir.rmdir()

    return str(output_path)


if __name__ == "__main__":
    html_file = sys.argv[1] if len(sys.argv) > 1 else "Ref/motion-infographic.html"
    record_html_to_video(html_file)
