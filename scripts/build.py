#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — validate the canonical dataset and build every distribution.

Usage:
    python scripts/build.py --check     # validate only (CI)
    python scripts/build.py             # validate + build dist/ + package payloads

Outputs:
    dist/wilayas.min.json, dist/moughataas.min.json, dist/communes.min.json
    dist/tree.min.json, dist/meta.json
    dist/csv/wilayas.csv, dist/csv/moughataas.csv, dist/csv/communes.csv
    dist/mauritania_geo.sql              (PostgreSQL / SQLite)
    dist/mauritania_geo.mysql.sql        (MySQL / MariaDB)
    dist/maps/mauritania-15.svg, .min.svg, mauritania-15.geojson
    dist/maps/mauritania-moughataas-63.geojson
    packages/typescript/src/data.gen.ts  (generated payload)
    packages/python/src/mauritania_geo/data.py (generated payload)

Zero third-party dependencies.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = REPO / "data"
DIST = REPO / "dist"
TS_PKG = REPO / "packages" / "typescript"
PY_PKG = REPO / "packages" / "python"

SVG_WIDTH = 1000.0


# ---------------------------------------------------------------------------
# loading + validation
# ---------------------------------------------------------------------------
def load_all():
    wilayas = json.loads((DATA / "wilayas.json").read_text("utf-8"))
    moughataas = json.loads((DATA / "moughataas.json").read_text("utf-8"))
    communes = json.loads((DATA / "communes.json").read_text("utf-8"))
    meta = json.loads((DATA / "meta.json").read_text("utf-8"))
    geo1 = json.loads((DATA / "geo" / "adm1.geojson").read_text("utf-8"))
    geo2 = json.loads((DATA / "geo" / "adm2.geojson").read_text("utf-8"))
    return wilayas, moughataas, communes, meta, geo1, geo2


def validate(wilayas, moughataas, communes, meta, geo1, geo2) -> list[str]:
    errors: list[str] = []
    if len(wilayas) != 15:
        errors.append(f"expected 15 wilayas, got {len(wilayas)}")
    if len(moughataas) != 63:
        errors.append(f"expected 63 moughataas, got {len(moughataas)}")
    if len(communes) != 238:
        errors.append(f"expected 238 communes, got {len(communes)}")

    wcodes = [w["code"] for w in wilayas]
    if len(set(wcodes)) != len(wcodes):
        errors.append("duplicate wilaya codes")
    mcodes = [m["code"] for m in moughataas]
    if len(set(mcodes)) != len(mcodes):
        errors.append("duplicate moughataa codes")
    ccodes = [c["code"] for c in communes]
    if len(set(ccodes)) != len(ccodes):
        errors.append("duplicate commune codes")

    wset, mset = set(wcodes), set(mcodes)
    for m in moughataas:
        if m["wilaya_code"] not in wset:
            errors.append(f"moughataa {m['code']} has unknown wilaya {m['wilaya_code']}")
    for c in communes:
        if c["moughataa_code"] not in mset:
            errors.append(f"commune {c['code']} has unknown moughataa {c['moughataa_code']}")
        if c["wilaya_code"] not in wset:
            errors.append(f"commune {c['code']} has unknown wilaya {c['wilaya_code']}")

    # hierarchy consistency: code prefixes
    for m in moughataas:
        if not m["code"].startswith(m["wilaya_code"]):
            errors.append(f"moughataa code {m['code']} does not prefix wilaya {m['wilaya_code']}")
    for c in communes:
        if not c["code"].startswith(c["moughataa_code"]):
            errors.append(f"commune code {c['code']} does not prefix moughataa {c['moughataa_code']}")

    # counts consistency
    from collections import Counter
    per_w_m = Counter(m["wilaya_code"] for m in moughataas)
    per_w_c = Counter(c["wilaya_code"] for c in communes)
    for w in wilayas:
        if per_w_m[w["code"]] != w["moughataas_count"]:
            errors.append(f"wilaya {w['code']} moughataas_count mismatch")
        if per_w_c[w["code"]] != w["communes_count"]:
            errors.append(f"wilaya {w['code']} communes_count mismatch")
    per_m_c = Counter(c["moughataa_code"] for c in communes)
    for m in moughataas:
        if per_m_c[m["code"]] != m["communes_count"]:
            errors.append(f"moughataa {m['code']} communes_count mismatch")

    # geo counts
    if len(geo1["features"]) != 15:
        errors.append("adm1 geojson must have 15 features")
    if len(geo2["features"]) != 63:
        errors.append("adm2 geojson must have 63 features")

    # arabic names sanity
    missing_ar_m = [m["code"] for m in moughataas if not m["name_ar"]]
    if meta["coverage"]["moughataas_name_ar"] != len(moughataas) - len(missing_ar_m):
        errors.append("meta coverage moughataas_name_ar mismatch")
    for w in wilayas:
        for f in ("name_fr", "name_ar", "name_en", "capital", "capital_ar", "latitude", "longitude"):
            if not w.get(f):
                errors.append(f"wilaya {w['code']} missing {f}")
    for m in moughataas:
        if not m.get("name_fr") or m.get("latitude") is None:
            errors.append(f"moughataa {m['code']} missing core fields")
    for c in communes:
        if not c.get("name_fr") or c.get("latitude") is None:
            errors.append(f"commune {c['code']} missing core fields")
    return errors


