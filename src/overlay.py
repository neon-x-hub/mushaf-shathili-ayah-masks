"""
Visual Overlay Generator
Renders colored verse segment polygons, surah headers, Thumun markers, and ayah rings.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import cv2
import pymupdf
from tqdm import tqdm

from .config import TARGET_WIDTH, TARGET_HEIGHT


PASTEL_COLORS = [
    (255, 100, 100),  # Blue
    (100, 200, 100),  # Green
    (100, 100, 255),  # Red
    (200, 180, 50),   # Cyan
    (180, 50, 200),   # Magenta
    (50, 200, 200),   # Yellow
    (220, 120, 50)    # Sky
]


def render_page_overlay(img_bgr: np.ndarray, page_data: Dict[str, Any], output_path: Path, quality: int = 85) -> None:
    """Draws visual verification overlay on the page image."""
    H, W = img_bgr.shape[:2]
    data_dims = page_data.get("dimensions", {})
    data_w = data_dims.get("width", W)
    data_h = data_dims.get("height", H)
    sx = W / float(data_w) if data_w and data_w > 0 else 1.0
    sy = H / float(data_h) if data_h and data_h > 0 else 1.0

    vis_img = img_bgr.copy()
    overlay = vis_img.copy()

    ayahs = page_data.get("ayahs", [])
    for idx, ayah in enumerate(ayahs):
        color = PASTEL_COLORS[idx % len(PASTEL_COLORS)]
        for poly in ayah.get("pixel_polygons", []):
            if sx != 1.0 or sy != 1.0:
                scaled_poly = [[int(round(p[0] * sx)), int(round(p[1] * sy))] for p in poly]
            else:
                scaled_poly = poly
            pts = np.array(scaled_poly, np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [pts], color)
            cv2.polylines(vis_img, [pts], True, color, 2)

    # 25% overlay opacity
    cv2.addWeighted(overlay, 0.25, vis_img, 0.75, 0, vis_img)

    # Draw content boundary in blue
    cb = page_data.get("content_bounds", {})
    if "x_min" in cb:
        x_min = int(round(cb["x_min"] * sx))
        y_min = int(round(cb["y_min"] * sy))
        x_max = int(round(cb["x_max"] * sx))
        y_max = int(round(cb["y_max"] * sy))
        cv2.rectangle(
            vis_img,
            (x_min, y_min),
            (x_max, y_max),
            (255, 0, 0),
            1
        )

    # Draw Surah Headers in gold/orange box
    headers = page_data.get("headers", [])
    for hdr in headers:
        hdr_lbl = hdr.get("label") or f"SURAH HEADER (Lines {hdr['start_line']+1}-{hdr['end_line']+1})"
        hx_left = int(round(hdr.get("x_left", cb.get("x_min", 46)) * sx))
        hx_right = int(round(hdr.get("x_right", cb.get("x_max", 1442)) * sx))
        hy_top = int(round(hdr["y_top"] * sy))
        hy_bottom = int(round(hdr["y_bottom"] * sy))
        cv2.rectangle(
            vis_img,
            (hx_left, hy_top),
            (hx_right, hy_bottom),
            (0, 165, 255),
            2
        )
        cv2.putText(
            vis_img,
            hdr_lbl,
            (hx_left + 15, hy_top + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 165, 255),
            2,
            cv2.LINE_AA
        )

    # Draw Basmalas in Emerald Green box with green tint
    basmalas = page_data.get("basmalas", [])
    for b in basmalas:
        px_left = int(round(b.get("x_left", cb.get("x_min", 46)) * sx))
        px_right = int(round(b.get("x_right", cb.get("x_max", 1442)) * sx))
        y_top = int(round(b.get("y_top", 0) * sy))
        y_bottom = int(round(b.get("y_bottom", 0) * sy))
        cv2.rectangle(overlay, (px_left, y_top), (px_right, y_bottom), (60, 200, 100), -1)
        cv2.rectangle(vis_img, (px_left, y_top), (px_right, y_bottom), (40, 180, 80), 2)
        cv2.putText(
            vis_img,
            f"BASMALA (Line {b['line']})",
            (px_left + 25, y_top + int((y_bottom - y_top) * 0.65)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (40, 180, 80),
            2,
            cv2.LINE_AA
        )

    # Draw Thumun markers in Cyan box with centered label 'TH'
    for th in page_data.get("thumun_markers", []):
        tcx = int(round(th["cx"] * sx))
        tcy = int(round(th["cy"] * sy))
        tw_box = int(round(th.get("w", 71) * sx))
        th_box = int(round(th.get("h", 72) * sy))
        half_w = tw_box // 2
        half_h = th_box // 2
        cv2.rectangle(
            vis_img,
            (tcx - half_w, tcy - half_h),
            (tcx + half_w, tcy + half_h),
            (255, 200, 0),  # Cyan in BGR
            2
        )
        (tw, th_txt), _ = cv2.getTextSize("TH", cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.putText(
            vis_img,
            "TH",
            (tcx - tw // 2, tcy + th_txt // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 200, 0),
            2,
            cv2.LINE_AA
        )

    # Draw markers in Red (or Magenta for predicted) with centered Ayah index
    for ayah in ayahs:
        m = ayah.get("marker")
        if m:
            is_pred = m.get("is_predicted", False)
            color = (255, 0, 255) if is_pred else (0, 0, 255)
            mcx = int(round(m["cx"] * sx))
            mcy = int(round(m["cy"] * sy))
            mw = int(round(m["w"] * sx))
            mh = int(round(m["h"] * sy))
            half_w = mw // 2
            half_h = mh // 2
            cv2.rectangle(
                vis_img,
                (mcx - half_w, mcy - half_h),
                (mcx + half_w, mcy + half_h),
                color,
                2
            )
            lbl = f"P{ayah['ayah_index']}" if is_pred else str(ayah["ayah_index"])
            (tw, th_txt), _ = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.putText(
                vis_img,
                lbl,
                (mcx - tw // 2, mcy + th_txt // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
                cv2.LINE_AA
            )

    cv2.imwrite(str(output_path), vis_img, [cv2.IMWRITE_JPEG_QUALITY, quality])


def generate_all_overlays(
    pdf_path: str = "Mushaf-Ashathili.pdf",
    pages_dir: str = "output/pages",
    output_dir: str = "output/overlays",
    target_width: int = TARGET_WIDTH,
    target_height: int = TARGET_HEIGHT,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    page_number: Optional[int] = None,
    overwrite: bool = True,
    quality: int = 85
) -> int:
    """Batch generates visual verification JPEG overlays for Mushaf pages."""
    import json
    pages_path = Path(pages_dir)
    overlays_path = Path(output_dir)
    overlays_path.mkdir(parents=True, exist_ok=True)

    print(f"Opening PDF: {pdf_path}...")
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    print(f"Found {total_pages} pages in PDF.")

    if page_number is not None:
        target_indices = [page_number]
    else:
        s = 0 if start_page is None else max(0, start_page)
        e = total_pages if end_page is None or end_page < 0 else min(total_pages, end_page)
        target_indices = list(range(s, e))

    rendered_count = 0
    for p_num in tqdm(target_indices, desc="Rendering Overlays"):
        if p_num >= total_pages:
            continue

        out_file = overlays_path / f"{p_num:03d}.jpg"
        if not overwrite and out_file.exists():
            continue

        jf = pages_path / f"{p_num:03d}.json"
        if not jf.exists():
            continue

        with open(jf, "r", encoding="utf-8") as f:
            page_data = json.load(f)

        page = doc[p_num]
        scale_x = target_width / page.rect.width
        scale_y = target_height / page.rect.height
        mat = pymupdf.Matrix(scale_x, scale_y)

        pix_rgb = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
        img_bgr = np.frombuffer(pix_rgb.samples, dtype=np.uint8).reshape(pix_rgb.h, pix_rgb.w, 3)[:, :, ::-1]

        render_page_overlay(img_bgr, page_data, out_file, quality=quality)
        rendered_count += 1

    print("\n--- Overlay Generation Complete ---")
    print(f"Total overlays saved: {rendered_count}")
    print(f"Saved directory      : {overlays_path.resolve()}")
    return rendered_count
