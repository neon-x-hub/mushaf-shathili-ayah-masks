"""
Ayah Line Segmenter & SVG Path Generator
Handles RTL Arabic text flow, line-boundary wrapping, word preservation, and Thumun merging.
"""

from typing import List, Dict, Any, Set, Tuple
from .config import EDGE_TOLERANCE_PCT, MIN_SLICE_PCT


def build_svg_path(polygons: List[List[List[int]]]) -> str:
    """Constructs a combined SVG path string 'M x y L x y ... Z' from pixel polygons."""
    commands = []
    for poly in polygons:
        pts = " ".join([f"L {p[0]} {p[1]}" for p in poly[1:]])
        commands.append(f"M {poly[0][0]} {poly[0][1]} {pts} Z")
    return " ".join(commands)


def build_normalized_svg_path(polygons: List[List[List[int]]], width: int, height: int) -> str:
    """Constructs a normalized SVG path string (0.0 to 1.0) for resolution-independent scaling."""
    commands = []
    for poly in polygons:
        pts = " ".join([f"L {p[0]/width:.4f} {p[1]/height:.4f}" for p in poly[1:]])
        commands.append(f"M {poly[0][0]/width:.4f} {poly[0][1]/height:.4f} {pts} Z")
    return " ".join(commands)


def build_compact_string(s_pct: float, e_pct: float) -> Any:
    """Encodes a line span in standard compact notation."""
    if s_pct >= 99.0 and e_pct <= 1.0:
        return "f"
    elif s_pct < 99.0 and e_pct <= 1.0:
        return f"{s_pct:.3f}%"
    elif s_pct >= 99.0 and e_pct > 1.0:
        return f"{e_pct:.3f}%"
    else:
        return [f"{s_pct:.3f}%", f"{e_pct:.3f}%"]


