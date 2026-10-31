"""
Visual Overlay Generator
Renders colored verse segment polygons, surah headers, Thumun markers, and ayah rings.
"""

from pathlib import Path
from typing import Dict, Any, List
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


def render_page_overlay(img_bgr: np.ndarray, page_data: Dict[str, Any], output_path: Path) -> None:
    """Draws visual verification overlay on the page image."""
    vis_img = img_bgr.copy()
    overlay = vis_img.copy()

    ayahs = page_data.get("ayahs", [])
    for idx, ayah in enumerate(ayahs):
        color = PASTEL_COLORS[idx % len(PASTEL_COLORS)]
        for poly in ayah.get("pixel_polygons", []):
            pts = np.array(poly, np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [pts], color)
            cv2.polylines(vis_img, [pts], True, color, 1)

    # 25% overlay opacity
    cv2.addWeighted(overlay, 0.25, vis_img, 0.75, 0, vis_img)

    # Draw content boundary in blue
    cb = page_data.get("content_bounds", {})
    if "x_min" in cb:
        cv2.rectangle(
            vis_img,
            (cb["x_min"], cb["y_min"]),
            (cb["x_max"], cb["y_max"]),
            (255, 0, 0),
            1
        )

    # Draw Surah Headers in gold/orange box
    headers = page_data.get("headers", [])
    for hdr in headers:
        hdr_lbl = hdr.get("label") or f"SURAH HEADER (Lines {hdr['start_line']+1}-{hdr['end_line']+1})"
        cv2.rectangle(
            vis_img,
            (hdr.get("x_left", cb.get("x_min", 40)), hdr["y_top"]),
            (hdr.get("x_right", cb.get("x_max", 580)), hdr["y_bottom"]),
            (0, 165, 255),
            2
        )
        cv2.putText(
            vis_img,
            hdr_lbl,
            (hdr.get("x_left", cb.get("x_min", 40)) + 10, hdr["y_top"] + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 165, 255),
            1,
            cv2.LINE_AA
        )

    # Draw Basmalas in Emerald Green box with green tint
    basmalas = page_data.get("basmalas", [])
    for b in basmalas:
        px_left = b.get("x_left", cb.get("x_min", 31))
        px_right = b.get("x_right", cb.get("x_max", 591))
        y_top = b.get("y_top", 0)
        y_bottom = b.get("y_bottom", 0)
        cv2.rectangle(overlay, (px_left, y_top), (px_right, y_bottom), (60, 200, 100), -1)
        cv2.rectangle(vis_img, (px_left, y_top), (px_right, y_bottom), (40, 180, 80), 2)
        cv2.putText(
            vis_img,
            f"BASMALA (Line {b['line']})",
            (px_left + 15, y_top + int((y_bottom - y_top) * 0.65)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (40, 180, 80),
            1,
            cv2.LINE_AA
        )

    # Draw Thumun markers in Cyan box with label 'TH'
    for th in page_data.get("thumun_markers", []):
        half_w = th.get("w", 35) // 2
        half_h = th.get("h", 37) // 2
        cv2.rectangle(
            vis_img,
            (th["cx"] - half_w, th["cy"] - half_h),
            (th["cx"] + half_w, th["cy"] + half_h),
            (255, 200, 0),  # Cyan in BGR
            2
        )
        cv2.putText(
            vis_img,
            "TH",
            (th["cx"] - 8, th["cy"] + 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (255, 200, 0),
            1,
            cv2.LINE_AA
        )

    # Draw markers in Red (or Magenta for predicted)
    for ayah in ayahs:
        m = ayah.get("marker")
        if m:
            is_pred = m.get("is_predicted", False)
            color = (255, 0, 255) if is_pred else (0, 0, 255)
            half_w = m["w"] // 2
            half_h = m["h"] // 2
            cv2.rectangle(
                vis_img,
                (m["cx"] - half_w, m["cy"] - half_h),
                (m["cx"] + half_w, m["cy"] + half_h),
                color,
                2
            )
            lbl = f"P{ayah['ayah_index']}" if is_pred else str(ayah["ayah_index"])
            cv2.putText(
                vis_img,
                lbl,
                (m["cx"] - 6, m["cy"] + 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                color,
                1,
                cv2.LINE_AA
            )

    cv2.imwrite(str(output_path), vis_img, [cv2.IMWRITE_JPEG_QUALITY, 85])


def generate_all_overlays(
    pdf_path: str = "ALSHAZLY__ALGZAER__WARSH.pdf",
    pages_dir: str = "output/pages",
    output_dir: str = "output/overlays",
    target_width: int = TARGET_WIDTH,
    target_height: int = TARGET_HEIGHT
) -> int:
    """Batch generates visual verification JPEG overlays for all pages."""
    import json
    pages_path = Path(pages_dir)
    overlays_path = Path(output_dir)
    overlays_path.mkdir(parents=True, exist_ok=True)

    print(f"Opening PDF: {pdf_path}...")
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    print(f"Found {total_pages} pages in PDF.")

    json_files = sorted(list(pages_path.glob("*.json")))
    print(f"Found {len(json_files)} page JSON files in {pages_path}.")

    rendered_count = 0
    for jf in tqdm(json_files, desc="Rendering Overlays"):
        p_num = int(jf.stem)
        if p_num >= total_pages:
            continue

        with open(jf, "r", encoding="utf-8") as f:
            page_data = json.load(f)

        page = doc[p_num]
        scale_x = target_width / page.rect.width
        scale_y = target_height / page.rect.height
        mat = pymupdf.Matrix(scale_x, scale_y)

        pix_rgb = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
        img_bgr = np.frombuffer(pix_rgb.samples, dtype=np.uint8).reshape(pix_rgb.h, pix_rgb.w, 3)[:, :, ::-1]

        out_file = overlays_path / f"{p_num:03d}.jpg"
        render_page_overlay(img_bgr, page_data, out_file)
        rendered_count += 1

    print("\n--- Overlay Generation Complete ---")
    print(f"Total overlays saved: {rendered_count}")
    print(f"Saved directory      : {overlays_path.resolve()}")
    return rendered_count
