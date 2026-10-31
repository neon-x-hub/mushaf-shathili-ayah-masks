"""
Surah Metadata and Surah-to-Ayah Mapping Module.
Provides canonical Warsh / Madani Surah definitions and builds comprehensive mappings.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json

# Canonical 114 Surahs with Arabic name, English name, and canonical Kufi ayah count
SURAH_CATALOG = [
    {"number": 1, "name_ar": "الفاتحة", "name_en": "Al-Fatihah", "ayah_count": 7},
    {"number": 2, "name_ar": "البقرة", "name_en": "Al-Baqarah", "ayah_count": 286},
    {"number": 3, "name_ar": "آل عمران", "name_en": "Ali 'Imran", "ayah_count": 200},
    {"number": 4, "name_ar": "النساء", "name_en": "An-Nisa", "ayah_count": 176},
    {"number": 5, "name_ar": "المائدة", "name_en": "Al-Ma'idah", "ayah_count": 120},
    {"number": 6, "name_ar": "الأنعام", "name_en": "Al-An'am", "ayah_count": 165},
    {"number": 7, "name_ar": "الأعراف", "name_en": "Al-A'raf", "ayah_count": 206},
    {"number": 8, "name_ar": "الأنفال", "name_en": "Al-Anfal", "ayah_count": 75},
    {"number": 9, "name_ar": "التوبة", "name_en": "At-Tawbah", "ayah_count": 129},
    {"number": 10, "name_ar": "يونس", "name_en": "Yunus", "ayah_count": 109},
    {"number": 11, "name_ar": "هود", "name_en": "Hud", "ayah_count": 123},
    {"number": 12, "name_ar": "يوسف", "name_en": "Yusuf", "ayah_count": 111},
    {"number": 13, "name_ar": "الرعد", "name_en": "Ar-Ra'd", "ayah_count": 43},
    {"number": 14, "name_ar": "إبراهيم", "name_en": "Ibrahim", "ayah_count": 52},
    {"number": 15, "name_ar": "الحجر", "name_en": "Al-Hijr", "ayah_count": 99},
    {"number": 16, "name_ar": "النحل", "name_en": "An-Nahl", "ayah_count": 128},
    {"number": 17, "name_ar": "الإسراء", "name_en": "Al-Isra", "ayah_count": 111},
    {"number": 18, "name_ar": "الكهف", "name_en": "Al-Kahf", "ayah_count": 110},
    {"number": 19, "name_ar": "مريم", "name_en": "Maryam", "ayah_count": 98},
    {"number": 20, "name_ar": "طه", "name_en": "Ta-Ha", "ayah_count": 135},
    {"number": 21, "name_ar": "الأنبياء", "name_en": "Al-Anbiya", "ayah_count": 112},
    {"number": 22, "name_ar": "الحج", "name_en": "Al-Hajj", "ayah_count": 78},
    {"number": 23, "name_ar": "المؤمنون", "name_en": "Al-Mu'minun", "ayah_count": 118},
    {"number": 24, "name_ar": "النور", "name_en": "An-Nur", "ayah_count": 64},
    {"number": 25, "name_ar": "الفرقان", "name_en": "Al-Furqan", "ayah_count": 77},
    {"number": 26, "name_ar": "الشعراء", "name_en": "Ash-Shu'ara", "ayah_count": 227},
    {"number": 27, "name_ar": "النمل", "name_en": "An-Naml", "ayah_count": 93},
    {"number": 28, "name_ar": "القصص", "name_en": "Al-Qasas", "ayah_count": 88},
    {"number": 29, "name_ar": "العنكبوت", "name_en": "Al-'Ankabut", "ayah_count": 69},
    {"number": 30, "name_ar": "الروم", "name_en": "Ar-Rum", "ayah_count": 60},
    {"number": 31, "name_ar": "لقمان", "name_en": "Luqman", "ayah_count": 34},
    {"number": 32, "name_ar": "السجدة", "name_en": "As-Sajdah", "ayah_count": 30},
    {"number": 33, "name_ar": "الأحزاب", "name_en": "Al-Ahzab", "ayah_count": 73},
    {"number": 34, "name_ar": "سبأ", "name_en": "Saba", "ayah_count": 54},
    {"number": 35, "name_ar": "فاطر", "name_en": "Fatir", "ayah_count": 45},
    {"number": 36, "name_ar": "يس", "name_en": "Ya-Sin", "ayah_count": 83},
    {"number": 37, "name_ar": "الصافات", "name_en": "As-Saffat", "ayah_count": 182},
    {"number": 38, "name_ar": "ص", "name_en": "Sad", "ayah_count": 88},
    {"number": 39, "name_ar": "الزمر", "name_en": "Az-Zumar", "ayah_count": 75},
    {"number": 40, "name_ar": "غافر", "name_en": "Ghafir", "ayah_count": 85},
    {"number": 41, "name_ar": "فصلت", "name_en": "Fussilat", "ayah_count": 54},
    {"number": 42, "name_ar": "الشورى", "name_en": "Ash-Shura", "ayah_count": 53},
    {"number": 43, "name_ar": "الزخرف", "name_en": "Az-Zukhruf", "ayah_count": 89},
    {"number": 44, "name_ar": "الدخان", "name_en": "Ad-Dukhan", "ayah_count": 59},
    {"number": 45, "name_ar": "الجاثية", "name_en": "Al-Jathiyah", "ayah_count": 37},
    {"number": 46, "name_ar": "الأحقاف", "name_en": "Al-Ahqaf", "ayah_count": 35},
    {"number": 47, "name_ar": "محمد", "name_en": "Muhammad", "ayah_count": 38},
    {"number": 48, "name_ar": "الفتح", "name_en": "Al-Fath", "ayah_count": 29},
    {"number": 49, "name_ar": "الحجرات", "name_en": "Al-Hujurat", "ayah_count": 18},
    {"number": 50, "name_ar": "ق", "name_en": "Qaf", "ayah_count": 45},
    {"number": 51, "name_ar": "الذاريات", "name_en": "Adh-Dhariyat", "ayah_count": 60},
    {"number": 52, "name_ar": "الطور", "name_en": "At-Tur", "ayah_count": 49},
    {"number": 53, "name_ar": "النجم", "name_en": "An-Najm", "ayah_count": 62},
    {"number": 54, "name_ar": "القمر", "name_en": "Al-Qamar", "ayah_count": 55},
    {"number": 55, "name_ar": "الرحمن", "name_en": "Ar-Rahman", "ayah_count": 78},
    {"number": 56, "name_ar": "الواقعة", "name_en": "Al-Waqi'ah", "ayah_count": 96},
    {"number": 57, "name_ar": "الحديد", "name_en": "Al-Hadid", "ayah_count": 29},
    {"number": 58, "name_ar": "المجادلة", "name_en": "Al-Mujadila", "ayah_count": 22},
    {"number": 59, "name_ar": "الحشر", "name_en": "Al-Hashr", "ayah_count": 24},
    {"number": 60, "name_ar": "الممتحنة", "name_en": "Al-Mumtahanah", "ayah_count": 13},
    {"number": 61, "name_ar": "الصف", "name_en": "As-Saff", "ayah_count": 14},
    {"number": 62, "name_ar": "الجمعة", "name_en": "Al-Jumu'ah", "ayah_count": 11},
    {"number": 63, "name_ar": "المنافقون", "name_en": "Al-Munafiqun", "ayah_count": 11},
    {"number": 64, "name_ar": "التغابن", "name_en": "At-Taghabun", "ayah_count": 18},
    {"number": 65, "name_ar": "الطلاق", "name_en": "At-Talaq", "ayah_count": 12},
    {"number": 66, "name_ar": "التحريم", "name_en": "At-Tahrim", "ayah_count": 12},
    {"number": 67, "name_ar": "الملك", "name_en": "Al-Mulk", "ayah_count": 30},
    {"number": 68, "name_ar": "القلم", "name_en": "Al-Qalam", "ayah_count": 52},
    {"number": 69, "name_ar": "الحاقة", "name_en": "Al-Haqqah", "ayah_count": 52},
    {"number": 70, "name_ar": "المعارج", "name_en": "Al-Ma'arij", "ayah_count": 44},
    {"number": 71, "name_ar": "نوح", "name_en": "Nuh", "ayah_count": 28},
    {"number": 72, "name_ar": "الجن", "name_en": "Al-Jinn", "ayah_count": 28},
    {"number": 73, "name_ar": "المزمل", "name_en": "Al-Muzzammil", "ayah_count": 20},
    {"number": 74, "name_ar": "المدثر", "name_en": "Al-Muddaththir", "ayah_count": 56},
    {"number": 75, "name_ar": "القيامة", "name_en": "Al-Qiyamah", "ayah_count": 40},
    {"number": 76, "name_ar": "الإنسان", "name_en": "Al-Insan", "ayah_count": 31},
    {"number": 77, "name_ar": "المرسلات", "name_en": "Al-Mursalat", "ayah_count": 50},
    {"number": 78, "name_ar": "النبأ", "name_en": "An-Naba", "ayah_count": 40},
    {"number": 79, "name_ar": "النازعات", "name_en": "An-Nazi'at", "ayah_count": 46},
    {"number": 80, "name_ar": "عبس", "name_en": "'Abasa", "ayah_count": 42},
    {"number": 81, "name_ar": "التكوير", "name_en": "At-Takwir", "ayah_count": 29},
    {"number": 82, "name_ar": "الانفطار", "name_en": "Al-Infitar", "ayah_count": 19},
    {"number": 83, "name_ar": "المطففين", "name_en": "Al-Mutaffifin", "ayah_count": 36},
    {"number": 84, "name_ar": "الانشقاق", "name_en": "Al-Inshiqaq", "ayah_count": 25},
    {"number": 85, "name_ar": "البروج", "name_en": "Al-Buruj", "ayah_count": 22},
    {"number": 86, "name_ar": "الطارق", "name_en": "At-Tariq", "ayah_count": 17},
    {"number": 87, "name_ar": "الأعلى", "name_en": "Al-A'la", "ayah_count": 19},
    {"number": 88, "name_ar": "الغاشية", "name_en": "Al-Ghashiyah", "ayah_count": 26},
    {"number": 89, "name_ar": "الفجر", "name_en": "Al-Fajr", "ayah_count": 30},
    {"number": 90, "name_ar": "البلد", "name_en": "Al-Balad", "ayah_count": 20},
    {"number": 91, "name_ar": "الشمس", "name_en": "Ash-Shams", "ayah_count": 15},
    {"number": 92, "name_ar": "الليل", "name_en": "Al-Layl", "ayah_count": 21},
    {"number": 93, "name_ar": "الضحى", "name_en": "Ad-Duha", "ayah_count": 11},
    {"number": 94, "name_ar": "الشرح", "name_en": "Ash-Sharh", "ayah_count": 8},
    {"number": 95, "name_ar": "التين", "name_en": "At-Tin", "ayah_count": 8},
    {"number": 96, "name_ar": "العلق", "name_en": "Al-'Alaq", "ayah_count": 19},
    {"number": 97, "name_ar": "القدر", "name_en": "Al-Qadr", "ayah_count": 5},
    {"number": 98, "name_ar": "البينة", "name_en": "Al-Bayyinah", "ayah_count": 8},
    {"number": 99, "name_ar": "الزلزلة", "name_en": "Az-Zalzalah", "ayah_count": 8},
    {"number": 100, "name_ar": "العاديات", "name_en": "Al-'Adiyat", "ayah_count": 11},
    {"number": 101, "name_ar": "القارعة", "name_en": "Al-Qari'ah", "ayah_count": 11},
    {"number": 102, "name_ar": "التكاثر", "name_en": "At-Takathur", "ayah_count": 8},
    {"number": 103, "name_ar": "العصر", "name_en": "Al-'Asr", "ayah_count": 3},
    {"number": 104, "name_ar": "الهمزة", "name_en": "Al-Humazah", "ayah_count": 9},
    {"number": 105, "name_ar": "الفيل", "name_en": "Al-Fil", "ayah_count": 5},
    {"number": 106, "name_ar": "قريش", "name_en": "Quraysh", "ayah_count": 4},
    {"number": 107, "name_ar": "الماعون", "name_en": "Al-Ma'un", "ayah_count": 7},
    {"number": 108, "name_ar": "الكوثر", "name_en": "Al-Kawthar", "ayah_count": 3},
    {"number": 109, "name_ar": "الكافرون", "name_en": "Al-Kafirun", "ayah_count": 6},
    {"number": 110, "name_ar": "النصر", "name_en": "An-Nasr", "ayah_count": 3},
    {"number": 111, "name_ar": "المسد", "name_en": "Al-Masad", "ayah_count": 5},
    {"number": 112, "name_ar": "الإخلاص", "name_en": "Al-Ikhlas", "ayah_count": 4},
    {"number": 113, "name_ar": "الفلق", "name_en": "Al-Falaq", "ayah_count": 5},
    {"number": 114, "name_ar": "الناس", "name_en": "An-Nas", "ayah_count": 6}
]

SURAH_BY_NUMBER = {s["number"]: s for s in SURAH_CATALOG}


def build_surah_ayah_mapping(pages_dir: str = "output/pages") -> Dict[str, Any]:
    """
    Traverses all page JSONs in order, associates each detected ayah with its
    canonical Surah number and Ayah number within that Surah.
    """
    p_path = Path(pages_dir)
    json_files = sorted(p_path.glob("*.json"), key=lambda p: int(p.stem))

    surahs_data = []
    for s_info in SURAH_CATALOG:
        surahs_data.append({
            "number": s_info["number"],
            "name_ar": s_info["name_ar"],
            "name_en": s_info["name_en"],
            "canonical_ayah_count": s_info["ayah_count"],
            "detected_ayah_count": 0,
            "pages": [],
            "ayahs": []
        })

    surah_idx = 1

    for jf in json_files:
        pno = int(jf.stem)
        with open(jf, "r", encoding="utf-8") as f:
            pdata = json.load(f)

        headers = sorted(pdata.get("headers", []), key=lambda h: h["start_line"])
        ayahs = pdata.get("ayahs", [])

        if pno == 0:
            # Surah 1 (Al-Fatihah)
            s_obj = surahs_data[0]
            s_obj["pages"].append(pno)
            for a in ayahs:
                s_obj["detected_ayah_count"] += 1
                s_obj["ayahs"].append({
                    "surah_number": 1,
                    "ayah_number": s_obj["detected_ayah_count"],
                    "page_number": pno,
                    "ayah_index_on_page": a["ayah_index"],
                    "start_line": a.get("start_line"),
                    "end_line": a.get("end_line"),
                    "compact_polygons": a.get("compact_polygons", []),
                    "segments": a.get("segments", []),
                    "pixel_polygons": a.get("pixel_polygons", []),
                    "svg_path": a.get("svg_path", ""),
                    "normalized_svg_path": a.get("normalized_svg_path", ""),
                    "marker": a.get("marker", {}),
                    "has_thumun": a.get("has_thumun", False),
                    "thumun_marker": a.get("thumun_marker")
                })
            continue

        elif pno == 1:
            # Surah 2 (Al-Baqarah)
            surah_idx = 2
            s_obj = surahs_data[1]
            s_obj["pages"].append(pno)
            for a in ayahs:
                s_obj["detected_ayah_count"] += 1
                s_obj["ayahs"].append({
                    "surah_number": 2,
                    "ayah_number": s_obj["detected_ayah_count"],
                    "page_number": pno,
                    "ayah_index_on_page": a["ayah_index"],
                    "start_line": a.get("start_line"),
                    "end_line": a.get("end_line"),
                    "compact_polygons": a.get("compact_polygons", []),
                    "segments": a.get("segments", []),
                    "pixel_polygons": a.get("pixel_polygons", []),
                    "svg_path": a.get("svg_path", ""),
                    "normalized_svg_path": a.get("normalized_svg_path", ""),
                    "marker": a.get("marker", {}),
                    "has_thumun": a.get("has_thumun", False),
                    "thumun_marker": a.get("thumun_marker")
                })
            continue

        if not headers:
            s_obj = surahs_data[surah_idx - 1]
            if pno not in s_obj["pages"]:
                s_obj["pages"].append(pno)
            for a in ayahs:
                s_obj["detected_ayah_count"] += 1
                s_obj["ayahs"].append({
                    "surah_number": surah_idx,
                    "ayah_number": s_obj["detected_ayah_count"],
                    "page_number": pno,
                    "ayah_index_on_page": a["ayah_index"],
                    "start_line": a.get("start_line"),
                    "end_line": a.get("end_line"),
                    "compact_polygons": a.get("compact_polygons", []),
                    "segments": a.get("segments", []),
                    "pixel_polygons": a.get("pixel_polygons", []),
                    "svg_path": a.get("svg_path", ""),
                    "normalized_svg_path": a.get("normalized_svg_path", ""),
                    "marker": a.get("marker", {}),
                    "has_thumun": a.get("has_thumun", False),
                    "thumun_marker": a.get("thumun_marker")
                })
        else:
            for a in ayahs:
                m_line = a["marker"]["line"] - 1
                interval = 0
                for h in headers:
                    if m_line >= h["end_line"]:
                        interval += 1
                current_surah = surah_idx + interval
                s_obj = surahs_data[current_surah - 1]
                if pno not in s_obj["pages"]:
                    s_obj["pages"].append(pno)
                s_obj["detected_ayah_count"] += 1
                s_obj["ayahs"].append({
                    "surah_number": current_surah,
                    "ayah_number": s_obj["detected_ayah_count"],
                    "page_number": pno,
                    "ayah_index_on_page": a["ayah_index"],
                    "start_line": a.get("start_line"),
                    "end_line": a.get("end_line"),
                    "compact_polygons": a.get("compact_polygons", []),
                    "segments": a.get("segments", []),
                    "pixel_polygons": a.get("pixel_polygons", []),
                    "svg_path": a.get("svg_path", ""),
                    "normalized_svg_path": a.get("normalized_svg_path", ""),
                    "marker": a.get("marker", {}),
                    "has_thumun": a.get("has_thumun", False),
                    "thumun_marker": a.get("thumun_marker")
                })

            surah_idx += len(headers)

    return {
        "version": "1.6.0",
        "mushaf": "Al-Shazly Warsh (Algeria Edition)",
        "total_surahs": len(surahs_data),
        "total_ayahs": sum(s["detected_ayah_count"] for s in surahs_data),
        "surahs": surahs_data
    }


def update_page_jsons_with_surah_ayah_tags(
    pages_dir: str = "output/pages",
    mapping_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Enriches each per-page JSON with surah_number and ayah_number fields for each ayah.
    """
    if mapping_data is None:
        mapping_data = build_surah_ayah_mapping(pages_dir)

    # Build lookup: (page_number, ayah_index_on_page) -> (surah_number, ayah_number, surah_name_ar, surah_name_en)
    lookup = {}
    for surah in mapping_data["surahs"]:
        s_num = surah["number"]
        s_ar = surah["name_ar"]
        s_en = surah["name_en"]
        for a in surah["ayahs"]:
            key = (a["page_number"], a["ayah_index_on_page"])
            lookup[key] = {
                "surah_number": s_num,
                "ayah_number": a["ayah_number"],
                "surah_name_ar": s_ar,
                "surah_name_en": s_en
            }

    p_path = Path(pages_dir)
    json_files = sorted(p_path.glob("*.json"), key=lambda p: int(p.stem))
    for jf in json_files:
        pno = int(jf.stem)
        with open(jf, "r", encoding="utf-8") as f:
            pdata = json.load(f)

        modified = False
        for a in pdata.get("ayahs", []):
            key = (pno, a["ayah_index"])
            if key in lookup:
                info = lookup[key]
                a["surah_number"] = info["surah_number"]
                a["ayah_number"] = info["ayah_number"]
                a["surah_name_ar"] = info["surah_name_ar"]
                a["surah_name_en"] = info["surah_name_en"]
                modified = True

        if modified:
            with open(jf, "w", encoding="utf-8") as f:
                json.dump(pdata, f, ensure_ascii=False, indent=2)