def segment_ayahs_on_page(
    markers: List[Dict[str, Any]],
    header_lines: Set[int],
    content_bounds: Tuple[int, int, int, int],
    page_dimensions: Tuple[int, int],
    num_lines: int = 15,
    edge_tolerance_pct: float = EDGE_TOLERANCE_PCT
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """
    Builds verse masks across 15 lines. Merges across unnumbered Thumun markers
    so complete Quranic verses are preserved as single unified masks.
    """
    W, H = page_dimensions
    x_min, y_min, x_max, y_max = content_bounds
    line_width = x_max - x_min
    line_height = (y_max - y_min) / num_lines

    thumun_markers = [m for m in markers if m.get("is_hollow", False)]
    ayah_markers = [m for m in markers if not m.get("is_hollow", False)]

    ayahs = []
    curr_line = 0
    curr_start_pct = 100.0  # 100% = right margin, 0% = left margin

    # Advance initial line past any header banner at the top of the page
    while curr_line < num_lines and curr_line in header_lines:
        curr_line += 1
        curr_start_pct = 100.0

    for m in ayah_markers:
        m_line = m["line"]
        end_x = max(x_min, min(x_max, m["x_left"]))
        end_pct = ((end_x - x_min) / line_width) * 100.0

        # Snap left boundary to 0.0% (border of bounding box) if remaining margin is ignored as whitespace
        snap_to_border = (end_pct < edge_tolerance_pct)
        effective_end_pct = 0.0 if snap_to_border else end_pct

        compact_array = []
        segments = []
        pixel_polygons = []

        for l in range(curr_line, m_line + 1):
            if l in header_lines:
                continue

            ly1 = int(y_min + l * line_height)
            ly2 = int(y_min + (l + 1) * line_height)

            s_pct = curr_start_pct if l == curr_line else 100.0
            e_pct = effective_end_pct if l == m_line else 0.0

            if s_pct - e_pct < MIN_SLICE_PCT:
                continue

            compact_array.append(build_compact_string(s_pct, e_pct))

            px_left = int(x_min + (e_pct / 100.0) * line_width)
            px_right = int(x_min + (s_pct / 100.0) * line_width)
            pixel_polygons.append([[px_left, ly1], [px_right, ly1], [px_right, ly2], [px_left, ly2]])

            segments.append({
                "line": l + 1,
                "start_pct": round(s_pct, 3),
                "end_pct": round(e_pct, 3),
                "x_right_norm": round((px_right / W), 4),
                "x_left_norm": round((px_left / W), 4),
                "y_top_norm": round((ly1 / H), 4),
                "y_bottom_norm": round((ly2 / H), 4),
                "pixel_rect": [px_left, ly1, px_right, ly2]
            })

        # Match any Thumun marker situated within this verse span
        matched_thumuns = []
        for th in thumun_markers:
            if curr_line <= th["line"] <= m_line:
                if th["line"] == curr_line and th["cx"] > int(x_min + (curr_start_pct / 100.0) * line_width):
                    continue
                if th["line"] == m_line and th["cx"] < end_x:
                    continue
                matched_thumuns.append({
                    "cx": th["cx"],
                    "cy": th["cy"],
                    "w": th["w"],
                    "h": th["h"],
                    "cx_norm": round(th["cx"] / W, 4),
                    "cy_norm": round(th["cy"] / H, 4),
                    "line": th["line"] + 1,
                    "score": th["score"],
                    "inner_mean": th.get("inner_mean", 0.0),
                    "is_hollow": True
                })

        has_thumun = len(matched_thumuns) > 0

        if segments:
            svg_path = build_svg_path(pixel_polygons)
            normalized_svg_path = build_normalized_svg_path(pixel_polygons, W, H)

            ayahs.append({
                "ayah_index": len(ayahs) + 1,
                "start_line": segments[0]["line"],
                "end_line": segments[-1]["line"],
                "is_continuation_to_next_page": False,
                "has_thumun": has_thumun,
                "thumun_marker": matched_thumuns[0] if has_thumun else None,
                "compact_polygons": compact_array,
                "segments": segments,
                "pixel_polygons": pixel_polygons,
                "svg_path": svg_path,
                "normalized_svg_path": normalized_svg_path,
                "marker": {
                    "cx": m["cx"],
                    "cy": m["cy"],
                    "w": m["w"],
                    "h": m["h"],
                    "cx_norm": round(m["cx"] / W, 4),
                    "cy_norm": round(m["cy"] / H, 4),
                    "line": m["line"] + 1,
                    "score": m["score"],
                    "is_predicted": False,
                    "is_hollow": False,
                    "type": "ayah"
                }
            })

        # Line-end edge tolerance:
        # Wrap cleanly if remaining margin <= 5.0%, otherwise keep starting word at end_pct
        if end_pct < edge_tolerance_pct:
            curr_line = m_line + 1
            curr_start_pct = 100.0
        else:
            curr_line = m_line
            curr_start_pct = end_pct

        while curr_line < num_lines and curr_line in header_lines:
            curr_line += 1
            curr_start_pct = 100.0

    # Advance past headers at bottom of page
    while curr_line < num_lines and curr_line in header_lines:
        curr_line += 1
        curr_start_pct = 100.0

    # Predict end-of-page marker if line 15 was not completed cleanly
    is_page_already_finished = (curr_line >= num_lines) or (curr_line == num_lines - 1 and curr_start_pct <= edge_tolerance_pct)
    predicted_count = 0

    if ayah_markers and not is_page_already_finished:
        final_compact = []
        final_segments = []
        final_polygons = []
        for l in range(curr_line, num_lines):
            if l in header_lines:
                continue

            ly1 = int(y_min + l * line_height)
            ly2 = int(y_min + (l + 1) * line_height)
            s_pct = curr_start_pct if l == curr_line else 100.0
            e_pct = 0.0

            if s_pct - e_pct < MIN_SLICE_PCT:
                continue

            final_compact.append(build_compact_string(s_pct, e_pct))
            px_left = int(x_min + (e_pct / 100.0) * line_width)
            px_right = int(x_min + (s_pct / 100.0) * line_width)
            final_polygons.append([[px_left, ly1], [px_right, ly1], [px_right, ly2], [px_left, ly2]])
            final_segments.append({
                "line": l + 1,
                "start_pct": round(s_pct, 3),
                "end_pct": 0.0,
                "x_right_norm": round(px_right / W, 4),
                "x_left_norm": round(px_left / W, 4),
                "y_top_norm": round(ly1 / H, 4),
                "y_bottom_norm": round(ly2 / H, 4),
                "pixel_rect": [px_left, ly1, px_right, ly2]
            })

        matched_thumuns = []
        for th in thumun_markers:
            if curr_line <= th["line"] < num_lines:
                if th["line"] == curr_line and th["cx"] > int(x_min + (curr_start_pct / 100.0) * line_width):
                    continue
                matched_thumuns.append({
                    "cx": th["cx"],
                    "cy": th["cy"],
                    "w": th["w"],
                    "h": th["h"],
                    "cx_norm": round(th["cx"] / W, 4),
                    "cy_norm": round(th["cy"] / H, 4),
                    "line": th["line"] + 1,
                    "score": th["score"],
                    "inner_mean": th.get("inner_mean", 0.0),
                    "is_hollow": True
                })

        has_thumun = len(matched_thumuns) > 0

        if final_segments:
            pred_cx = x_min + 18
            pred_cy = int(y_min + (num_lines - 0.5) * line_height)
            predicted_marker = {
                "cx": pred_cx,
                "cy": pred_cy,
                "w": 35,
                "h": 37,
                "cx_norm": round(pred_cx / W, 4),
                "cy_norm": round(pred_cy / H, 4),
                "line": num_lines,
                "score": 0.0,
                "is_predicted": True,
                "is_hollow": False,
                "type": "ayah"
            }
            predicted_count = 1

            ayahs.append({
                "ayah_index": len(ayahs) + 1,
                "start_line": final_segments[0]["line"],
                "end_line": final_segments[-1]["line"],
                "is_continuation_to_next_page": False,
                "has_thumun": has_thumun,
                "thumun_marker": matched_thumuns[0] if has_thumun else None,
                "compact_polygons": final_compact,
                "segments": final_segments,
                "pixel_polygons": final_polygons,
                "svg_path": build_svg_path(final_polygons),
                "normalized_svg_path": build_normalized_svg_path(final_polygons, W, H),
                "marker": predicted_marker
            })

    # Page-level Thumun list
    page_thumuns = [{
        "cx": th["cx"],
        "cy": th["cy"],
        "w": th["w"],
        "h": th["h"],
        "cx_norm": round(th["cx"] / W, 4),
        "cy_norm": round(th["cy"] / H, 4),
        "line": th["line"] + 1,
        "score": th["score"],
        "inner_mean": th.get("inner_mean", 0.0),
        "is_hollow": True
    } for th in thumun_markers]

    return ayahs, page_thumuns, predicted_count
