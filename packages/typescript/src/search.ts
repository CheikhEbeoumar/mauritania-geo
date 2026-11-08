import type { Commune, Moughataa, Scored, SearchResult, SearchOptions, Wilaya } from "./types.js";
import { WILAYAS, MOUGHATAAS, COMMUNES } from "./data.gen.js";

const ARABIC_DIACRITICS = /[\u064B-\u0652\u0670\u0640\u06D6-\u06ED]/g;

/** Fold a string for cross-script, accent-insensitive comparison. */
export function normalize(input: string): string {
  if (!input) return "";
  let s = input.normalize("NFD").replace(ARABIC_DIACRITICS, "");
  s = s.normalize("NFC")
    .replace(/[\u0623\u0625\u0622\u0671]/g, "\u0627") // أ إ آ ٱ -> ا
    .replace(/\u0629/g, "\u0647")                     // ة -> ه
    .replace(/\u0649/g, "\u064A")                     // ى -> ي
    .replace(/[\u0624]/g, "\u0648")                   // ؤ -> و
    .replace(/[\u0626]/g, "\u064A")                   // ئ -> ي
    .replace(/\u0621/g, "")                           // hamza dropped
    .toLowerCase();
  // strip Latin accents (NFD combining marks)
  s = s.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  s = s.replace(/[\u2019'`´]/g, "")
    .replace(/[^0-9a-z\u0600-\u06FF]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
  return s;
}

function squash(s: string): string {
  return s.replace(/ /g, "");
}

function scoreOne(query: string, ...targets: (string | null | undefined)[]): number {
  const q = normalize(query);
  if (!q) return 0;
  const qs = squash(q);
  let best = 0;
  for (const raw of targets) {
    if (!raw) continue;
    const t = normalize(raw);
    if (!t) continue;
    const ts = squash(t);
    let s = 0;
    if (t === q || ts === qs) s = 1.0;
    else if (t.startsWith(q) || ts.startsWith(qs)) s = 0.9;
    else if (t.split(" ").some((w) => w.startsWith(q))) s = 0.85;
    else if (t.includes(q) || ts.includes(qs)) s = 0.8;
    if (s > best) best = s;
    if (best === 1.0) break;
  }
  return best;
}

interface Bucket<T> {
  get: () => readonly T[];
  code: (item: T) => string;
  names: (item: T) => (string | null | undefined)[];
  arName: (item: T) => string | null;
  type: "wilaya" | "moughataa" | "commune";
}

function searchBucket<T>(bucket: Bucket<T>, query: string, limit: number,
                          lang?: "fr" | "ar" | "en"): Scored<T>[] {
  const out: Scored<T>[] = [];
  for (const item of bucket.get()) {
    if (lang === "ar" && !bucket.arName(item)) continue;
    const score = scoreOne(query, ...bucket.names(item));
    if (score > 0) out.push({ item, score });
  }
  out.sort((a, b) => b.score - a.score);
  return out.slice(0, limit);
}

/**
 * Cross-script fuzzy search across wilayas, moughataas and communes.
 * Understands French accents, ASCII romanizations and Arabic script
 * (diacritics, hamza variants, ta-marbuta...).
 */
export function search(query: string, options: SearchOptions = {}): SearchResult {
  const limit = options.limit && options.limit > 0 ? options.limit : 10;
  const wilayas = searchBucket<Wilaya>(
    {
      get: () => WILAYAS,
      code: (w) => w.code,
      names: (w) => [w.name_fr, w.name_en, w.name_ar, w.capital, w.capital_ar, ...w.aliases],
      arName: (w) => w.name_ar,
      type: "wilaya",
    },
    query, limit, options.lang);
  const moughataas = searchBucket<Moughataa>(
    {
      get: () => MOUGHATAAS,
      code: (m) => m.code,
      names: (m) => [m.name_fr, m.name_en, m.name_ar, ...m.aliases, m.capital],
      arName: (m) => m.name_ar,
      type: "moughataa",
    },
    query, limit, options.lang);
  const communes = searchBucket<Commune>(
    {
      get: () => COMMUNES,
      code: (c) => c.code,
      names: (c) => [c.name_fr, c.name_en, c.name_ar, ...c.aliases],
      arName: (c) => c.name_ar,
      type: "commune",
    },
    query, limit, options.lang);

  const buckets = [
    ...wilayas.map((s) => ({ ...s, level: "wilaya" as const })),
    ...moughataas.map((s) => ({ ...s, level: "moughataa" as const })),
    ...communes.map((s) => ({ ...s, level: "commune" as const })),
  ].sort((a, b) => b.score - a.score);

  const best = buckets.length
    ? { item: buckets[0].item, score: buckets[0].score, level: buckets[0].level }
    : null;

  return { wilayas, moughataas, communes, best: best as SearchResult["best"] };
}
