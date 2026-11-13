"""
Detectors for Ayah Markers, Surah Headers, and Hollow Thumun Symbols
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import cv2

from .config import (
    NMS_OVERLAP_THRESHOLD,
    AYAH_MARKER_THRESHOLD,
    SURAH_HEADER_THRESHOLD,
    HOLLOW_MEAN_MIN,
    HOLLOW_MIN_PIXEL,
    HOLLOW_DARK_THRESHOLD,
    resolve_asset_path,
)


def group_overlapping_boxes(boxes: List[Any], overlap_thresh: float = NMS_OVERLAP_THRESHOLD) -> List[Tuple[int, int, int, int, float]]:
    """Non-Maximum Suppression (NMS) sorted by highest correlation score."""
    if len(boxes) == 0:
        return []
    b_arr = np.array(boxes, dtype="float")
    pick = []
    x1, y1, x2, y2, scores = b_arr[:, 0], b_arr[:, 1], b_arr[:, 2], b_arr[:, 3], b_arr[:, 4]
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(scores)

    while len(idxs) > 0:
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)
        overlap = (w * h) / np.minimum(area[i], area[idxs[:last]])
        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlap_thresh)[0])))

    picked_boxes = []
    for idx in pick:
        picked_boxes.append((
            int(b_arr[idx, 0]),
            int(b_arr[idx, 1]),
            int(b_arr[idx, 2]),
            int(b_arr[idx, 3]),
            float(b_arr[idx, 4])
        ))
    return picked_boxes


def load_template(template_path: str = "template_ring.png") -> Tuple[np.ndarray, np.ndarray]:
    """Loads ayah ring template and builds annular mask."""
    path = resolve_asset_path(template_path)
    tmpl = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if tmpl is None:
        raise FileNotFoundError(f"Could not load marker template at {path}")

    if len(tmpl.shape) == 3 and tmpl.shape[2] == 4:
        template_gray = cv2.cvtColor(tmpl[:, :, :3], cv2.COLOR_BGR2GRAY)
        mask = tmpl[:, :, 3]
    else:
        template_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY) if len(tmpl.shape) == 3 else tmpl
        h, w = template_gray.shape
        mask = np.zeros((h, w), dtype=np.uint8)
        center = (w // 2, h // 2)
        cv2.circle(mask, center, int(min(w, h) * 0.48), 255, -1)
        cv2.circle(mask, center, int(min(w, h) * 0.24), 0, -1)

    return template_gray, mask


def load_hollow_bitmask(bitmask_path: str = "template_ring_hollow_bitmask.png") -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Loads hollow ring bitmask used to detect unnumbered Thumun markers."""
    path = resolve_asset_path(bitmask_path)
    bm = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if bm is None:
        return None, None
    return bm, (bm < 128)


def load_header_templates(header_template_path: str = "template_surah_header.png") -> List[Tuple[int, int, np.ndarray, np.ndarray]]:
    """Loads surah header template and pre-computes multi-scale variants."""
    path = resolve_asset_path(header_template_path)
    tmpl = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if tmpl is None:
        return []

    if len(tmpl.shape) == 3 and tmpl.shape[2] == 4:
        tmpl_gray = cv2.cvtColor(tmpl[:, :, :3], cv2.COLOR_BGR2GRAY)
        mask = tmpl[:, :, 3]
    else:
        tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY) if len(tmpl.shape) == 3 else tmpl
        mask = np.ones(tmpl_gray.shape, dtype=np.uint8) * 255

    scales = []
    # Multi-scale coverage (1354 to 1366 px width) for 1488x2207 scan
    aspect = tmpl_gray.shape[0] / float(tmpl_gray.shape[1])
    for tw in [1354, 1360, 1366]:
        th = int(round(tw * aspect))
        t_res = cv2.resize(tmpl_gray, (tw, th))
        m_res = cv2.resize(mask, (tw, th))
        scales.append((tw, th, t_res, m_res))

    return scales


def assign_two_lines_by_overlap(
    y_top: int,
    y_bottom: int,
    y_min: int,
    line_height: float,
    num_lines: int = 15
) -> Tuple[int, int, float]:
    """Assigns a detected header bounding box to the two lines with maximum vertical intersection."""
    best_l = 0
    best_overlap = -1.0
    for l in range(num_lines - 1):
        l_top = y_min + l * line_height
        l_bottom = y_min + (l + 2) * line_height
        overlap = max(0.0, min(float(y_bottom), l_bottom) - max(float(y_top), l_top))
        if overlap > best_overlap:
            best_overlap = overlap
            best_l = l

    hdr_h = max(1.0, float(y_bottom - y_top))
    coverage_pct = round((best_overlap / hdr_h) * 100.0, 1)
    return best_l, best_l + 1, coverage_pct


