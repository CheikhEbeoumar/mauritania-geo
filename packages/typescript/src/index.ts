/**
 * mauritania-geo — the zero-runtime-dependency geospatial & administrative
 * dataset for Mauritania: 15 wilayas, 63 moughataas, 238 communes,
 * historical era views (13 = pre-2014 unified Nouakchott) and cross-script
 * search (French / ASCII / Arabic).
 *
 * Works in Node.js, Bun, Deno, Next.js, Nuxt, Vite and browser bundlers.
 */
import type {
  Commune,
  DatasetMeta,
  DropdownOption,
  Era,
  Moughataa,
  Wilaya,
} from "./types.js";
import {
  COMMUNES,
  DATASET_META,
  MAP_BBOX,
  MOUGHATAA_SVG_PATHS,
  MOUGHATAAS,
  WILAYA_SVG_PATHS,
  WILAYAS,
} from "./data.gen.js";
import { search as fuzzySearch } from "./search.js";
import { getMapSvg, getWilayaSvgPath, getMoughataaSvgPath } from "./map.js";

export { search } from "./search.js";
export { getMapSvg, getWilayaSvgPath, getMoughataaSvgPath } from "./map.js";
export { WILAYA_SVG_PATHS, MOUGHATAA_SVG_PATHS, MAP_BBOX, DATASET_META };
export type {
  Commune, DatasetMeta, DropdownOption, Era, MapOptions, Moughataa,
  Scored, SearchOptions, SearchResult, Wilaya,
} from "./types.js";

export function normalizeEra(era?: Era | number | string | null): Era {
  if (era === 13 || era === "13" || era === 2013 || era === "2013") return 13;
  return 15;
}

function wilayaCodeOf(id: string | number): string {
  const raw = String(id).trim();
  if (/^\d{1,2}$/.test(raw)) return raw.padStart(2, "0");
  const iso = raw.toUpperCase().match(/^MR-?(\d{2})$/);
  if (iso) return iso[1];
  const pcode = raw.toUpperCase().match(/^MR(\d{2})$/);
  if (pcode) return pcode[1];
  return raw;
}

/** Wilaya matching by code / ISO / P-code / name (fr, en, ar, aliases). */
export function getWilaya(id: string | number, era: Era = 15): Wilaya | null {
  const e = normalizeEra(era);
  const code = wilayaCodeOf(id);

  if (e === 13 && (code === "13" || code === "14" || code === "15")) {
    return buildUnifiedNouakchott();
  }
  const w = WILAYAS.find((x) => x.code === code);
  if (w) {
    if (e === 13 && (w.code === "13" || w.code === "14" || w.code === "15")) {
      return buildUnifiedNouakchott();
    }
    return w;
  }
  const wanted = String(id).trim();
  if (!/^\d{1,2}$/.test(wanted) && !/^MR-?\d{2}$/i.test(wanted) && !/^MR\d{2}$/i.test(wanted)) {
    const byName = WILAYAS.find((x) =>
      x.name_fr === wanted || x.name_en === wanted ||
      x.name_ar === wanted || x.capital_ar === wanted || x.aliases.includes(wanted));
    if (byName) {
      if (e === 13 && (byName.code === "13" || byName.code === "14" || byName.code === "15")) {
        return buildUnifiedNouakchott();
      }
      return byName;
    }
    if (e === 15 && wanted.toLowerCase() === "nouakchott") return null;
    if (e === 13 && wanted.toLowerCase() === "nouakchott") return buildUnifiedNouakchott();
  }
  return null;
}

function buildUnifiedNouakchott(): Wilaya {
  const parts = WILAYAS.filter((w) => ["13", "14", "15"].includes(w.code));
  const avg = (pick: (w: Wilaya) => number) =>
    parts.reduce((acc, w) => acc + pick(w), 0) / parts.length;
  return {
    code: "13",
    iso_code: "MR-NKC",
    p_code: "MR13",
    name_fr: "Nouakchott",
    name_ar: "نواكشوط",
    name_en: "Nouakchott",
    capital: "Nouakchott",
    capital_ar: "نواكشوط",
    capital_latitude: Math.round(avg((w) => w.capital_latitude) * 1e6) / 1e6,
    capital_longitude: Math.round(avg((w) => w.capital_longitude) * 1e6) / 1e6,
    latitude: Math.round(avg((w) => w.latitude) * 1e6) / 1e6,
    longitude: Math.round(avg((w) => w.longitude) * 1e6) / 1e6,
    area_sqkm: Math.round(parts.reduce((acc, w) => acc + w.area_sqkm, 0) * 10) / 10,
    aliases: ["Nouakchott"],
    moughataas_count: parts.reduce((acc, w) => acc + w.moughataas_count, 0),
    communes_count: parts.reduce((acc, w) => acc + w.communes_count, 0),
    active_from: 1990,
  };
}

