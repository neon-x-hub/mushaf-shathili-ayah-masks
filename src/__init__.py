"""
Mushaf Ayah Masks & Geometry Extraction Package
"""

from .config import (
    TARGET_WIDTH,
    TARGET_HEIGHT,
    NUM_LINES,
    CONTENT_BOUNDS_NORMALIZED,
    AYAH_MARKER_THRESHOLD,
    SURAH_HEADER_THRESHOLD,
    EDGE_TOLERANCE_PCT,
)
from .detectors import (
    load_template,
    load_hollow_bitmask,
    load_header_templates,
    detect_ayah_markers,
    detect_surah_headers_full_page,
    classify_marker_hollow,
)
from .segmenter import (
    segment_ayahs_on_page,
    build_svg_path,
    build_normalized_svg_path,
)
from .overlay import (
    render_page_overlay,
    generate_all_overlays,
)
from .pipeline import (
    process_page_data,
    run_pipeline,
)

__version__ = "1.4.0"

__all__ = [
    "run_pipeline",
    "process_page_data",
    "generate_all_overlays",
    "render_page_overlay",
    "segment_ayahs_on_page",
    "build_svg_path",
    "build_normalized_svg_path",
    "detect_ayah_markers",
    "detect_surah_headers_full_page",
    "classify_marker_hollow",
    "load_template",
    "load_hollow_bitmask",
    "load_header_templates",
]
