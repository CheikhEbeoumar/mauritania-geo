#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_source.py — build the canonical mauritania-geo dataset from raw sources.

Usage:
    python scripts/import_source.py --raw-dir <dir-with-OCHA-files> [--out-dir data]

Expected raw files (OCHA COD-AB "Mauritania - Subnational Administrative
Boundaries", https://data.humdata.org/dataset/cod-ab-mrt):
    mrt_admin1.geojson      15 wilaya polygons
    mrt_admin2.geojson      63 moughataa polygons
    mrt_admin3_em.geojson   238 commune polygons
    mrt_admincapitals.geojson  capitals (adm_p_lvl 1 = wilaya, 2 = moughataa)
    mrt_adminpoints.geojson    centroids for all levels

Outputs (deterministic, sorted):
    data/wilayas.json, data/moughataas.json, data/communes.json, data/meta.json
    data/geo/adm1.geojson, data/geo/adm2.geojson  (WGS84, simplified)

Zero third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from canonical_names import (
    COMMUNE_ALIASES,
    COMMUNE_ARABIC,
    COMMUNE_RENAMES,
    HISTORY,
    MOUGHATAAS,
    NKC_HISTORICAL,
    WILAYAS,
)

# Percent of commune polygons kept when simplifying ADM2 geometry.
ADM1_TOL = 0.010  # degrees (~1.1 km) — wilaya boundaries
ADM2_TOL = 0.004  # degrees (~440 m) — moughataa boundaries

SOURCES = {
    "structure_and_geometry": {
        "name": "OCHA COD-AB — Mauritania Subnational Administrative Boundaries",
        "url": "https://data.humdata.org/dataset/cod-ab-mrt",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "attribution": "© OCHA / official Mauritanian sources",
        "used_for": "hierarchy, P-codes, polygons, areas, centroids, capitals",
    },
    "iso_codes": {
        "name": "ISO 3166-2:MR",
        "url": "https://www.iso.org/obp/ui/#iso:code:3166:MR",
        "license": "ISO 3166 codes (facts)",
        "used_for": "ISO 3166-2 codes MR-01..MR-15 (MR-NKC deleted 2015-11-27)",
    },
    "french_spellings": {
        "name": "French Wikipedia + citypopulation.de",
        "url": "https://fr.wikipedia.org/wiki/Subdivisions_de_la_Mauritanie",
        "license": "CC-BY-SA 4.0 / public reference",
        "used_for": "canonical French spellings verification",
    },
    "arabic_names": {
        "name": "Arabic Wikipedia",
        "url": "https://ar.wikipedia.org/wiki/%D9%85%D9%88%D8%B1%D9%8A%D8%AA%D8%A7%D9%86%D9%8A%D8%A7",
        "license": "CC-BY-SA 4.0",
        "used_for": "Arabic names of wilayas, moughataas and communes",
    },
}


def ascii_fold(text: str) -> str:
    """Kaédi -> Kaedi, Aïoun El Atrouss -> Aioun El Atrouss."""
    if text is None:
        return None
    decomposed = unicodedata.normalize("NFKD", text)
    out = []
    for ch in decomposed:
        if unicodedata.combining(ch):
            continue
        if ch in "‘’`":
            ch = "'"
        out.append(ch)
    return unicodedata.normalize("NFKC", "".join(out))


# ---------------------------------------------------------------------------
# Pure-python geometry helpers (no shapely dependency)
# ---------------------------------------------------------------------------
def _perpendicular_distance(point, line_start, line_end):
    if line_start == line_end:
        dx, dy = point[0] - line_start[0], point[1] - line_start[1]
        return math.hypot(dx, dy)
    x0, y0 = line_start
    x1, y1 = line_end
    x2, y2 = point
    num = abs((y1 - y0) * x2 - (x1 - x0) * y2 + x1 * y0 - y1 * x0)
    den = math.hypot(x1 - x0, y1 - y0)
    return num / den


def douglas_peucker(points, tolerance):
    """Iterative Douglas-Peucker (avoids recursion limits on big rings)."""
    n = len(points)
    if n < 3:
        return points[:]
    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack = [(0, n - 1)]
    while stack:
        lo, hi = stack.pop()
        if hi <= lo + 1:
            continue
        dmax, idx = -1.0, -1
        for i in range(lo + 1, hi):
            d = _perpendicular_distance(points[i], points[lo], points[hi])
            if d > dmax:
                dmax, idx = d, i
        if dmax > tolerance:
            keep[idx] = True
            stack.append((lo, idx))
            stack.append((idx, hi))
    return [p for p, k in zip(points, keep) if k]


def simplify_ring(ring, tolerance):
    """DP-simplify a closed ring, preserving closure and >= 4 points."""
    closed = len(ring) >= 2 and ring[0] == ring[-1]
    body = ring[:-1] if closed else ring
    if len(body) <= 4:
        return list(ring)
    simplified = douglas_peucker(body, tolerance)
    if len(simplified) < 3:
        simplified = body
    if closed:
        simplified = simplified + [simplified[0]]
    return simplified


def simplify_geometry(geom, tolerance):
    gtype = geom["type"]
    if gtype == "Polygon":
        return {"type": "Polygon", "coordinates": [
            simplify_ring(r, tolerance) for r in geom["coordinates"]]}
    if gtype == "MultiPolygon":
        return {"type": "MultiPolygon", "coordinates": [
            [simplify_ring(r, tolerance) for r in poly]
            for poly in geom["coordinates"]]}
    raise ValueError(f"unexpected geometry type {gtype}")


def round_geometry(geom, ndigits=5):
    def rnd(x):
        return round(x, ndigits)
    gtype = geom["type"]
    if gtype == "Polygon":
        return {"type": "Polygon", "coordinates": [
            [[rnd(x), rnd(y)] for x, y in r] for r in geom["coordinates"]]}
    if gtype == "MultiPolygon":
        return {"type": "MultiPolygon", "coordinates": [
            [[[rnd(x), rnd(y)] for x, y in r] for r in poly]
            for poly in geom["coordinates"]]}
    raise ValueError(gtype)


def load_geojson(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Import pipeline
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    default_raw = here.parent.parent.parent / "work" / "raw"
    parser.add_argument("--raw-dir", type=Path, default=default_raw)
    parser.add_argument("--out-dir", type=Path, default=here.parent / "data")
    args = parser.parse_args()
    raw, out = args.raw_dir, args.out_dir
    (out / "geo").mkdir(parents=True, exist_ok=True)

    adm1 = load_geojson(raw / "mrt_admin1.geojson")["features"]
    adm2 = load_geojson(raw / "mrt_admin2.geojson")["features"]
    adm3 = load_geojson(raw / "mrt_admin3_em.geojson")["features"]
    capitals = load_geojson(raw / "mrt_admincapitals.geojson")["features"]

    # ---------------- wilayas ------------------------------------------------
    # NOTE: mrt_admincapitals uses legacy (pre-2014, alphabetical) P-codes that
    # disagree with mrt_admin1.geojson — match capitals by city name instead.
    CAPITAL_CANON = {  # ascii_lower(OCHA name) -> canonical display name
        "nema": "Néma", "aioun el atrouss": "Aïoun El Atrouss",
        "kaedi": "Kaédi", "selibaby": "Sélibaby", "tijikja": "Tidjikja",
        "zouerate": "Zouérat",
    }
    wilaya_cap_lookup = {}
    for w in WILAYAS:
        wilaya_cap_lookup[ascii_fold(w[5]).lower()] = w[5]
    cap1 = {}
    for f in capitals:
        p = f["properties"]
        if p.get("adm_p_lvl") == 1:
            key = ascii_fold(p["name"]).lower()
            if key in CAPITAL_CANON:
                canon = CAPITAL_CANON[key]
                cap1[canon] = (canon, p["x_coord"], p["y_coord"])
            elif key in wilaya_cap_lookup:
                canon = wilaya_cap_lookup[key]
                cap1[canon] = (canon, p["x_coord"], p["y_coord"])
    # Nouakchott city coordinates (capital of the 3 NKC wilayas) — OCHA
    # adminpoints centroid of the three wilayas averages to the city center;
    # we use the classic documented coordinates of Nouakchott instead.
    NKC_CAPITAL_COORDS = (18.0785, -15.9658)

    wilaya_by_pcode = {}
    for w in WILAYAS:
        code, iso, pcode, fr, ar, capital, capital_ar, aliases = w
        feat = next((f for f in adm1 if f["properties"]["adm1_pcode"] == pcode), None)
        if feat is None:
            sys.exit(f"FATAL: wilaya p_code {pcode} not found in COD-AB")
        pr = feat["properties"]
        lat, lon = pr["center_lat"], pr["center_lon"]
        if capital == "Nouakchott":
            cap_lat, cap_lon = NKC_CAPITAL_COORDS
        else:
            cap_info = cap1.get(capital)
            if cap_info:
                cap_name, cap_lon, cap_lat = cap_info
            else:
                cap_name, cap_lon, cap_lat = capital, lon, lat
        wilaya_by_pcode[pcode] = {
            "code": code,
            "iso_code": iso,
            "p_code": pcode,
            "name_fr": fr,
            "name_ar": ar,
            "name_en": ascii_fold(fr),
            "capital": capital,
            "capital_ar": capital_ar or None,
            "capital_latitude": round(cap_lat, 6),
            "capital_longitude": round(cap_lon, 6),
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "area_sqkm": round(pr["area_sqkm"], 1),
            "aliases": sorted(set(aliases)),
            "moughataas_count": 0,
            "communes_count": 0,
            "active_from": 2014 if code in ("13", "14", "15") else 1990,
        }
    if len(wilaya_by_pcode) != 15:
        sys.exit("FATAL: expected 15 wilayas")

    # ---------------- moughataas --------------------------------------------
    # mrt_admincapitals uses a legacy P-code scheme that does not match the
    # admin polygons — match chief towns by NAME (ascii-insensitive) against
    # canonical names/aliases, over both level-2 and level-1 (wilaya capitals
    # that are also moughataa chief towns, e.g. Kaédi, Néma).
    cap_pool = {}
    for f in capitals:
        p = f["properties"]
        lvl = p.get("adm_p_lvl")
        if lvl in (1, 2) and p.get("name"):
            key = ascii_fold(CAPITAL_CANON.get(ascii_fold(p["name"]).lower(),
                                               p["name"])).lower()
            # level-1 wins (city-precise coordinates)
            cap_pool.setdefault(key, (p["x_coord"], p["y_coord"]))

    # chief-town display overrides (dept name != chief town name)
    CAPITAL_OVERRIDE = {"0201": "Aïoun El Atrouss"}

    # code <- ascii-normalized variant of canonical name or alias
    mg_lookup = {}
    for wcode, suffix, fr, _ar, aliases in MOUGHATAAS:
        code = wcode + f"{suffix:02d}"
        for variant in [fr] + aliases:
            mg_lookup.setdefault(ascii_fold(variant).lower(), code)

    moughataas = []
    mg_by_pcode = {}
    for wcode, suffix, fr, ar, aliases in MOUGHATAAS:
        w = wilaya_by_pcode["MR" + wcode]
        pcode = w["p_code"] + str(suffix)
        feat = next((f for f in adm2 if f["properties"]["adm2_pcode"] == pcode), None)
        if feat is None:
            sys.exit(f"FATAL: moughataa p_code {pcode} ({fr}) not found in COD-AB")
        pr = feat["properties"]
        code = wcode + f"{suffix:02d}"
        # chief town: matched by name from OCHA capital points, else centroid
        cap_name = CAPITAL_OVERRIDE.get(code, fr)
        cap_info = cap_pool.get(ascii_fold(cap_name).lower())
        if cap_info:
            cap_lon, cap_lat = cap_info
        else:
            cap_name, cap_lon, cap_lat = fr, pr["center_lon"], pr["center_lat"]
        m = {
            "code": code,
            "p_code": pcode,
            "name_fr": fr,
            "name_ar": ar,
            "name_en": ascii_fold(fr),
            "wilaya_code": wcode,
            "wilaya_name_fr": w["name_fr"],
            "latitude": round(pr["center_lat"], 6),
            "longitude": round(pr["center_lon"], 6),
            "area_sqkm": round(pr["area_sqkm"], 1),
            "capital": cap_name,
            "capital_latitude": round(cap_lat, 6) if cap_lat is not None else None,
            "capital_longitude": round(cap_lon, 6) if cap_lon is not None else None,
            "aliases": sorted(set(a for a in aliases if a != fr)),
            "communes_count": 0,
        }
        moughataas.append(m)
        mg_by_pcode[pcode] = m
    moughataas.sort(key=lambda m: m["code"])
    if len(moughataas) != 63:
        sys.exit(f"FATAL: expected 63 moughataas, got {len(moughataas)}")

    # ---------------- communes ----------------------------------------------
    # Fix the verified OCHA Teyarett <-> Toujounine commune/moughataa mix-up.
    def fix_parent(pr):
        name = pr["adm3_name"]
        if name == "Toujounine":
            return "MR141"   # Toujounine moughataa
        if name == "Teyaret":
            return "MR143"   # Teyarett moughataa
        return pr["adm2_pcode"]

    per_moughataa = defaultdict(list)
    for f in adm3:
        pr = f["properties"]
        per_moughataa[fix_parent(pr)].append(pr)

    communes = []
    for pcode, items in per_moughataa.items():
        m = mg_by_pcode.get(pcode)
        if m is None:
            sys.exit(f"FATAL: commune parent moughataa {pcode} unknown")
        # deterministic order: OCHA commune suffix when sane, else name
        def sort_key(pr):
            suf = pr["adm3_pcode"][-2:]
            return (0, suf) if suf.isdigit() else (1, ascii_fold(pr["adm3_name"]))
        ordered = sorted(items, key=sort_key)
        for i, pr in enumerate(ordered, start=1):
            ocha_name = pr["adm3_name"]
            name_fr = COMMUNE_RENAMES.get(ocha_name, ocha_name)
            aliases = []
            if name_fr != ocha_name:
                aliases.append(ocha_name)
            aliases += COMMUNE_ALIASES.get(ocha_name, [])
            c_code = m["code"] + f"{i:02d}"
            communes.append({
                "code": c_code,
                "p_code": pr["adm3_pcode"],
                "name_fr": name_fr,
                "name_ar": COMMUNE_ARABIC.get(ocha_name),
                "name_en": ascii_fold(name_fr),
                "moughataa_code": m["code"],
                "moughataa_name_fr": m["name_fr"],
                "wilaya_code": m["wilaya_code"],
                "wilaya_name_fr": m["wilaya_name_fr"],
                "latitude": round(pr["center_lat"], 6) if pr["center_lat"] is not None else None,
                "longitude": round(pr["center_lon"], 6) if pr["center_lon"] is not None else None,
                "area_sqkm": round(pr["area_sqkm"], 1) if pr.get("area_sqkm") is not None else None,
                "aliases": sorted(set(a for a in aliases if a != name_fr)),
            })
    communes.sort(key=lambda c: c["code"])

    # counts
    mg_count = defaultdict(int)
    co_count = defaultdict(int)
    for m in moughataas:
        mg_count[m["wilaya_code"]] += 1
    for c in communes:
        co_count[c["wilaya_code"]] += 1
        mg_by_code = next(mm for mm in moughataas if mm["code"] == c["moughataa_code"])
        mg_by_code["communes_count"] += 1
    for w in wilaya_by_pcode.values():
        w["moughataas_count"] = mg_count[w["code"]]
        w["communes_count"] = co_count[w["code"]]
    for m in moughataas:
        del m["wilaya_name_fr"]

    # ---------------- write data --------------------------------------------
    def dump(path, obj):
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")

    wilayas_list = [wilaya_by_pcode["MR" + w[0]] for w in WILAYAS]
    dump(out / "wilayas.json", wilayas_list)
    dump(out / "moughataas.json", moughataas)
    dump(out / "communes.json", communes)

    ar_w = sum(1 for w in wilayas_list if w["name_ar"])
    ar_m = sum(1 for m in moughataas if m["name_ar"])
    ar_c = sum(1 for c in communes if c["name_ar"])
    coords_c = sum(1 for c in communes if c["latitude"] is not None)
    meta = {
        "dataset": "mauritania-geo",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "counts": {
            "wilayas": len(wilayas_list),
            "moughataas": len(moughataas),
            "communes": len(communes),
        },
        "coverage": {
            "wilayas_name_ar": ar_w,
            "moughataas_name_ar": ar_m,
            "communes_name_ar": ar_c,
            "communes_with_coordinates": coords_c,
        },
        "eras": {
            "13": "pre-2014 view — 13 wilayas (unified Nouakchott district)",
            "15": "current view — 15 wilayas (default)",
        },
        "history": HISTORY,
        "sources": SOURCES,
    }
    dump(out / "meta.json", meta)

    # ---------------- simplified geo (WGS84) --------------------------------
    def build_geo(features, props_fn, tolerance):
        out_feats = []
        for f in features:
            pr = f["properties"]
            geom = round_geometry(simplify_geometry(f["geometry"], tolerance))
            out_feats.append({"type": "Feature", "properties": props_fn(pr),
                              "geometry": geom})
        return {"type": "FeatureCollection", "features": out_feats}

    def adm1_props(pr):
        w = wilaya_by_pcode[pr["adm1_pcode"]]
        return {kk: w[kk] for kk in ("code", "iso_code", "p_code", "name_fr",
                                     "name_ar", "name_en", "capital")}
    geo1 = build_geo(adm1, adm1_props, ADM1_TOL)

    def adm2_props(pr):
        m = mg_by_pcode[pr["adm2_pcode"]]
        return {kk: m[kk] for kk in ("code", "p_code", "name_fr", "name_ar",
                                     "name_en", "wilaya_code")}
    geo2 = build_geo(adm2, adm2_props, ADM2_TOL)

    (out / "geo" / "adm1.geojson").write_text(
        json.dumps(geo1, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (out / "geo" / "adm2.geojson").write_text(
        json.dumps(geo2, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"wilayas:    {len(wilayas_list)}  (AR {ar_w}/15)")
    print(f"moughataas: {len(moughataas)}  (AR {ar_m}/63)")
    print(f"communes:   {len(communes)}  (AR {ar_c}/238, coords {coords_c}/238)")
    print(f"geo: adm1={ (out/'geo'/'adm1.geojson').stat().st_size }B "
          f"adm2={ (out/'geo'/'adm2.geojson').stat().st_size }B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