# ---------------------------------------------------------------------------
# SVG map generation (Web Mercator, like the reference project)
# ---------------------------------------------------------------------------
def mercator_norm(lon: float, lat: float) -> tuple[float, float]:
    x = (lon + 180.0) / 360.0
    lat = max(-85.0, min(85.0, lat))
    y = 0.5 - math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) / (2 * math.pi)
    return x, y


def compute_viewbox(features):
    xs, ys = [], []
    for f in features:
        for poly in iter_polys(f["geometry"]):
            for ring in poly:
                for lon, lat in ring:
                    x, y = mercator_norm(lon, lat)
                    xs.append(x)
                    ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def iter_polys(geom):
    if geom["type"] == "Polygon":
        yield geom["coordinates"]
    elif geom["type"] == "MultiPolygon":
        yield from geom["coordinates"]
    else:
        raise ValueError(geom["type"])


def geometry_to_path(geom, box) -> str:
    x0, y0, x1, y1 = box
    sx = SVG_WIDTH / (x1 - x0)
    sy = sx  # keep geographic aspect; viewBox height derived from y-extent
    parts = []
    for poly in iter_polys(geom):
        for ring in poly:
            cmds = []
            first = True
            for lon, lat in ring:
                x, y = mercator_norm(lon, lat)
                px = (x - x0) * sx
                py = (y1 - y) * sy
                if px > 1e6 or py > 1e6:
                    continue
                cmds.append(f"{'M' if first else 'L'}{px:.1f} {py:.1f}")
                first = False
            if cmds:
                cmds.append("Z")
                parts.append("".join(cmds))
    return "".join(parts)


