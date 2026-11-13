"""
Configuration & Constants for Mushaf Ayah Mask Processing
Al-Shazly Warsh Mushaf (Algeria Edition)
High-Resolution Scan Edition (1488 x 2207)
"""

from pathlib import Path

# Layout geometry
TARGET_WIDTH = 1488
TARGET_HEIGHT = 2207
NUM_LINES = 15

# Standard page padding (for all pages except the opening two)
# Padding is 46.23 px on both x and y directions
PAGE_PADDING_PX = 46.23

# Content bounds normalized:
# x_min = 46.23 / 1488 ~ 0.0311
# y_min = 46.23 / 2207 ~ 0.0209
# x_max = (1488 - 46.23) / 1488 ~ 0.9689
# y_max = (2207 - 46.23) / 2207 ~ 0.9791
CONTENT_BOUNDS_NORMALIZED = (
    round(PAGE_PADDING_PX / TARGET_WIDTH, 4),
    round(PAGE_PADDING_PX / TARGET_HEIGHT, 4),
    round((TARGET_WIDTH - PAGE_PADDING_PX) / TARGET_WIDTH, 4),
    round((TARGET_HEIGHT - PAGE_PADDING_PX) / TARGET_HEIGHT, 4),
)

# Opening pages (0 and 1) explicit bounding boxes
OPENING_HEADER_BOUNDS = {
    "left": 92,
    "top": 88,
    "width": 1304,
    "height": 285
}

OPENING_CONTENT_BOUNDS = {
    "left": 132,
    "top": 488,
    "width": 1222,
    "height": 1224
}

# Calibrated matching thresholds
AYAH_MARKER_THRESHOLD = 0.50
SURAH_HEADER_THRESHOLD = 0.33
NMS_OVERLAP_THRESHOLD = 0.25

# Line-end edge tolerance:
# Spans <= 5.0% from left border are white trailing margin (wrap to next line)
# Spans >= 5.0% contain real words (preserved as start of next ayah)
EDGE_TOLERANCE_PCT = 5.0

# Word slice minimum width to prevent 0-width empty segments
MIN_SLICE_PCT = 0.1

# Hollow Thumun (1/8 Hizb) classification criteria:
# Hollow markers have inner mean >= 245.0, min >= 180, and zero dark pixels (< 128)
HOLLOW_MEAN_MIN = 245.0
HOLLOW_MIN_PIXEL = 180
HOLLOW_DARK_THRESHOLD = 128


def resolve_asset_path(filename: str) -> Path:
    """Finds asset in assets/ directory first, falling back to repository root."""
    asset_in_dir = Path("assets") / filename
    if asset_in_dir.exists():
        return asset_in_dir
    root_asset = Path(filename)
    return root_asset