def detect_surah_headers_full_page(
    page_gray: np.ndarray,
    header_scales: List[Tuple[int, int, np.ndarray, np.ndarray]],
    y_min: int,
    line_height: float,
    num_lines: int = 15,
    threshold: float = SURAH_HEADER_THRESHOLD
) -> List[Dict[str, Any]]:
    """Detects surah headers across the entire page without hard margin clipping."""
    if not header_scales:
        return []

    all_boxes = []
    for tw, th, t_res, m_res in header_scales:
        res = cv2.matchTemplate(page_gray, t_res, cv2.TM_CCOEFF_NORMED, mask=m_res)
        res = np.nan_to_num(res, nan=0.0)
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            score = float(res[pt[1], pt[0]])
            all_boxes.append([pt[0], pt[1], pt[0] + tw, pt[1] + th, score])

    if not all_boxes:
        return []

    # Non-maximum suppression across scales
    all_boxes = np.array(all_boxes)
    idxs = np.argsort(all_boxes[:, 4])
    pick = []
    suppress_dist = max(55.0, line_height * 0.75)
    while len(idxs) > 0:
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)
        idxs = np.delete(idxs, [last])
        new_idxs = []
        for idx in idxs:
            if abs(all_boxes[idx, 1] - all_boxes[i, 1]) > suppress_dist:
                new_idxs.append(idx)
        idxs = np.array(new_idxs)

    headers = []
    for i in pick:
        bx1, by1, bx2, by2, score = all_boxes[i]
        start_line, end_line, cov_pct = assign_two_lines_by_overlap(
            int(by1), int(by2), y_min, line_height, num_lines=num_lines
        )
        headers.append({
            "start_line": start_line,
            "end_line": end_line,
            "y_top": int(by1),
            "y_bottom": int(by2),
            "x_left": int(bx1),
            "x_right": int(bx2),
            "score": round(float(score), 3),
            "line_coverage_pct": cov_pct
        })

    headers.sort(key=lambda h: h["start_line"])
    return headers


def detect_ayah_markers(
    page_gray: np.ndarray,
    template_gray: np.ndarray,
    mask: np.ndarray,
    search_bounds: Tuple[int, int, int, int],
    threshold: float = AYAH_MARKER_THRESHOLD
) -> List[Dict[str, Any]]:
    """Detects Ayah markers using zero-mean normalized cross-correlation."""
    x_min, y_min, x_max, y_max = search_bounds
    th, tw = template_gray.shape

    roi_gray = page_gray[y_min:y_max, x_min:x_max]
    result = cv2.matchTemplate(roi_gray, template_gray, cv2.TM_CCOEFF_NORMED, mask=mask)
    result = np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)

    loc = np.where(result >= threshold)
    raw_boxes = []
    for pt in zip(*loc[::-1]):
        score = float(result[pt[1], pt[0]])
        px1, py1 = pt[0] + x_min, pt[1] + y_min
        patch = roi_gray[pt[1]:pt[1] + th, pt[0]:pt[0] + tw]
        ring_pixels = patch[mask > 0]
        if np.std(ring_pixels) < 25:
            continue
        raw_boxes.append([px1, py1, px1 + tw, py1 + th, score])

    nms_boxes = group_overlapping_boxes(raw_boxes, overlap_thresh=NMS_OVERLAP_THRESHOLD)

    markers = []
    for (x1, y1, x2, y2, score) in nms_boxes:
        markers.append({
            "x_left": int(x1),
            "x_right": int(x2),
            "cx": int((x1 + x2) / 2),
            "cy": int((y1 + y2) / 2),
            "w": int(x2 - x1),
            "h": int(y2 - y1),
            "score": round(float(score), 4)
        })
    return markers


def classify_marker_hollow(
    marker: Dict[str, Any],
    page_gray: np.ndarray,
    hollow_bitmask: Optional[np.ndarray],
    hollow_inner_mask: Optional[np.ndarray]
) -> Tuple[bool, float, int]:
    """Tests if a detected marker patch has empty center (hollow Thumun marker)."""
    if hollow_bitmask is None or hollow_inner_mask is None:
        return False, 0.0, 0

    H, W = page_gray.shape[:2]
    half_w = marker["w"] // 2
    half_h = marker["h"] // 2
    py1 = max(0, marker["cy"] - half_h)
    py2 = min(H, marker["cy"] + (marker["h"] - half_h))
    px1 = max(0, marker["cx"] - half_w)
    px2 = min(W, marker["cx"] + (marker["w"] - half_w))

    crop = page_gray[py1:py2, px1:px2]
    if crop.shape != hollow_bitmask.shape:
        crop = cv2.resize(crop, (hollow_bitmask.shape[1], hollow_bitmask.shape[0]))

    inner_pixels = crop[hollow_inner_mask]
    inner_mean = float(inner_pixels.mean())
    inner_min = int(inner_pixels.min())
    dark_cnt = int(np.sum(inner_pixels < HOLLOW_DARK_THRESHOLD))

    is_hollow = bool(
        inner_mean >= HOLLOW_MEAN_MIN and
        dark_cnt == 0 and
        inner_min >= HOLLOW_MIN_PIXEL
    )
    return is_hollow, round(inner_mean, 2), inner_min
