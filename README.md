# Al-Shazly Warsh Mushaf: Ayah Masks & Coordinates Dataset | مصحف الشاذلي برواية ورش: إحداثيات ومحددات الآيات القرآنية

High-precision bounding polygons, line segments, verse markers, and ready-to-render SVG paths for every Ayah in the **Al-Shazly Warsh Mushaf** (Algeria edition, 15 lines/page).

Designed for frictionless integration into Quran mobile apps (**Flutter**, **Android/Kotlin**, **iOS/Swift**) and web apps (**React**, **Vue**, **SVG/Canvas**).

> **Source Mushaf:** The original PDF scan is hosted on the Internet Archive:  
> 🔗 **[Internet Archive: مصحف الشاذلي الجزائري برواية ورش عن نافع](https://archive.org/details/ALSHTTTTTTTTTTTTTTTTTTTTTARSH/mode/2up)**

---

## Dataset Highlights

- **606 Total PDF Pages** processed with streaming PyMuPDF rendering (all 606 pages with active verses).
- **114 Surah Header Banners** automatically detected across lines and cleanly excluded from verse masks (Surahs 1–114, excluding the closing footer on Page 605).
- **112 Basmala Lines** identified directly beneath headers (excluding Surah At-Tawbah on Page 186, and Surah Al-Fatihah on Page 000 where Basmala is counted as Ayah 1) and isolated from verse masks so Ayah 1 of each Surah contains only genuine verse text.
- **13 Hollow Thumun (1/8 Hizb) Markers** identified and merged into their true parent Quranic verses, providing complete verse highlighting while exposing exact Thumun coordinates.
- **6,236 Total Completed Verses** across all 606 pages, perfectly matching the canonical Kufi count across all 114 Surahs with 100.0% verification.
- **Dedicated Handlers for Opening Pages 000 & 001**: Special 7-line content framing, ornamental header detection, and rosette ring matching using assets/000_mask.png and assets/001_mask.png.
- **Resolution-Independent**: Stored both in original page coordinates and normalized ($0.0 \dots 1.0$) coordinates.
- **Ready-to-Render SVG**: Every verse contains pre-computed SVG path strings (`svg_path` and `normalized_svg_path`) for single-element rendering.
- **Interactive Viewer**: Open [`viewer.html`](viewer.html) in your browser to inspect overlays on sample pages immediately.

---

## Repository Structure

```text
shathili-mushaf/
├── ALSHAZLY__ALGZAER__WARSH.pdf        # Source Mushaf PDF (download from Internet Archive)
├── template_ring.png                   # Ayah marker template
├── template_ring_hollow_bitmask.png    # Hollow bitmask for Thumun marker detection
├── template_surah_header.png           # Surah header banner template
├── mushaf_pipeline.py                  # High-performance batch extraction pipeline
├── map_surah_ayahs.py                  # Generates Surah-to-Ayah mapping & tags every Ayah
├── check_surah_ayah_counts.py          # Verification CLI: tests all 114 Surahs against canonical counts
├── generate_all_overlays.py            # Generates visual debug JPEG overlays for all pages
├── viewer.html                         # Interactive HTML/SVG demo viewer (zero-dependency)
├── output/
│   ├── pages/                          # Per-page JSON files (000.json to 605.json)
│   │   ├── 000.json
│   │   ├── ...
│   │   ├── 071.json
│   │   └── 605.json
│   ├── overlays/                       # Visual verification JPEG overlays (000.jpg to 605.jpg)
│   ├── mushaf_ayah_masks.json          # Consolidated single dataset (~15.7 MB, ~1.2 MB gzipped)
│   ├── surah_ayah_mapping.json         # Standalone Surah-to-Ayah hierarchical dataset (~16.8 MB)
│   └── mushaf-masks.d.ts               # TypeScript type definitions
└── README.md                           # Documentation & integration guides
```

---

## Data Schema (`pages/{page_num}.json`)

Each page JSON file is self-contained and formatted as follows:

```json
{
  "page_number": 71,
  "dimensions": { "width": 621, "height": 878 },
  "content_bounds": {
    "x_min": 31, "y_min": 24, "x_max": 591, "y_max": 853,
    "normalized": { "x_min": 0.050, "y_min": 0.028, "x_max": 0.952, "y_max": 0.972 }
  },
  "lines_count": 15,
  "ayahs_count": 8,
  "thumun_count": 0,
  "thumun_markers": [],
  "markers_count": 8,
  "headers_count": 0,
  "headers": [],
  "ayahs": [
    {
      "ayah_index": 1,
      "start_line": 1,
      "end_line": 1,
      "is_continuation_to_next_page": false,
      "has_thumun": false,
      "thumun_marker": null,
      "compact_polygons": ["0.187%"],
      "segments": [
        {
          "line": 1,
          "start_pct": 100.0,
          "end_pct": 0.187,
          "x_right_norm": 0.9308,
          "x_left_norm": 0.0692,
          "y_top_norm": 0.0273,
          "y_bottom_norm": 0.0900,
          "pixel_rect": [43, 24, 578, 79]
        }
      ],
      "pixel_polygons": [
        [[43, 24], [578, 24], [578, 79], [43, 79]]
      ],
      "svg_path": "M 43 24 L 578 24 L 578 79 L 43 79 Z",
      "normalized_svg_path": "M 0.0692 0.0273 L 0.9308 0.0273 L 0.9308 0.0900 L 0.0692 0.0900 Z",
      "marker": {
        "cx": 60, "cy": 52, "w": 35, "h": 37,
        "cx_norm": 0.0966, "cy_norm": 0.0592,
        "line": 1, "score": 0.65,
        "is_predicted": false,
        "is_hollow": false,
        "type": "ayah"
      }
    }
  ]
}
```

### Key Properties

| Property | Type | Description |
| :--- | :--- | :--- |
| `svg_path` | `string` | SVG multi-polygon path command `M x y ... Z`. Drop directly into `<path d={ayah.svg_path} />`. |
| `normalized_svg_path` | `string` | Resolution-independent SVG path scaled to $0.0 \dots 1.0$. Use with SVG `viewBox="0 0 1 1"`. |
| `segments` | `Array` | Line-by-line bounding coordinates (normalized and pixels) for Canvas or Flutter painting. |
| `has_thumun` | `boolean` | `true` if this verse contains an unnumbered hollow Thumun (1/8 Hizb) marker inside it. |
| `thumun_marker` | `Object \| null` | Coordinates of the Thumun marker inside this verse (`cx`, `cy`, `line`, etc.). |
| `thumun_markers` | `Array` | Page-level list of all hollow Thumun markers found on the page. |
| `basmalas` | `Array` | Bounding boxes and SVG paths for Basmala lines (`line`, `pixel_rect`, `svg_path`). |
| `headers` | `Array` | Surah header bounding boxes and covered 2-line span (`start_line`, `end_line`, `has_basmala`). |
| `compact_polygons` | `Array` | Industry-standard compact notation (`"f"` for full line, percentage strings for margins). |
| `marker` | `Object` | Pixel and normalized center coordinates of the verse end ring marker. |
| `is_continuation_to_next_page` | `boolean` | `true` if this segment represents verse text at the bottom of the page that continues onto the next page. |

---

## Quick Integration Guides

### 1. React / Next.js / Web (Using SVG Overlay)

```tsx
import React, { useState } from 'react';

interface MushafPageViewProps {
  pageImageUrl: string;
  pageData: {
    dimensions: { width: number; height: number };
    ayahs: Array<{ ayah_index: number; svg_path: string }>;
  };
}

export function MushafPageView({ pageImageUrl, pageData }: MushafPageViewProps) {
  const [selectedAyah, setSelectedAyah] = useState<number | null>(null);
  const { width, height } = pageData.dimensions;

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: width }}>
      {/* Background Mushaf Page */}
      <img
        src={pageImageUrl}
        alt="Mushaf Page"
        style={{ width: '100%', height: 'auto', display: 'block' }}
      />

      {/* SVG Mask Overlay */}
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
      >
        {pageData.ayahs.map((ayah) => {
          const isSelected = selectedAyah === ayah.ayah_index;
          return (
            <path
              key={ayah.ayah_index}
              d={ayah.svg_path}
              fill={isSelected ? 'rgba(251, 191, 36, 0.45)' : 'rgba(56, 189, 248, 0.1)'}
              stroke={isSelected ? '#f59e0b' : 'transparent'}
              strokeWidth={1.5}
              style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
              onClick={() => setSelectedAyah(ayah.ayah_index)}
            />
          );
        })}
      </svg>
    </div>
  );
}
```

---

### 2. Flutter (`CustomPainter`)

```dart
import 'package:flutter/material.dart';

class AyahHighlightPainter extends CustomPainter {
  final List<AyahSegment> segments;
  final Rect pageRect; // Bounding rect on screen
  final Color highlightColor;

  AyahHighlightPainter({
    required this.segments,
    required this.pageRect,
    this.highlightColor = const Color(0x55FBBF24),
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = highlightColor
      ..style = PaintingStyle.fill;

    for (final seg in segments) {
      final left = pageRect.left + (seg.xLeftNorm * pageRect.width);
      final right = pageRect.left + (seg.xRightNorm * pageRect.width);
      final top = pageRect.top + (seg.yTopNorm * pageRect.height);
      final bottom = pageRect.top + (seg.yBottomNorm * pageRect.height);

      final rrect = RRect.fromRectAndRadius(
        Rect.fromLTRB(left, top, right, bottom),
        const Radius.circular(4),
      );
      canvas.drawRRect(rrect, paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
```

---

## Pipeline Usage & Re-generation

The extraction pipeline runs directly in memory using `PyMuPDF` and `OpenCV`.

### Run for all 606 pages:
```bash
python mushaf_pipeline.py --output output
```

### Generate visual verification overlays for all 606 pages:
```bash
python generate_all_overlays.py
```

### Run for a specific page range with visual verification overlays:
```bash
python mushaf_pipeline.py --start 70 --end 75 --save-overlays --output output
```

### CLI Arguments:
- `--pdf`: Path to Mushaf PDF (default: `ALSHAZLY__ALGZAER__WARSH.pdf`).
- `--template`: Path to marker ring template (default: `template_ring.png`).
- `--output`: Output directory (default: `output`).
- `--start`: Start page index (default: `0`).
- `--end`: End page index (default: `-1` for all pages).
- `--threshold`: Match threshold (default: `0.58`).
- `--save-overlays`: Render visual `.jpg` overlays into `output/overlays/`.
- `--no-overwrite`: Skip pages that already have JSON files generated.

---

## 📄 License
Distributed under the **[MIT License](LICENSE)**. Free for community, commercial, research, and educational use in all Islamic applications.
