"""
Core Pipeline Orchestration
Streams PDF pages in memory, coordinates detection, segmentation, and dataset packaging.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import argparse
import numpy as np
import cv2
import pymupdf
from tqdm import tqdm

from .config import (
    TARGET_WIDTH,
    TARGET_HEIGHT,
    NUM_LINES,
    CONTENT_BOUNDS_NORMALIZED,
    AYAH_MARKER_THRESHOLD,
    SURAH_HEADER_THRESHOLD,
    EDGE_TOLERANCE_PCT,
    resolve_asset_path,
)
from .detectors import (
    load_template,
    load_hollow_bitmask,
    load_header_templates,
    detect_surah_headers_full_page,
    detect_ayah_markers,
    classify_marker_hollow,
    group_overlapping_boxes,
)
from .segmenter import segment_ayahs_on_page
from .overlay import render_page_overlay


def process_opening_page(
    page_number: int,
    page_gray: np.ndarray,
    target_dimensions: Tuple[int, int] = (TARGET_WIDTH, TARGET_HEIGHT),
    edge_tolerance_pct: float = EDGE_TOLERANCE_PCT
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Special handler for ornamental opening pages 000 (Al-Fatihah) and 001 (Al-Baqarah)."""
    W, H = target_dimensions
    mask_file = f"{page_number:03d}_mask.png"
    mask_path = resolve_asset_path(mask_file)
    mask_bgr = cv2.imread(str(mask_path))
    if mask_bgr is None:
        raise FileNotFoundError(f"Opening mask file not found: {mask_path}")
    if (mask_bgr.shape[1], mask_bgr.shape[0]) != (W, H):
        mask_bgr = cv2.resize(mask_bgr, (W, H))

    # Green content bounding box
    g_mask = (mask_bgr[:, :, 1] > 180) & (mask_bgr[:, :, 2] < 80) & (mask_bgr[:, :, 0] < 80)
    ys, xs = np.where(g_mask)
    gx1, gx2 = int(xs.min()), int(xs.max())
    gy1, gy2 = int(ys.min()), int(ys.max())

    # Red surah header bounding box
    r_mask = (mask_bgr[:, :, 2] > 180) & (mask_bgr[:, :, 1] < 80) & (mask_bgr[:, :, 0] < 80)
    rys, rxs = np.where(r_mask)
    rx1, rx2 = int(rxs.min()), int(rxs.max())
    ry1, ry2 = int(rys.min()), int(rys.max())

    # Detect rosette markers in content crop
    crop = page_gray[gy1:gy2 + 1, gx1:gx2 + 1]
    rosette_path = resolve_asset_path("template_rosette_ring.png")
    rosette_ring = cv2.imread(str(rosette_path), cv2.IMREAD_GRAYSCALE)
    if rosette_ring is None:
        raise FileNotFoundError(f"Rosette ring template not found: {rosette_path}")
    th, tw = rosette_ring.shape

    res = cv2.matchTemplate(crop, rosette_ring, cv2.TM_CCOEFF_NORMED)
    locs = np.where(res >= 0.50)
    boxes = []
    for y, x in zip(*locs):
        boxes.append((int(x), int(y), int(x + tw), int(y + th), float(res[y, x])))
    nms_boxes = group_overlapping_boxes(boxes, overlap_thresh=0.3)

    content_h = gy2 - gy1 + 1
    num_opening_lines = 7
    line_h = content_h / float(num_opening_lines)

    markers = []
    for b in nms_boxes:
        px = gx1 + b[0]
        py = gy1 + b[1]
        cx = px + tw // 2
        cy = py + th // 2
        line_idx = int((py - gy1 + th // 2) / line_h)
        markers.append({
            "cx": cx,
            "cy": cy,
            "w": tw,
            "h": th,
            "x_left": px,
            "x_right": px + tw,
            "y_top": py,
            "y_bottom": py + th,
            "line": line_idx,
            "score": round(float(b[4]), 3),
            "is_predicted": False,
            "is_hollow": False,
            "type": "ayah"
        })

    # Sort markers: line asc, cx desc (RTL)
    markers.sort(key=lambda m: (m["line"], -m["cx"]))

    # Surah Header
    headers = [{
        "start_line": 0,
        "end_line": 0,
        "y_top": ry1,
        "y_bottom": ry2,
        "x_left": rx1,
        "x_right": rx2,
        "score": 1.0,
        "line_coverage_pct": 100.0,
        "has_basmala": (page_number == 1),
        "basmala_line": 1 if page_number == 1 else None,
        "label": "SURAH HEADER"
    }]

    # Basmalas:
    # Page 0 (Al-Fatihah): Basmala is counted as Ayah 1, so no separate Basmala banner.
    # Page 1 (Al-Baqarah): Has a separate Basmala on line 1 (index 0).
    basmalas = []
    if page_number == 1:
        by1 = gy1
        by2 = int(gy1 + line_h)
        bx1 = gx1
        bx2 = gx2
        basmalas.append({
            "line": 1,
            "y_top": by1,
            "y_bottom": by2,
            "x_left": bx1,
            "x_right": bx2,
            "y_top_norm": round(by1 / H, 4),
            "y_bottom_norm": round(by2 / H, 4),
            "x_left_norm": round(bx1 / W, 4),
            "x_right_norm": round(bx2 / W, 4),
            "pixel_rect": [bx1, by1, bx2, by2],
            "svg_path": f"M {bx1} {by1} L {bx2} {by1} L {bx2} {by2} L {bx1} {by2} Z",
            "normalized_svg_path": (
                f"M {round(bx1 / W, 4)} {round(by1 / H, 4)} "
                f"L {round(bx2 / W, 4)} {round(by1 / H, 4)} "
                f"L {round(bx2 / W, 4)} {round(by2 / H, 4)} "
                f"L {round(bx1 / W, 4)} {round(by2 / H, 4)} Z"
            ),
            "surah_header_lines": [0]
        })

    # Line exclusion for ayah segmentation:
    # On Page 1, line index 0 is Basmala so it's excluded from Ayah 1.
    # On Page 0, line index 0 is Ayah 1 (Basmala) so nothing is excluded.
    header_lines = {0} if page_number == 1 else set()

    ayahs, thumuns, pred_count = segment_ayahs_on_page(
        markers=markers,
        header_lines=header_lines,
        content_bounds=(gx1, gy1, gx2, gy2),
        page_dimensions=(W, H),
        num_lines=num_opening_lines,
        edge_tolerance_pct=edge_tolerance_pct
    )

    page_data = {
        "page_number": page_number,
        "dimensions": {"width": W, "height": H},
        "content_bounds": {
            "x_min": gx1,
            "y_min": gy1,
            "x_max": gx2,
            "y_max": gy2,
            "normalized": {
                "x_min": round(gx1 / W, 4),
                "y_min": round(gy1 / H, 4),
                "x_max": round(gx2 / W, 4),
                "y_max": round(gy2 / H, 4)
            }
        },
        "lines_count": num_opening_lines,
        "ayahs_count": len(ayahs),
        "thumun_count": 0,
        "thumun_markers": [],
        "markers_count": len(markers),
        "headers_count": len(headers),
        "headers": headers,
        "basmalas_count": len(basmalas),
        "basmalas": basmalas,
        "ayahs": ayahs
    }

    return page_data, markers, headers


def process_page_data(
    page_gray: np.ndarray,
    template_gray: np.ndarray,
    template_mask: np.ndarray,
    header_scales: List[Any],
    page_number: int,
    hollow_bitmask: Optional[np.ndarray] = None,
    hollow_inner_mask: Optional[np.ndarray] = None,
    num_lines: int = NUM_LINES,
    padding_bounds: Tuple[float, float, float, float] = CONTENT_BOUNDS_NORMALIZED,
    match_threshold: float = AYAH_MARKER_THRESHOLD,
    header_threshold: float = SURAH_HEADER_THRESHOLD,
    edge_tolerance_pct: float = EDGE_TOLERANCE_PCT
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Processes a single page grayscale array, detects headers & markers, and extracts ayahs."""
    H, W = page_gray.shape[:2]

    if page_number in (0, 1):
        return process_opening_page(page_number, page_gray, target_dimensions=(W, H), edge_tolerance_pct=edge_tolerance_pct)

    x_min = int(W * padding_bounds[0])
    y_min = int(H * padding_bounds[1])
    x_max = int(W * padding_bounds[2])
    y_max = int(H * padding_bounds[3])
    line_height = (y_max - y_min) / num_lines

    # 1. Full-page Surah Header Detection (unclipped by line margins)
    raw_headers = detect_surah_headers_full_page(
        page_gray,
        header_scales,
        y_min=y_min,
        line_height=line_height,
        num_lines=num_lines,
        threshold=header_threshold
    )

    # Exclude the very last decorative footer banner on Page 605 lines 14-15
    headers = [h for h in raw_headers if not (page_number == 605 and h["start_line"] >= 13)]

    header_lines = set()
    for hdr in headers:
        for hl in range(hdr["start_line"], hdr["end_line"] + 1):
            header_lines.add(hl)

    # Page 605 decorative bands and footer (lines 13-15 / indices 12, 13, 14)
    # must be excluded from verse text segmentation
    if page_number == 605:
        header_lines.add(12)
        header_lines.add(13)
        header_lines.add(14)

    # Basmala Detection:
    # Directly following each surah header (end_line + 1), except Surah At-Tawbah (Page 186)
    basmalas = []
    basmala_lines = set()

    for hdr in headers:
        # Surah At-Tawbah (Header #7 on Page 186) does not have a Basmala
        if page_number == 186:
            hdr["has_basmala"] = False
            continue

        b_line_0 = hdr["end_line"] + 1
        if b_line_0 < num_lines:
            hdr["has_basmala"] = True
            hdr["basmala_line"] = b_line_0 + 1  # 1-indexed
            basmala_lines.add(b_line_0)

            ly1 = int(y_min + b_line_0 * line_height)
            ly2 = int(y_min + (b_line_0 + 1) * line_height)
            px_left = x_min
            px_right = x_max
            svg_p = f"M {px_left} {ly1} L {px_right} {ly1} L {px_right} {ly2} L {px_left} {ly2} Z"
            norm_svg_p = f"M {px_left/W:.4f} {ly1/H:.4f} L {px_right/W:.4f} {ly1/H:.4f} L {px_right/W:.4f} {ly2/H:.4f} L {px_left/W:.4f} {ly2/H:.4f} Z"

            basmalas.append({
                "line": b_line_0 + 1,
                "y_top": ly1,
                "y_bottom": ly2,
                "x_left": px_left,
                "x_right": px_right,
                "y_top_norm": round(ly1 / H, 4),
                "y_bottom_norm": round(ly2 / H, 4),
                "x_left_norm": round(px_left / W, 4),
                "x_right_norm": round(px_right / W, 4),
                "pixel_rect": [px_left, ly1, px_right, ly2],
                "svg_path": svg_p,
                "normalized_svg_path": norm_svg_p,
                "surah_header_lines": [hdr["start_line"] + 1, hdr["end_line"] + 1]
            })
        else:
            hdr["has_basmala"] = False

    # Lines excluded from Ayah text segmentation (headers + basmalas)
    excluded_lines = header_lines | basmala_lines

    # 2. Detect Ayah markers inside the text box
    markers = detect_ayah_markers(
        page_gray,
        template_gray,
        template_mask,
        search_bounds=(x_min, y_min, x_max, y_max),
        threshold=match_threshold
    )

    # Assign each marker to its line and classify hollow Thumun markers
    for m in markers:
        line_idx = int((m["cy"] - y_min) / line_height)
        m["line"] = max(0, min(num_lines - 1, line_idx))

        is_hollow, inner_mean, inner_min = classify_marker_hollow(
            m, page_gray, hollow_bitmask, hollow_inner_mask
        )
        m["is_hollow"] = is_hollow
        m["inner_mean"] = inner_mean
        m["type"] = "thumun" if is_hollow else "ayah"

    # 2b. Check for manual/missing ayah markers defined via assets/{page_number:03d}_missing_ayah.png
    missing_mask_path = resolve_asset_path(f"{page_number:03d}_missing_ayah.png")
    if missing_mask_path.exists():
        missing_img = cv2.imread(str(missing_mask_path))
        if missing_img is not None:
            if (missing_img.shape[1], missing_img.shape[0]) != (W, H):
                missing_img = cv2.resize(missing_img, (W, H))
            is_black = (missing_img[:, :, 0] == 0) & (missing_img[:, :, 1] == 0) & (missing_img[:, :, 2] == 0)
            num_l, labels, stats, centroids = cv2.connectedComponentsWithStats(is_black.astype(np.uint8))
            for i in range(1, num_l):
                bx, by, bw, bh, barea = stats[i]
                if barea > 100 and bw >= 15 and bh >= 15:
                    bcx = int(centroids[i][0])
                    bcy = int(centroids[i][1])
                    bline_idx = int((bcy - y_min) / line_height)
                    bline_idx = max(0, min(num_lines - 1, bline_idx))
                    markers.append({
                        "cx": bcx,
                        "cy": bcy,
                        "w": int(bw),
                        "h": int(bh),
                        "x_left": int(bx),
                        "x_right": int(bx + bw),
                        "y_top": int(by),
                        "y_bottom": int(by + bh),
                        "line": bline_idx,
                        "score": 1.0,
                        "is_predicted": False,
                        "is_hollow": False,
                        "type": "ayah"
                    })

    # Sort top-to-bottom by line, then right-to-left
    markers.sort(key=lambda m: (m["line"], -m["cx"]))

    # 3. Build Ayah segments (excluding headers and basmalas)
    ayahs, page_thumuns, _ = segment_ayahs_on_page(
        markers=markers,
        header_lines=excluded_lines,
        content_bounds=(x_min, y_min, x_max, y_max),
        page_dimensions=(W, H),
        num_lines=num_lines,
        edge_tolerance_pct=edge_tolerance_pct
    )

    page_record = {
        "page_number": page_number,
        "dimensions": {
            "width": W,
            "height": H
        },
        "content_bounds": {
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max,
            "normalized": {
                "x_min": padding_bounds[0],
                "y_min": padding_bounds[1],
                "x_max": padding_bounds[2],
                "y_max": padding_bounds[3]
            }
        },
        "lines_count": num_lines,
        "ayahs_count": len(ayahs),
        "thumun_count": len(page_thumuns),
        "thumun_markers": page_thumuns,
        "markers_count": len(markers),
        "headers_count": len(headers),
        "headers": headers,
        "basmalas_count": len(basmalas),
        "basmalas": basmalas,
        "ayahs": ayahs
    }

    return page_record, markers, headers


def run_pipeline(
    pdf_path: str = "ALSHAZLY__ALGZAER__WARSH.pdf",
    template_path: str = "template_ring.png",
    hollow_bitmask_path: str = "template_ring_hollow_bitmask.png",
    header_template_path: str = "template_surah_header.png",
    output_dir: str = "output",
    start_page: int = 0,
    end_page: Optional[int] = None,
    target_width: int = TARGET_WIDTH,
    target_height: int = TARGET_HEIGHT,
    threshold: float = AYAH_MARKER_THRESHOLD,
    header_threshold: float = SURAH_HEADER_THRESHOLD,
    edge_tolerance_pct: float = EDGE_TOLERANCE_PCT,
    save_overlays: bool = False,
    overwrite: bool = True
) -> Dict[str, Any]:
    """Executes the full extraction pipeline across the specified page range."""
    out_dir = Path(output_dir)
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    if save_overlays:
        overlays_dir = out_dir / "overlays"
        overlays_dir.mkdir(parents=True, exist_ok=True)

    tmpl_gray, mask = load_template(template_path)
    hollow_bm, hollow_inner_mask = load_hollow_bitmask(hollow_bitmask_path)
    header_scales = load_header_templates(header_template_path)

    print(f"Opening PDF: {pdf_path}...")
    doc = pymupdf.open(pdf_path)
    total_doc_pages = len(doc)
    print(f"PDF contains {total_doc_pages} pages.")

    if end_page is None or end_page < 0:
        end_page = total_doc_pages

    start_page = max(0, start_page)
    end_page = min(total_doc_pages, end_page)
    pages_to_process = list(range(start_page, end_page))
    print(f"Processing {len(pages_to_process)} pages (indices {start_page} to {end_page - 1})...")

    all_pages_data = {}
    stats = {
        "processed_pages": 0,
        "pages_with_markers": 0,
        "empty_pages": 0,
        "total_headers_detected": 0,
        "total_basmalas_detected": 0,
        "total_markers_detected": 0,
        "total_thumun_markers": 0,
        "total_predicted_markers": 0,
        "total_ayahs_extracted": 0
    }

    for p in tqdm(pages_to_process, desc="Extracting Ayah Masks"):
        page_file = pages_dir / f"{p:03d}.json"
        if not overwrite and page_file.exists():
            with open(page_file, "r", encoding="utf-8") as f:
                page_data = json.load(f)
            all_pages_data[str(p)] = page_data
            stats["processed_pages"] += 1
            stats["total_headers_detected"] += page_data.get("headers_count", 0)
            stats["total_basmalas_detected"] += page_data.get("basmalas_count", 0)
            stats["total_thumun_markers"] += page_data.get("thumun_count", 0)
            if page_data["markers_count"] > 0:
                stats["pages_with_markers"] += 1
                stats["total_markers_detected"] += page_data["markers_count"]
                stats["total_ayahs_extracted"] += page_data["ayahs_count"]
            else:
                stats["empty_pages"] += 1
            continue

        page = doc[p]
        scale_x = target_width / page.rect.width
        scale_y = target_height / page.rect.height
        mat = pymupdf.Matrix(scale_x, scale_y)

        pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csGRAY)
        gray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w)

        page_data, markers, headers = process_page_data(
            gray,
            tmpl_gray,
            mask,
            header_scales,
            page_number=p,
            hollow_bitmask=hollow_bm,
            hollow_inner_mask=hollow_inner_mask,
            num_lines=NUM_LINES,
            padding_bounds=CONTENT_BOUNDS_NORMALIZED,
            match_threshold=threshold,
            header_threshold=header_threshold,
            edge_tolerance_pct=edge_tolerance_pct
        )

        with open(page_file, "w", encoding="utf-8") as f:
            json.dump(page_data, f, ensure_ascii=False, indent=2)

        all_pages_data[str(p)] = page_data
        stats["processed_pages"] += 1
        stats["total_headers_detected"] += len(headers)
        stats["total_basmalas_detected"] += page_data.get("basmalas_count", 0)
        stats["total_thumun_markers"] += page_data.get("thumun_count", 0)
        if len(markers) > 0:
            stats["pages_with_markers"] += 1
            stats["total_markers_detected"] += len(markers)
            stats["total_ayahs_extracted"] += page_data["ayahs_count"]
            pred_count = sum(1 for a in page_data["ayahs"] if a.get("marker", {}).get("is_predicted", False))
            stats["total_predicted_markers"] += pred_count
        else:
            stats["empty_pages"] += 1

        if save_overlays and (len(markers) > 0 or len(headers) > 0 or page_data.get("basmalas_count", 0) > 0):
            pix_rgb = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
            img_bgr = np.frombuffer(pix_rgb.samples, dtype=np.uint8).reshape(pix_rgb.h, pix_rgb.w, 3)[:, :, ::-1]
            render_page_overlay(img_bgr, page_data, overlays_dir / f"{p:03d}.jpg")

    # Always assemble consolidated dataset from all available page JSONs
    full_pages_data = {}
    full_stats = {
        "processed_pages": 0,
        "pages_with_markers": 0,
        "empty_pages": 0,
        "total_headers_detected": 0,
        "total_basmalas_detected": 0,
        "total_markers_detected": 0,
        "total_thumun_markers": 0,
        "total_predicted_markers": 0,
        "total_ayahs_extracted": 0
    }
    for p_idx in range(total_doc_pages):
        pf = pages_dir / f"{p_idx:03d}.json"
        pdata = None
        if str(p_idx) in all_pages_data:
            pdata = all_pages_data[str(p_idx)]
        elif pf.exists():
            with open(pf, "r", encoding="utf-8") as f:
                pdata = json.load(f)

        if pdata is not None:
            full_pages_data[str(p_idx)] = pdata
            full_stats["processed_pages"] += 1
            full_stats["total_headers_detected"] += pdata.get("headers_count", 0)
            full_stats["total_basmalas_detected"] += pdata.get("basmalas_count", 0)
            full_stats["total_thumun_markers"] += pdata.get("thumun_count", 0)
            if pdata.get("markers_count", 0) > 0:
                full_stats["pages_with_markers"] += 1
                full_stats["total_markers_detected"] += pdata["markers_count"]
                full_stats["total_ayahs_extracted"] += pdata["ayahs_count"]
                full_stats["total_predicted_markers"] += sum(1 for a in pdata.get("ayahs", []) if a.get("marker", {}).get("is_predicted", False))
            else:
                full_stats["empty_pages"] += 1

    consolidated_path = out_dir / "mushaf_ayah_masks.json"
    with open(consolidated_path, "w", encoding="utf-8") as f:
        json.dump({
            "version": "1.5.0",
            "mushaf": "Al-Shazly Warsh (Algeria)",
            "total_pages": len(full_pages_data),
            "stats": full_stats,
            "pages": full_pages_data
        }, f, ensure_ascii=False, indent=2)

    print("\n================ Processing Summary ================")
    print(f"Total Pages in Dataset         : {full_stats['processed_pages']}")
    print(f"Pages with Ayahs               : {full_stats['pages_with_markers']}")
    print(f"Empty/Cover Pages              : {full_stats['empty_pages']}")
    print(f"Total Surah Headers Found      : {full_stats['total_headers_detected']}")
    print(f"Total Basmalas Labeled         : {full_stats['total_basmalas_detected']}")
    print(f"Total Physical Markers Detected: {full_stats['total_markers_detected']}")
    print(f"Total Hollow Thumun Markers    : {full_stats['total_thumun_markers']}")
    print(f"Predicted End-of-Page Markers  : {full_stats['total_predicted_markers']}")
    print(f"Total Completed Ayahs          : {full_stats['total_ayahs_extracted']}")
    print(f"Per-page JSON directory        : {pages_dir.resolve()}")
    print(f"Consolidated JSON file         : {consolidated_path.resolve()}")
    print("====================================================")

    return full_stats


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Extract Ayah masks from Mushaf PDF")
    parser.add_argument("--pdf", default="ALSHAZLY__ALGZAER__WARSH.pdf", help="Path to PDF")
    parser.add_argument("--template", default="template_ring.png", help="Path to ring template")
    parser.add_argument("--hollow-bitmask", default="template_ring_hollow_bitmask.png", help="Path to hollow bitmask")
    parser.add_argument("--header-template", default="template_surah_header.png", help="Path to surah header template")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--start", type=int, default=0, help="Start page index (0-based)")
    parser.add_argument("--end", type=int, default=-1, help="End page index (-1 for all)")
    parser.add_argument("--threshold", type=float, default=AYAH_MARKER_THRESHOLD, help="Ayah marker threshold")
    parser.add_argument("--header-threshold", type=float, default=SURAH_HEADER_THRESHOLD, help="Surah header threshold")
    parser.add_argument("--edge-tolerance", type=float, default=EDGE_TOLERANCE_PCT, help="Line-end edge tolerance percentage")
    parser.add_argument("--save-overlays", action="store_true", help="Save visual overlays")
    parser.add_argument("--no-overwrite", action="store_true", help="Skip already processed pages")

    args = parser.parse_args()
    run_pipeline(
        pdf_path=args.pdf,
        template_path=args.template,
        hollow_bitmask_path=args.hollow_bitmask,
        header_template_path=args.header_template,
        output_dir=args.output,
        start_page=args.start,
        end_page=None if args.end == -1 else args.end,
        threshold=args.threshold,
        header_threshold=args.header_threshold,
        edge_tolerance_pct=args.edge_tolerance,
        save_overlays=args.save_overlays,
        overwrite=not args.no_overwrite
    )


if __name__ == "__main__":
    main()
