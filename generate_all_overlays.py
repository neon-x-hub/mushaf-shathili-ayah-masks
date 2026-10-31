#!/usr/bin/env python3
"""
Generate Visual Debug Overlays for All Mushaf Pages - CLI Entry Point
Renders each PDF page with colored ayah polygons, marker boxes, Thumun markers, and surah headers.
"""

from src.overlay import generate_all_overlays, render_page_overlay

if __name__ == "__main__":
    generate_all_overlays()
