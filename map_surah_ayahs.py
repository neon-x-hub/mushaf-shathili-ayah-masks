#!/usr/bin/env python3
"""
Surah-to-Ayah Mapping Generator - Standalone Deliverable
Builds comprehensive hierarchical mapping of all 114 Surahs and tags every Ayah
with canonical Surah and Ayah numbers.
"""

import sys
import json
from pathlib import Path
from src.mapper import build_surah_ayah_mapping, update_page_jsons_with_surah_ayah_tags


def main() -> None:
    output_dir = Path("output")
    pages_dir = output_dir / "pages"
    mapping_file = output_dir / "surah_ayah_mapping.json"
    consolidated_file = output_dir / "mushaf_ayah_masks.json"

    print("Building Surah-to-Ayah mapping across all pages...")
    mapping_data = build_surah_ayah_mapping(str(pages_dir))

    # Save standalone hierarchical deliverable
    print(f"Saving standalone mapping to {mapping_file}...")
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(mapping_data, f, ensure_ascii=False, indent=2)

    # Enrich per-page JSON files
    print("Tagging per-page JSONs with surah_number and ayah_number...")
    update_page_jsons_with_surah_ayah_tags(str(pages_dir), mapping_data)

    # Update consolidated mushaf_ayah_masks.json
    if consolidated_file.exists():
        print(f"Updating consolidated {consolidated_file}...")
        with open(consolidated_file, "r", encoding="utf-8") as f:
            cons_data = json.load(f)

        # Build lookup: (page_number, ayah_index) -> (surah_number, ayah_number, surah_name_ar, surah_name_en)
        lookup = {}
        for s in mapping_data["surahs"]:
            for a in s["ayahs"]:
                lookup[(a["page_number"], a["ayah_index_on_page"])] = {
                    "surah_number": s["number"],
                    "ayah_number": a["ayah_number"],
                    "surah_name_ar": s["name_ar"],
                    "surah_name_en": s["name_en"]
                }

        for p_key, p_obj in cons_data.get("pages", {}).items():
            p_num = int(p_key)
            for a in p_obj.get("ayahs", []):
                key = (p_num, a["ayah_index"])
                if key in lookup:
                    info = lookup[key]
                    a["surah_number"] = info["surah_number"]
                    a["ayah_number"] = info["ayah_number"]
                    a["surah_name_ar"] = info["surah_name_ar"]
                    a["surah_name_en"] = info["surah_name_en"]

        cons_data["stats"]["total_surahs"] = len(mapping_data["surahs"])
        cons_data["stats"]["total_ayahs_extracted"] = mapping_data["total_ayahs"]

        with open(consolidated_file, "w", encoding="utf-8") as f:
            json.dump(cons_data, f, ensure_ascii=False, indent=2)

    print("\n--- Surah-to-Ayah Mapping Complete ---")
    print(f"Total Surahs mapped : {mapping_data['total_surahs']}")
    print(f"Total Ayahs mapped  : {mapping_data['total_ayahs']}")
    print(f"Mapping deliverable : {mapping_file.resolve()}")


if __name__ == "__main__":
    main()
