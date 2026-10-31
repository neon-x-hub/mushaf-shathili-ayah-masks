#!/usr/bin/env python3
"""
Surah Ayah Count Verification Tool
Checks detected ayah counts against canonical Kufi recitation counts
for all 114 Surahs.
"""

import sys
import argparse
import json
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.mapper import SURAH_CATALOG, build_surah_ayah_mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify detected ayah counts against canonical counts for each Surah.")
    parser.add_argument("--pages-dir", default="output/pages", help="Path to per-page JSON directory")
    parser.add_argument("--surah", type=int, default=None, help="Inspect a specific Surah number (1-114)")
    parser.add_argument("--diff-only", action="store_true", help="Display only surahs with mismatched counts")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output results in JSON format")

    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    if not pages_dir.exists():
        print(f"Error: Pages directory '{pages_dir}' not found. Run mushaf_pipeline.py first.")
        return 1

    mapping_data = build_surah_ayah_mapping(str(pages_dir))
    surahs = mapping_data["surahs"]

    # If single surah requested
    if args.surah is not None:
        if args.surah < 1 or args.surah > 114:
            print(f"Error: Invalid Surah number {args.surah}. Must be between 1 and 114.")
            return 1

        s = surahs[args.surah - 1]
        if args.as_json:
            print(json.dumps(s, ensure_ascii=False, indent=2))
            return 0

        print(f"\n================ Surah {s['number']:03d}: {s['name_en']} ({s['name_ar']}) ================")
        print(f"Canonical Count : {s['canonical_ayah_count']}")
        print(f"Detected Count  : {s['detected_ayah_count']}")
        print(f"Status          : {'MATCH [OK]' if s['canonical_ayah_count'] == s['detected_ayah_count'] else 'MISMATCH [FAIL]'}")
        print(f"Pages           : {', '.join(f'{p:03d}' for p in s['pages'])}")
        print(f"Total Ayahs     : {len(s['ayahs'])}")
        print("-" * 65)
        print(f"{'Ayah #':<8} {'Page':<8} {'Page Ayah #':<14} {'Lines':<10} {'Marker Cx/Cy':<15}")
        print("-" * 65)
        for a in s["ayahs"]:
            lines_str = f"{a['start_line']}-{a['end_line']}" if a['start_line'] != a['end_line'] else str(a['start_line'])
            m = a.get("marker", {})
            m_str = f"({m.get('cx')}, {m.get('cy')})" if m else "None"
            print(f"{a['ayah_number']:<8} {a['page_number']:<8} {a['ayah_index_on_page']:<14} {lines_str:<10} {m_str:<15}")
        print("=" * 65)
        return 0 if s['canonical_ayah_count'] == s['detected_ayah_count'] else 1

    # Overview for all surahs
    results = []
    total_canonical = 0
    total_detected = 0
    mismatches = 0

    for s in surahs:
        canonical = s["canonical_ayah_count"]
        detected = s["detected_ayah_count"]
        diff = detected - canonical
        is_match = (diff == 0)
        total_canonical += canonical
        total_detected += detected
        if not is_match:
            mismatches += 1

        results.append({
            "number": s["number"],
            "name_en": s["name_en"],
            "name_ar": s["name_ar"],
            "canonical": canonical,
            "detected": detected,
            "diff": diff,
            "match": is_match,
            "page_start": s["pages"][0] if s["pages"] else None,
            "page_end": s["pages"][-1] if s["pages"] else None
        })

    if args.as_json:
        print(json.dumps({
            "total_surahs": len(results),
            "total_canonical_ayahs": total_canonical,
            "total_detected_ayahs": total_detected,
            "mismatches": mismatches,
            "surahs": results if not args.diff_only else [r for r in results if not r["match"]]
        }, ensure_ascii=False, indent=2))
        return 0 if mismatches == 0 else 1

    # Formatted table
    print("\n" + "=" * 80)
    print(f"{'#':<4} {'Surah Name':<18} {'Arabic':<14} {'Canonical':<10} {'Detected':<10} {'Diff':<6} {'Pages':<12} {'Status'}")
    print("=" * 80)

    for r in results:
        if args.diff_only and r["match"]:
            continue
        status_str = "PASS" if r["match"] else f"FAIL ({r['diff']:+d})"
        p_range = f"{r['page_start']:03d}-{r['page_end']:03d}" if r['page_start'] != r['page_end'] else f"{r['page_start']:03d}"
        diff_str = f"{r['diff']:+d}" if r['diff'] != 0 else "0"
        print(f"{r['number']:<4} {r['name_en']:<18} {r['name_ar']:<14} {r['canonical']:<10} {r['detected']:<10} {diff_str:<6} {p_range:<12} {status_str}")

    print("=" * 80)
    print(f"Total Surahs Checked : {len(results)}")
    print(f"Perfect Matches      : {len(results) - mismatches} / {len(results)} ({((len(results) - mismatches)/len(results))*100:.1f}%)")
    print(f"Total Canonical Ayahs: {total_canonical}")
    print(f"Total Detected Ayahs : {total_detected}")
    if mismatches == 0:
        print("RESULT: ALL 114 SURAHS PERFECTLY MATCH CANONICAL WARSH COUNTS! [PASS]")
    else:
        print(f"RESULT: {mismatches} SURAH(S) HAVE MISMATCHED AYAH COUNTS! [FAIL]")
    print("=" * 80 + "\n")

    return 0 if mismatches == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
