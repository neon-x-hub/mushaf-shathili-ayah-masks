#!/usr/bin/env python3
"""
Release Packaging Script for GitHub Releases
Packages the Mushaf Ayah Mask dataset into compact, distributable release archives:
- output/mushaf_ayah_masks.json.gz
- output/surah_ayah_mapping.json.gz
- output/pages.zip
"""

import sys
import gzip
import shutil
import zipfile
from pathlib import Path
from tqdm import tqdm


def gzip_file(src_path: Path, dst_path: Path) -> int:
    """Compresses a single file into a .gz archive."""
    print(f"Compressing {src_path.name} -> {dst_path.name}...")
    with open(src_path, "rb") as f_in, gzip.open(dst_path, "wb", compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)
    src_size = src_path.stat().st_size
    dst_size = dst_path.stat().st_size
    ratio = (1 - dst_size / src_size) * 100
    print(f"  {src_size / (1024*1024):.2f} MB -> {dst_size / (1024*1024):.2f} MB ({ratio:.1f}% reduction)")
    return dst_size


def zip_directory(src_dir: Path, dst_zip: Path, pattern: str = "*.json") -> int:
    """Zips files matching a pattern from a directory into a single zip archive."""
    files = sorted(list(src_dir.glob(pattern)))
    print(f"Zipping {len(files)} files from {src_dir} -> {dst_zip.name}...")
    with zipfile.ZipFile(dst_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in tqdm(files, desc="Archiving pages"):
            zf.write(f, arcname=f.name)
    dst_size = dst_zip.stat().st_size
    print(f"  Saved {dst_zip.name} ({dst_size / (1024*1024):.2f} MB)")
    return dst_size


def main() -> None:
    output_dir = Path("output")
    if not output_dir.exists():
        print("Error: output/ directory not found. Please run the pipeline first.")
        sys.exit(1)

    print("==================================================")
    print("Packaging Mushaf Dataset for GitHub Releases")
    print("==================================================\n")

    # 1. Package mushaf_ayah_masks.json.gz
    masks_json = output_dir / "mushaf_ayah_masks.json"
    if masks_json.exists():
        gzip_file(masks_json, output_dir / "mushaf_ayah_masks.json.gz")
    else:
        print(f"Warning: {masks_json} not found.")

    # 2. Package surah_ayah_mapping.json.gz
    mapping_json = output_dir / "surah_ayah_mapping.json"
    if mapping_json.exists():
        gzip_file(mapping_json, output_dir / "surah_ayah_mapping.json.gz")
    else:
        print(f"Warning: {mapping_json} not found.")

    # 3. Package pages.zip
    pages_dir = output_dir / "pages"
    if pages_dir.exists():
        zip_directory(pages_dir, output_dir / "pages.zip", "*.json")
    else:
        print(f"Warning: {pages_dir} not found.")

    print("\n==================================================")
    print("Packaging Complete! Assets ready for GitHub Release:")
    print("==================================================")
    for p in [output_dir / "mushaf_ayah_masks.json.gz",
              output_dir / "surah_ayah_mapping.json.gz",
              output_dir / "pages.zip",
              Path("Mushaf-Ashathili.pdf")]:
        if p.exists():
            print(f"  - {p.as_posix():<35} ({p.stat().st_size / (1024*1024):.2f} MB)")
    print("\nTo publish via GitHub CLI (optional):")
    print("  gh release create v2.0.0 output/*.gz output/pages.zip Mushaf-Ashathili.pdf --title \"v2.0.0\"")


if __name__ == "__main__":
    main()