def esc(s) -> str:
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def build_svg(wilayas, moughataas, geo1, geo2, era: int, include_moughataas=False) -> str:
    box = compute_viewbox(geo1["features"])
    x0, y0, x1, y1 = box
    height = round(SVG_WIDTH * (y1 - y0) / (x1 - x0), 1)

    paths = {}
    for f in geo1["features"]:
        paths[f["properties"]["code"]] = geometry_to_path(f["geometry"], box)
    m_paths = {f["properties"]["code"]: geometry_to_path(f["geometry"], box)
               for f in geo2["features"]}

    body = []
    body.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_WIDTH:.0f} {height}" '
        f'role="img" aria-label="Map of Mauritania ({len(geo1["features"])} wilayas)">')
    body.append(
        "<title>Mauritania — administrative regions</title>\n"
        "<style>\n"
        "  .wilaya{fill:#4a90c2;stroke:#ffffff;stroke-width:1.2;cursor:pointer;"
        "transition:fill .15s ease}\n"
        "  .wilaya:hover{fill:#f2a541}\n"
        f'  .moughataa{{fill:#7fb3d5;stroke:#ffffff;stroke-width:0.5}}\n'
        "  .moughataa:hover{fill:#f2a541}\n"
        "</style>")
    if include_moughataas:
        for m in moughataas:
            d = m_paths[m["code"]]
            a = (f'id="moughataa-{m["code"]}" data-code="{m["code"]}" '
                 f'data-name-ar="{esc(m["name_ar"])}" data-name-fr="{esc(m["name_fr"])}" '
                 f'data-wilaya-code="{m["wilaya_code"]}"')
            body.append(f'<path class="moughataa" {a} d="{d}"/>')
    else:
        for w in sorted(wilayas, key=lambda x: x["code"]):
            d = paths[w["code"]]
            a = (f'id="wilaya-{w["code"]}" data-code="{w["code"]}" '
                 f'data-name-ar="{esc(w["name_ar"])}" data-name-fr="{esc(w["name_fr"])}" '
                 f'data-iso-code="{w["iso_code"]}" data-capital="{esc(w["capital"])}" '
                 f'data-moughataas="{w["moughataas_count"]}" '
                 f'data-communes="{w["communes_count"]}"')
            body.append(f'<path class="wilaya" {a} d="{d}"/>')
    body.append("</svg>")
    return "\n".join(body)


# ---------------------------------------------------------------------------
# SQL generation
# ---------------------------------------------------------------------------
def sql_quote(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).replace("'", "''")
    return f"'{s}'"


