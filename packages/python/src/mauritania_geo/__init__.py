"""mauritania-geo — the zero-dependency administrative dataset for Mauritania.

15 wilayas, 63 moughataas, 238 communes, historical era views
(era=13 → pre-2014 unified Nouakchott) and cross-script search
(French / ASCII / Arabic). Zero third-party dependencies.
"""
from __future__ import annotations

from typing import List, Optional, Union

from .data import (
    COMMUNES as _COMMUNE_DICTS,
    DATASET_META,
    MAP_BBOX,
    MOUGHATAAS as _MOUGHATAA_DICTS,
    MOUGHATAA_SVG_PATHS,
    WILAYAS as _WILAYA_DICTS,
    WILAYA_SVG_PATHS,
)
from .map import get_map_svg, get_moughataa_svg_path, get_wilaya_svg_path
from .model import COMMUNES, MOUGHATAAS, WILAYAS, Commune, Moughataa, Wilaya
from .search import SearchResult, Scored, normalize, search

__version__ = "1.0.0"
__all__ = [
    "Wilaya", "Moughataa", "Commune", "Scored", "SearchResult",
    "get_wilaya", "get_wilayas", "get_moughataa", "get_moughataas",
    "get_all_moughataas", "get_commune", "get_communes", "get_all_communes",
    "get_communes_by_moughataa", "get_moughataa_by_commune",
    "get_wilaya_by_commune", "search", "to_dropdown_options",
    "get_map_svg", "get_wilaya_svg_path", "get_moughataa_svg_path",
    "normalize", "get_dataset_meta",
    "WILAYA_SVG_PATHS", "MOUGHATAA_SVG_PATHS", "MAP_BBOX", "DATASET_META",
]


_UNIFIED_NKC = None


def normalize_era(era: Optional[Union[int, str]]) -> int:
    """Accept 13/"13"/2013 → 13 (pre-2014); anything else → 15 (current)."""
    if era in (13, "13", 2013, "2013"):
        return 13
    return 15


def build_unified_nouakchott() -> Wilaya:
    """Pre-2014 unified Nouakchott district view (era=13)."""
    parts = [w for w in WILAYAS if w.code in ("13", "14", "15")]
    n = len(parts)
    avg = lambda pick: round(sum(pick(w) for w in parts) / n, 6)  # noqa: E731
    return Wilaya(
        code="13", iso_code="MR-NKC", p_code="MR13",
        name_fr="Nouakchott", name_ar="نواكشوط", name_en="Nouakchott",
        capital="Nouakchott", capital_ar="نواكشوط",
        capital_latitude=avg(lambda w: w.capital_latitude),
        capital_longitude=avg(lambda w: w.capital_longitude),
        latitude=avg(lambda w: w.latitude),
        longitude=avg(lambda w: w.longitude),
        area_sqkm=round(sum(w.area_sqkm for w in parts), 1),
        aliases=["Nouakchott"],
        moughataas_count=sum(w.moughataas_count for w in parts),
        communes_count=sum(w.communes_count for w in parts),
        active_from=1990,
    )


def _wilaya_code_of(id_: Union[str, int]) -> str:
    raw = str(id_).strip()
    if raw.isdigit() and len(raw) <= 2:
        return raw.zfill(2)
    up = raw.upper()
    if up.startswith("MR"):
        body = up[2:]
        if body.startswith("-"):
            body = body[1:]
        if body.isdigit() and len(body) == 2:
            return body
    return raw


def get_wilaya(id_: Union[str, int], era: int = 15) -> Optional[Wilaya]:
    """Look up a wilaya by code (3, "03", "MR-03", "MR03") or name (fr/en/ar)."""
    e = normalize_era(era)
    code = _wilaya_code_of(id_)
    if e == 13 and code in ("13", "14", "15"):
        return build_unified_nouakchott()
    wanted = str(id_).strip()
    for w in WILAYAS:
        if w.code == code:
            return build_unified_nouakchott() if (e == 13 and w.code in ("13", "14", "15")) else w
    is_code_like = (wanted.isdigit() and len(wanted) <= 2) or wanted.upper().replace("-", "").startswith("MR")
    if not is_code_like:
        for w in WILAYAS:
            if wanted in (w.name_fr, w.name_en, w.name_ar, w.capital_ar) or wanted in w.aliases:
                return build_unified_nouakchott() if (e == 13 and w.code in ("13", "14", "15")) else w
        if wanted.casefold() == "nouakchott":
            return build_unified_nouakchott() if e == 13 else None
    return None


def get_wilayas(era: int = 15) -> List[Wilaya]:
    """All wilayas of the boundary era; era=13 → 13 wilayas (unified NKC)."""
    if normalize_era(era) == 15:
        return list(WILAYAS)
    out = [w for w in WILAYAS if w.code not in ("13", "14", "15")]
    return out + [build_unified_nouakchott()]


def get_moughataa(code: Union[str, int]) -> Optional[Moughataa]:
    c = str(code).strip()
    for m in MOUGHATAAS:
        if m.code == c or m.p_code == c.upper():
            return m
    return None


def get_moughataas(wilaya_code: Union[str, int], era: int = 15) -> List[Moughataa]:
    code = _wilaya_code_of(wilaya_code)
    if normalize_era(era) == 13 and code in ("13", "14", "15"):
        return [m for m in MOUGHATAAS if m.wilaya_code in ("13", "14", "15")]
    return [m for m in MOUGHATAAS if m.wilaya_code == code]


def get_all_moughataas() -> List[Moughataa]:
    return list(MOUGHATAAS)


def get_commune(code: Union[str, int]) -> Optional[Commune]:
    c = str(code).strip()
    for x in COMMUNES:
        if x.code == c or x.p_code == c.upper():
            return x
    return None


def get_communes(wilaya_code: Union[str, int], era: int = 15) -> List[Commune]:
    code = _wilaya_code_of(wilaya_code)
    if normalize_era(era) == 13 and code in ("13", "14", "15"):
        return [c for c in COMMUNES if c.wilaya_code in ("13", "14", "15")]
    return [c for c in COMMUNES if c.wilaya_code == code]


def get_all_communes() -> List[Commune]:
    return list(COMMUNES)


def get_communes_by_moughataa(moughataa_code: Union[str, int]) -> List[Commune]:
    c = str(moughataa_code).strip()
    return [x for x in COMMUNES if x.moughataa_code == c]


def get_moughataa_by_commune(commune_code: Union[str, int]) -> Optional[Moughataa]:
    commune = get_commune(commune_code)
    return get_moughataa(commune.moughataa_code) if commune else None


def get_wilaya_by_commune(commune_code: Union[str, int], era: int = 15) -> Optional[Wilaya]:
    commune = get_commune(commune_code)
    return get_wilaya(commune.wilaya_code, era) if commune else None


def get_dataset_meta() -> dict:
    return DATASET_META


def to_dropdown_options(lang: str = "fr", era: int = 15) -> List[dict]:
    """`[{"value": "01", "label": ...}]` options for HTML <select>."""
    out = []
    for w in get_wilayas(era):
        if lang == "ar":
            label = w.name_ar or w.name_fr
        elif lang == "en":
            label = w.name_en or w.name_fr
        else:
            label = w.name_fr
        out.append({"value": w.code, "label": label})
    return out
