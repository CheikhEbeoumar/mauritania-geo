// GENERATED file imports live in data.gen.ts — see that file for the payload.

/** A wilaya (region) — first-level administrative division of Mauritania. */
export interface Wilaya {
  /** 2-digit code "01".."15" (ISO 3166-2 numbering, = OCHA P-code) */
  code: string;
  /** ISO 3166-2 code, e.g. "MR-01" ("MR-NKC" for the pre-2014 district) */
  iso_code: string;
  /** OCHA/INS P-code, e.g. "MR01" */
  p_code: string;
  name_fr: string;
  name_ar: string | null;
  name_en: string;
  /** chef-lieu */
  capital: string;
  /** Arabic name of the chef-lieu (null when unknown) */
  capital_ar: string | null;
  capital_latitude: number;
  capital_longitude: number;
  /** centroid of the wilaya polygon */
  latitude: number;
  longitude: number;
  area_sqkm: number;
  aliases: string[];
  moughataas_count: number;
  communes_count: number;
  /** first year this wilaya existed under its current definition */
  active_from: number;
}

/** A moughataa (department) — second-level administrative division. */
export interface Moughataa {
  /** 4-digit code: wilaya (2) + serial within wilaya (2), e.g. "0305" */
  code: string;
  /** OCHA P-code, e.g. "MR035" */
  p_code: string;
  name_fr: string;
  name_ar: string | null;
  name_en: string;
  wilaya_code: string;
  capital: string;
  latitude: number;
  longitude: number;
  capital_latitude: number | null;
  capital_longitude: number | null;
  area_sqkm: number;
  aliases: string[];
  communes_count: number;
}

/** A commune (municipality) — third-level administrative division. */
export interface Commune {
  /** 6-digit code: wilaya (2) + moughataa (2) + serial (2), e.g. "030501" */
  code: string;
  /** OCHA P-code as published (some Nouakchott codes are legacy) */
  p_code: string;
  name_fr: string;
  name_ar: string | null;
  name_en: string;
  moughataa_code: string;
  wilaya_code: string;
  /** denormalized parent names (kept for convenience) */
  moughataa_name_fr?: string;
  wilaya_name_fr?: string;
  latitude: number | null;
  longitude: number | null;
  area_sqkm: number | null;
  aliases: string[];
}

export interface DatasetMeta {
  dataset: string;
  version: string;
  generated_at: string;
  counts: { wilayas: number; moughataas: number; communes: number };
  coverage: Record<string, number>;
  eras: Record<string, string>;
  history: Record<string, { instrument: string; effect: string }>;
  sources: Record<string, Record<string, string>>;
  built_at?: string;
  map_bbox_mercator?: number[];
}

/** Administrative boundary era: 13 = pre-2014 (unified Nouakchott), 15 = current. */
export type Era = 13 | 15;

export interface SearchOptions {
  /** preferred language bias: "fr" | "ar" | "en" (default: all) */
  lang?: "fr" | "ar" | "en";
  /** max results per level (default 10) */
  limit?: number;
}

export interface Scored<T> {
  item: T;
  score: number;
}

export interface SearchResult {
  wilayas: Scored<Wilaya>[];
  moughataas: Scored<Moughataa>[];
  communes: Scored<Commune>[];
  best: (Scored<Wilaya> | Scored<Moughataa> | Scored<Commune>) | null;
}

export interface MapOptions {
  /** boundary era to draw (default 15) */
  era?: Era;
  /** draw the 63 moughataas instead of the 15 wilayas */
  includeMoughataas?: boolean;
  /** extra CSS classes for the root svg element */
  className?: string;
}

export interface DropdownOption {
  value: string;
  label: string;
}