def build_sql(wilayas, moughataas, communes, mysql: bool) -> str:
    autoinc = "AUTO_INCREMENT" if mysql else "SERIAL"
    txt = "TEXT" if mysql else "TEXT"
    out = io.StringIO()
    w = out.write
    if mysql:
        w("SET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS = 0;\n")
    w("-- mauritania-geo — ready-to-run database script\n")
    w("-- Generated by scripts/build.py — do not edit by hand.\n")
    if mysql:
        w("DROP TABLE IF EXISTS communes;\nDROP TABLE IF EXISTS moughataas;\n"
          "DROP TABLE IF EXISTS wilayas;\n")
    else:
        w("DROP TABLE IF EXISTS communes;\nDROP TABLE IF EXISTS moughataas;\n"
          "DROP TABLE IF EXISTS wilayas;\n")
    w(f"""CREATE TABLE wilayas (
  code VARCHAR(2) PRIMARY KEY,
  p_code VARCHAR(5),
  iso_code VARCHAR(6),
  name_fr {txt} NOT NULL,
  name_ar {txt},
  name_en {txt},
  capital {txt},
  capital_ar {txt},
  capital_latitude DOUBLE PRECISION,
  capital_longitude DOUBLE PRECISION,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  area_sqkm DOUBLE PRECISION,
  moughataas_count INTEGER,
  communes_count INTEGER,
  aliases {txt}
);
CREATE TABLE moughataas (
  code VARCHAR(4) PRIMARY KEY,
  p_code VARCHAR(6),
  name_fr {txt} NOT NULL,
  name_ar {txt},
  name_en {txt},
  wilaya_code VARCHAR(2) REFERENCES wilayas(code),
  capital {txt},
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  capital_latitude DOUBLE PRECISION,
  capital_longitude DOUBLE PRECISION,
  area_sqkm DOUBLE PRECISION,
  communes_count INTEGER,
  aliases {txt}
);
CREATE TABLE communes (
  code VARCHAR(6) PRIMARY KEY,
  p_code VARCHAR(9),
  name_fr {txt} NOT NULL,
  name_ar {txt},
  name_en {txt},
  moughataa_code VARCHAR(4) REFERENCES moughataas(code),
  wilaya_code VARCHAR(2) REFERENCES wilayas(code),
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  area_sqkm DOUBLE PRECISION,
  aliases {txt}
);
""")
    for wb in wilayas:
        w("INSERT INTO wilayas (code,p_code,iso_code,name_fr,name_ar,name_en,"
          "capital,capital_ar,capital_latitude,capital_longitude,latitude,longitude,"
          "area_sqkm,moughataas_count,communes_count,aliases) VALUES (")
        w(",".join([
            sql_quote(wb["code"]), sql_quote(wb["p_code"]), sql_quote(wb["iso_code"]),
            sql_quote(wb["name_fr"]), sql_quote(wb["name_ar"]), sql_quote(wb["name_en"]),
            sql_quote(wb["capital"]), sql_quote(wb.get("capital_ar")),
            sql_quote(wb["capital_latitude"]),
            sql_quote(wb["capital_longitude"]), sql_quote(wb["latitude"]),
            sql_quote(wb["longitude"]), sql_quote(wb["area_sqkm"]),
            sql_quote(wb["moughataas_count"]), sql_quote(wb["communes_count"]),
            sql_quote(", ".join(wb["aliases"])),
        ]))
        w(");\n")
    for m in moughataas:
        w("INSERT INTO moughataas (code,p_code,name_fr,name_ar,name_en,wilaya_code,"
          "capital,latitude,longitude,capital_latitude,capital_longitude,"
          "area_sqkm,communes_count,aliases) VALUES (")
        w(",".join([
            sql_quote(m["code"]), sql_quote(m["p_code"]), sql_quote(m["name_fr"]),
            sql_quote(m["name_ar"]), sql_quote(m["name_en"]), sql_quote(m["wilaya_code"]),
            sql_quote(m["capital"]), sql_quote(m["latitude"]), sql_quote(m["longitude"]),
            sql_quote(m["capital_latitude"]), sql_quote(m["capital_longitude"]),
            sql_quote(m["area_sqkm"]), sql_quote(m["communes_count"]),
            sql_quote(", ".join(m["aliases"])),
        ]))
        w(");\n")
    for c in communes:
        w("INSERT INTO communes (code,p_code,name_fr,name_ar,name_en,"
          "moughataa_code,wilaya_code,latitude,longitude,area_sqkm,aliases) VALUES (")
        w(",".join([
            sql_quote(c["code"]), sql_quote(c["p_code"]), sql_quote(c["name_fr"]),
            sql_quote(c["name_ar"]), sql_quote(c["name_en"]), sql_quote(c["moughataa_code"]),
            sql_quote(c["wilaya_code"]), sql_quote(c["latitude"]), sql_quote(c["longitude"]),
            sql_quote(c["area_sqkm"]), sql_quote(", ".join(c["aliases"])),
        ]))
        w(");\n")
    if mysql:
        w("SET FOREIGN_KEY_CHECKS = 1;\n")
    return out.getvalue()


# ---------------------------------------------------------------------------
# package payloads
# ---------------------------------------------------------------------------
def ts_str(v) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


def write_ts_payload(wilayas, moughataas, communes, meta, w_paths, m_paths, bbox) -> None:
    src = io.StringIO()
    w = src.write
    w("// GENERATED by scripts/build.py — do not edit.\n")
    w("/* eslint-disable */\n\n")
    w("import type { Wilaya, Moughataa, Commune, DatasetMeta } from \"./types\";\n\n")
    w(f"export const DATASET_META: DatasetMeta = {ts_str(meta)};\n\n")
    w(f"export const WILAYAS: Wilaya[] = {ts_str(wilayas)};\n\n")
    w(f"export const MOUGHATAAS: Moughataa[] = {ts_str(moughataas)};\n\n")
    w(f"export const COMMUNES: Commune[] = {ts_str(communes)};\n\n")
    w("/** Web-Mercator bbox of the map paths: [minX, minY, maxX, maxY]. */\n")
    w(f"export const MAP_BBOX: [number, number, number, number] = {ts_str(list(bbox))};\n\n")
    w("/** SVG path (d attribute) per wilaya code, projected like dist/maps/mauritania-15.svg. */\n")
    w(f"export const WILAYA_SVG_PATHS: Record<string, string> = {ts_str(w_paths)};\n\n")
    w("/** SVG path per moughataa code (4-digit). */\n")
    w(f"export const MOUGHATAA_SVG_PATHS: Record<string, string> = {ts_str(m_paths)};\n")
    (TS_PKG / "src" / "data.gen.ts").write_text(src.getvalue(), "utf-8")


