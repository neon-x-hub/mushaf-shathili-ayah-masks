/**
 * TypeScript Type Definitions for Mushaf Ayah Masks Dataset
 * Al-Shazly Warsh Mushaf (Algeria Edition)
 */

export interface ContentBounds {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  normalized: {
    x_min: number; // e.g. 0.050 (5.0% from left)
    y_min: number; // e.g. 0.028 (2.8% from top)
    x_max: number; // e.g. 0.952 (95.2% from left)
    y_max: number; // e.g. 0.972 (97.2% from top)
  };
}

export interface SurahHeader {
  start_line: number; // 0-indexed start line (e.g. 0 for line 1)
  end_line: number;   // 0-indexed end line (e.g. 1 for line 2)
  y_top: number;      // Pixel top coordinate
  y_bottom: number;   // Pixel bottom coordinate
  x_left?: number;
  x_right?: number;
  score: number;      // Detection confidence score
  line_coverage_pct?: number;
  has_basmala?: boolean;
  basmala_line?: number; // 1-indexed line number of the following Basmala
}

export interface BasmalaLine {
  line: number; // 1-indexed line number (1 to 15)
  y_top: number;
  y_bottom: number;
  x_left: number;
  x_right: number;
  y_top_norm: number;
  y_bottom_norm: number;
  x_left_norm: number;
  x_right_norm: number;
  pixel_rect: [number, number, number, number];
  svg_path: string;
  normalized_svg_path: string;
  surah_header_lines: [number, number];
}

export interface AyahMarker {
  cx: number;
  cy: number;
  w: number;
  h: number;
  cx_norm: number; // Normalized center X (0.0 - 1.0)
  cy_norm: number; // Normalized center Y (0.0 - 1.0)
  line: number;    // 1-indexed line number where marker sits
  score: number;   // Detection confidence score
  is_predicted: boolean; // True if predicted at page end due to faint/missed print
  is_hollow?: boolean;   // False for numbered ayah markers
  type?: "ayah" | "thumun";
}

export interface ThumunMarker {
  cx: number;
  cy: number;
  w: number;
  h: number;
  cx_norm: number;
  cy_norm: number;
  line: number;
  score: number;
  inner_mean: number;
  is_hollow: boolean;
}

export interface AyahLineSegment {
  line: number;        // 1-indexed line number (1 to 15)
  start_pct: number;   // Right edge in RTL (100.0 = right text margin)
  end_pct: number;     // Left edge in RTL (0.0 = left text margin)
  x_right_norm: number;// Normalized coordinate (0.0 - 1.0) of right edge
  x_left_norm: number; // Normalized coordinate (0.0 - 1.0) of left edge
  y_top_norm: number;  // Normalized coordinate (0.0 - 1.0) of line top
  y_bottom_norm: number;// Normalized coordinate (0.0 - 1.0) of line bottom
  pixel_rect: [number, number, number, number]; // [left, top, right, bottom]
}

export interface AyahMask {
  ayah_index: number;
  surah_number?: number;
  ayah_number?: number;
  surah_name_ar?: string;
  surah_name_en?: string;
  start_line: number;
  end_line: number;
  /** True if this is the bottom text segment of an ayah that spills into the next page */
  is_continuation_to_next_page: boolean;
  /** True if this ayah contains an unnumbered hollow Thumun (1/8 Hizb) division marker */
  has_thumun?: boolean;
  /** Thumun marker coordinates if present inside this ayah */
  thumun_marker?: ThumunMarker | null;
  /** Compact representation: "f" for full line, or percentage strings */
  compact_polygons: Array<string | [string, string]>;
  /** Structured line segments with normalized bounding coordinates */
  segments: AyahLineSegment[];
  /** Absolute pixel polygon vertices [[x1, y1], [x2, y2], [x3, y3], [x4, y4]] */
  pixel_polygons: number[][][];
  /** Ready-to-render SVG path string 'M x y L x y ... Z' */
  svg_path: string;
  /** Normalized SVG path string (0.0 to 1.0) for viewBox="0 0 1 1" */
  normalized_svg_path: string;
  /** Ayah end ring marker, null for page-continuation trailing segment */
  marker: AyahMarker | null;
}

export interface MushafPageData {
  page_number: number;
  dimensions: {
    width: number;
    height: number;
  };
  content_bounds: ContentBounds;
  lines_count: number;
  ayahs_count: number;
  thumun_count?: number;
  thumun_markers?: ThumunMarker[];
  markers_count: number;
  headers_count: number;
  headers: SurahHeader[];
  basmalas_count?: number;
  basmalas?: BasmalaLine[];
  ayahs: AyahMask[];
}

export interface ConsolidatedMushafDataset {
  version: string;
  mushaf: string;
  total_pages: number;
  stats: {
    processed_pages: number;
    pages_with_markers: number;
    empty_pages: number;
    total_headers_detected: number;
    total_basmalas_detected: number;
    total_markers_detected: number;
    total_thumun_markers: number;
    total_predicted_markers: number;
    total_ayahs_extracted: number;
    total_surahs?: number;
  };
  pages: Record<string, MushafPageData>;
}

export interface SurahAyahItem {
  surah_number: number;
  ayah_number: number;
  page_number: number;
  ayah_index_on_page: number;
  start_line: number;
  end_line: number;
  compact_polygons: Array<string | [string, string]>;
  segments: AyahLineSegment[];
  pixel_polygons: number[][][];
  svg_path: string;
  normalized_svg_path: string;
  marker: AyahMarker;
  has_thumun?: boolean;
  thumun_marker?: ThumunMarker | null;
}

export interface SurahData {
  number: number;
  name_ar: string;
  name_en: string;
  canonical_ayah_count: number;
  detected_ayah_count: number;
  pages: number[];
  ayahs: SurahAyahItem[];
}

export interface SurahAyahMappingDataset {
  version: string;
  mushaf: string;
  total_surahs: number;
  total_ayahs: number;
  surahs: SurahData[];
}