/** All wilayas of the given boundary era. era=13 → 13 wilayas (unified NKC). */
export function getWilayas(era: Era = 15): Wilaya[] {
  const e = normalizeEra(era);
  if (e === 15) return [...WILAYAS];
  const out = WILAYAS.filter((w) => !["13", "14", "15"].includes(w.code));
  return [...out, buildUnifiedNouakchott()];
}

export function getMoughataa(code: string | number): Moughataa | null {
  const c = String(code).trim();
  return MOUGHATAAS.find((m) => m.code === c || m.p_code === c.toUpperCase()) ?? null;
}

export function getMoughataas(wilayaCode: string | number, era: Era = 15): Moughataa[] {
  const e = normalizeEra(era);
  const code = wilayaCodeOf(wilayaCode);
  if (e === 13 && (code === "13" || code === "14" || code === "15")) {
    return MOUGHATAAS.filter((m) => ["13", "14", "15"].includes(m.wilaya_code));
  }
  return MOUGHATAAS.filter((m) => m.wilaya_code === code);
}

export function getAllMoughataas(): Moughataa[] {
  return [...MOUGHATAAS];
}

export function getCommune(code: string | number): Commune | null {
  const c = String(code).trim();
  return COMMUNES.find((x) => x.code === c || x.p_code === c.toUpperCase()) ?? null;
}

export function getCommunes(wilayaCode: string | number, era: Era = 15): Commune[] {
  const e = normalizeEra(era);
  const code = wilayaCodeOf(wilayaCode);
  if (e === 13 && (code === "13" || code === "14" || code === "15")) {
    return COMMUNES.filter((c) => ["13", "14", "15"].includes(c.wilaya_code));
  }
  return COMMUNES.filter((c) => c.wilaya_code === code);
}

export function getAllCommunes(): Commune[] {
  return [...COMMUNES];
}

export function getCommunesByMoughataa(moughataaCode: string | number): Commune[] {
  const c = String(moughataaCode).trim();
  return COMMUNES.filter((x) => x.moughataa_code === c);
}

/** Reverse lookup: the moughataa of a commune. */
export function getMoughataaByCommune(communeCode: string | number): Moughataa | null {
  const commune = getCommune(communeCode);
  return commune ? getMoughataa(commune.moughataa_code) : null;
}

/** Reverse lookup: the wilaya of a commune, honoring the boundary era. */
export function getWilayaByCommune(communeCode: string | number, era: Era = 15): Wilaya | null {
  const commune = getCommune(communeCode);
  if (!commune) return null;
  return getWilaya(commune.wilaya_code, era);
}

export function getDatasetMeta(): DatasetMeta {
  return DATASET_META;
}

/** `{ value, label }` options for HTML <select> (lang: "fr" | "ar" | "en"). */
export function toDropdownOptions(lang: "fr" | "ar" | "en" = "fr", era: Era = 15): DropdownOption[] {
  return getWilayas(era).map((w) => {
    const label =
      lang === "ar" ? (w.name_ar ?? w.name_fr)
        : lang === "en" ? (w.name_en ?? w.name_fr)
          : w.name_fr;
    return { value: w.code, label };
  });
}

/** Alias kept for parity with similar datasets; identical to `search`. */
export const fuzzy = fuzzySearch;

/** Default export bundling the whole API (handy for `import geo from …`). */
export default {
  DATASET_META,
  MAP_BBOX,
  WILAYA_SVG_PATHS,
  MOUGHATAA_SVG_PATHS,
  getWilaya,
  getWilayas,
  getMoughataa,
  getMoughataas,
  getAllMoughataas,
  getCommune,
  getCommunes,
  getAllCommunes,
  getCommunesByMoughataa,
  getMoughataaByCommune,
  getWilayaByCommune,
  getDatasetMeta,
  search: fuzzySearch,
  toDropdownOptions,
  getMapSvg,
  getWilayaSvgPath,
  getMoughataaSvgPath,
};
