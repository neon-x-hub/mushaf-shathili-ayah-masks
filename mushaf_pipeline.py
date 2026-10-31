#!/usr/bin/env python3
"""
Mushaf Ayah Mask Generator - CLI Entry Point
Extracts verse markers, surah headers, thumun indicators, line segments, and SVG paths.
"""

import sys
from src.pipeline import main, run_pipeline, process_page_data
from src.detectors import (
    load_template,
    load_hollow_bitmask,
    load_header_templates,
    detect_ayah_markers,
    detect_surah_headers_full_page,
)
from src.segmenter import (
    segment_ayahs_on_page,
    build_svg_path,
    build_normalized_svg_path,
)
from src.overlay import render_page_overlay

if __name__ == "__main__":
    main()
