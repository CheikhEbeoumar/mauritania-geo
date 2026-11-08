"""SVG map helpers (Web Mercator projection, same geometry as dist/maps)."""
from __future__ import annotations

from typing import Optional, Union

from .data import MAP_BBOX, MOUGHATAA_SVG_PATHS, WILAYA_SVG_PATHS
from .model import MOUGHATAAS as _MOUGHATAAS
from .model import WILAYAS as _WILAYAS


_SVG_WIDTH = 1000.0
_DEFAULT_FILL = "#4a90c2"
_HOVER_FILL = "#f2a541"

CodeLike = Union[str, int]


def _esc(s: Optional[str]) -> str:
    if s is None:
        return ""
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _viewbox_height() -> float:
    min_x, min_y, max_x, max_y = MAP_BBOX
    return round(_SVG_WIDTH * (max_y - min_y) / (max_x - min_x) * 10) / 10


def get_wilaya_svg_path(code: CodeLike, era: int = 15) -> Optional[str]:
    """SVG path ("d" attribute) of a wilaya; era=13 merges Nouakchott."""
    c = str(code).zfill(2)
    if era == 13:
        if c == "13":
            parts = [WILAYA_SVG_PATHS.get(x, "") for x in ("13", "14", "15")]
            merged = " ".join(p for p in parts if p)
            return merged or None
        if c in ("14", "15"):
            return None
        return WILAYA_SVG_PATHS.get(c)
    return WILAYA_SVG_PATHS.get(c)


def get_moughataa_svg_path(code: CodeLike) -> Optional[str]:
    """SVG path ("d" attribute) of a moughataa (4-digit code)."""
    return MOUGHATAA_SVG_PATHS.get(str(code).zfill(4))


def get_map_svg(era: int = 15, include_moughataas: bool = False,
                class_name: Optional[str] = None) -> str:
    """Standalone, styled, semantic SVG map of Mauritania."""
    era = 13 if era == 13 else 15
    moughataas = bool(include_moughataas)
    css_class = "moughataa" if moughataas else "wilaya"
    n = 63 if moughataas else (13 if era == 13 else 15)
    attr = f' class="{_esc(class_name)}"' if class_name else ""
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {_viewbox_height()}"'
        f' role="img" aria-label="Map of Mauritania ({n} regions)"{attr}>',
        "<title>Mauritania</title>",
        f"<style>.{css_class}{{fill:{_DEFAULT_FILL};stroke:#fff;"
        f"stroke-width:{0.5 if moughataas else 1.2};cursor:pointer;"
        f"transition:fill .15s ease}}.{css_class}:hover{{fill:{_HOVER_FILL}}}</style>",
    ]
    if moughataas:
        for m in _MOUGHATAAS:
            d = MOUGHATAA_SVG_PATHS.get(m.code)
            if not d:
                continue
            parts.append(
                f'<path class="moughataa" id="moughataa-{m.code}" data-code="{m.code}"'
                f' data-name-ar="{_esc(m.name_ar)}" data-name-fr="{_esc(m.name_fr)}"'
                f' data-wilaya-code="{m.wilaya_code}" d="{d}"/>')
    elif era == 13:
        parts.append(
            '<path class="wilaya" id="wilaya-13" data-code="13"'
            ' data-name-ar="نواكشوط" data-name-fr="Nouakchott"'
            ' data-iso-code="MR-NKC" d="' + (get_wilaya_svg_path("13", 13) or "") + '"/>')
        for w in _WILAYAS:
            if w.code in ("13", "14", "15"):
                continue
            d = WILAYA_SVG_PATHS.get(w.code)
            if not d:
                continue
            parts.append(
                f'<path class="wilaya" id="wilaya-{w.code}" data-code="{w.code}"'
                f' data-name-ar="{_esc(w.name_ar)}" data-name-fr="{_esc(w.name_fr)}"'
                f' data-iso-code="{w.iso_code}" d="{d}"/>')
    else:
        for w in _WILAYAS:
            d = WILAYA_SVG_PATHS.get(w.code)
            if not d:
                continue
            parts.append(
                f'<path class="wilaya" id="wilaya-{w.code}" data-code="{w.code}"'
                f' data-name-ar="{_esc(w.name_ar)}" data-name-fr="{_esc(w.name_fr)}"'
                f' data-iso-code="{w.iso_code}" data-capital="{_esc(w.capital)}"'
                f' data-moughataas="{w.moughataas_count}"'
                f' data-communes="{w.communes_count}" d="{d}"/>')
    parts.append("</svg>")
    return "".join(parts)
