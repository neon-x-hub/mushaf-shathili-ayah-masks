"""
Configuration & Constants for Mushaf Ayah Mask Processing
Al-Shazly Warsh Mushaf (Algeria Edition)
"""

from pathlib import Path

# Layout geometry
TARGET_WIDTH = 621
TARGET_HEIGHT = 878
NUM_LINES = 15

# Inner text box bounds as normalized ratios (x_min, y_min, x_max, y_max)
# Evaluates to x: [31, 591] (width 560 px), y: [24, 853] (line height ~55.25 px)
CONTENT_BOUNDS_NORMALIZED = (0.050, 0.028, 0.952, 0.972)

# Calibrated matching thresholds
AYAH_MARKER_THRESHOLD = 0.58
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
