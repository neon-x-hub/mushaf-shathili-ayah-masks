#!/usr/bin/env python3
"""
Generate Visual Debug Overlays for Mushaf Pages - CLI Entry Point
Renders PDF pages with colored ayah polygons, marker boxes, Thumun markers, and surah headers.
"""

import argparse
from src.config import TARGET_WIDTH, TARGET_HEIGHT
from src.overlay import generate_all_overlays, render_page_overlay


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate visual verification debug overlays for Mushaf pages.")
    parser.add_argument("--pdf", default="Mushaf-Ashathili.pdf", help="Path to Mushaf PDF")
    parser.add_argument("--pages-dir", default="output/pages", help="Path to per-page JSON directory")
    parser.add_argument("--output", default="output/overlays", help="Directory where overlay images will be saved")
    parser.add_argument("--start", type=int, default=None, help="Start page index (0-based)")
    parser.add_argument("--end", type=int, default=None, help="End page index")
    parser.add_argument("--page", type=int, default=None, help="Render a single specific page index")
    parser.add_argument("--width", type=int, default=TARGET_WIDTH, help="Render target width (default: 1488)")
    parser.add_argument("--height", type=int, default=TARGET_HEIGHT, help="Render target height (default: 2207)")
    parser.add_argument("--quality", type=int, default=85, help="JPEG quality (1-100, default: 85)")
    parser.add_argument("--no-overwrite", action="store_true", help="Skip already rendered overlays")

    args = parser.parse_args()

    generate_all_overlays(
        pdf_path=args.pdf,
        pages_dir=args.pages_dir,
        output_dir=args.output,
        target_width=args.width,
        target_height=args.height,
        start_page=args.start,
        end_page=args.end,
        page_number=args.page,
        overwrite=not args.no_overwrite,
        quality=args.quality
    )


if __name__ == "__main__":
    main()