def write_py_payload(wilayas, moughataas, communes, meta, w_paths, m_paths, bbox) -> None:
    src = io.StringIO()
    w = src.write
    w('# GENERATED by scripts/build.py — do not edit.\n')
    w('"""Embedded dataset for mauritania_geo (generated)."""\n\n')
    w("from typing import Any, Dict, List, Tuple\n\n")
    w(f"DATASET_META: Dict[str, Any] = {meta!r}\n\n")
    w(f"WILAYAS: List[Dict[str, Any]] = {wilayas!r}\n\n")
    w(f"MOUGHATAAS: List[Dict[str, Any]] = {moughataas!r}\n\n")
    w(f"COMMUNES: List[Dict[str, Any]] = {communes!r}\n\n")
    w(f"MAP_BBOX: Tuple[float, float, float, float] = {tuple(bbox)!r}\n\n")
    w("WILAYA_SVG_PATHS: Dict[str, str] = ")
    w(json.dumps(w_paths, ensure_ascii=False, separators=(",", ":")))
    w("\n\nMOUGHATAA_SVG_PATHS: Dict[str, str] = ")
    w(json.dumps(m_paths, ensure_ascii=False, separators=(",", ":")))
    w("\n")
    (PY_PKG / "src" / "mauritania_geo" / "data.py").write_text(src.getvalue(), "utf-8")


# ---------------------------------------------------------------------------
# distributions
# ---------------------------------------------------------------------------
def write_dist(wilayas, moughataas, communes, meta, geo1, geo2,
               svg_full: str, svg_min: str) -> None:
    (DIST / "csv").mkdir(parents=True, exist_ok=True)
    (DIST / "maps").mkdir(parents=True, exist_ok=True)

    def dump_min(name, obj):
        (DIST / name).write_text(
            json.dumps(obj, ensure_ascii=False, separators=(",", ":")), "utf-8")

    dump_min("wilayas.min.json", wilayas)
    dump_min("moughataas.min.json", moughataas)
    dump_min("communes.min.json", communes)
    dump_min("meta.json", meta)

    tree = []
    mg_by_w: dict[str, list] = {}
    for m in moughataas:
        mg_by_w.setdefault(m["wilaya_code"], []).append(m)
    co_by_m: dict[str, list] = {}
    for c in communes:
        co_by_m.setdefault(c["moughataa_code"], []).append(c)
    for w in sorted(wilayas, key=lambda x: x["code"]):
        node = {**{k: w[k] for k in ("code", "iso_code", "p_code", "name_fr",
                                     "name_ar", "name_en", "capital", "capital_ar")},
                "moughataas": [
                    {**{k: m[k] for k in ("code", "p_code", "name_fr", "name_ar",
                                          "name_en")},
                     "communes": [
                         {k: c[k] for k in ("code", "p_code", "name_fr", "name_ar",
                                            "name_en", "latitude", "longitude")}
                         for c in sorted(co_by_m.get(m["code"], []),
                                         key=lambda x: x["code"])]}
                    for m in sorted(mg_by_w.get(w["code"], []), key=lambda x: x["code"])]}
        tree.append(node)
    dump_min("tree.min.json", tree)

    # CSV (UTF-8 BOM for Excel)
    def csv_rows(path, header, rows):
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
        path.write_text("﻿" + buf.getvalue(), "utf-8")

    csv_rows(DIST / "csv" / "wilayas.csv",
             ["code", "p_code", "iso_code", "name_fr", "name_ar", "name_en",
              "capital", "capital_ar", "capital_latitude", "capital_longitude",
              "latitude", "longitude", "area_sqkm", "moughataas_count",
              "communes_count", "aliases"],
             [[w[c] for c in ("code", "p_code", "iso_code", "name_fr", "name_ar",
                              "name_en", "capital", "capital_ar", "capital_latitude",
                              "capital_longitude", "latitude", "longitude",
                              "area_sqkm", "moughataas_count", "communes_count")]
              + [", ".join(w["aliases"])] for w in wilayas])
    csv_rows(DIST / "csv" / "moughataas.csv",
             ["code", "p_code", "name_fr", "name_ar", "name_en", "wilaya_code",
              "capital", "latitude", "longitude", "area_sqkm", "communes_count", "aliases"],
             [[m[c] for c in ("code", "p_code", "name_fr", "name_ar", "name_en",
                              "wilaya_code", "capital", "latitude", "longitude",
                              "area_sqkm", "communes_count")]
              + [", ".join(m["aliases"])] for m in moughataas])
    csv_rows(DIST / "csv" / "communes.csv",
             ["code", "p_code", "name_fr", "name_ar", "name_en", "moughataa_code",
              "wilaya_code", "latitude", "longitude", "area_sqkm", "aliases"],
             [[c[cn] for cn in ("code", "p_code", "name_fr", "name_ar", "name_en",
                                "moughataa_code", "wilaya_code", "latitude",
                                "longitude", "area_sqkm")]
              + [", ".join(c["aliases"])] for c in communes])

    (DIST / "maps" / "mauritania-15.svg").write_text(svg_full, "utf-8")
    (DIST / "maps" / "mauritania-15.min.svg").write_text(svg_min, "utf-8")

    # dist geojson = data geo (already simplified) — copy through
    (DIST / "maps" / "mauritania-15.geojson").write_text(
        json.dumps(geo1, ensure_ascii=False, separators=(",", ":")), "utf-8")
    (DIST / "maps" / "mauritania-moughataas-63.geojson").write_text(
        json.dumps(geo2, ensure_ascii=False, separators=(",", ":")), "utf-8")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate only")
    args = parser.parse_args()

    wilayas, moughataas, communes, meta, geo1, geo2 = load_all()
    errors = validate(wilayas, moughataas, communes, meta, geo1, geo2)
    if errors:
        for e in errors:
            print("VALIDATION ERROR:", e, file=sys.stderr)
        return 1
    print(f"validation OK — {len(wilayas)} wilayas, {len(moughataas)} moughataas, "
          f"{len(communes)} communes")
    if args.check:
        return 0

    DIST.mkdir(parents=True, exist_ok=True)

    box = compute_viewbox(geo1["features"])
    svg_full = build_svg(wilayas, moughataas, geo1, geo2, era=15)
    # minified: drop newline/space runs between tags, keep XML intact
    svg_min = re.sub(r">\s+<", "><", svg_full.replace("\n", "")).strip()

    # SVG paths for the libraries (same projection as the standalone SVG)
    w_paths = {f["properties"]["code"]: geometry_to_path(f["geometry"], box)
               for f in geo1["features"]}
    m_paths = {f["properties"]["code"]: geometry_to_path(f["geometry"], box)
               for f in geo2["features"]}

    meta = {**meta,
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "map_bbox_mercator": [round(b, 8) for b in box]}

    write_dist(wilayas, moughataas, communes, meta, geo1, geo2, svg_full, svg_min)
    (DIST / "mauritania_geo.sql").write_text(
        build_sql(wilayas, moughataas, communes, mysql=False), "utf-8")
    (DIST / "mauritania_geo.mysql.sql").write_text(
        build_sql(wilayas, moughataas, communes, mysql=True), "utf-8")
    write_ts_payload(wilayas, moughataas, communes, meta, w_paths, m_paths, box)
    write_py_payload(wilayas, moughataas, communes, meta, w_paths, m_paths, box)

    for p in sorted(DIST.rglob("*")):
        if p.is_file():
            print(f"  dist/{p.relative_to(DIST)}  {p.stat().st_size}B")
    print("build complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
