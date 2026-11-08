import type { Era, MapOptions } from "./types.js";
import { WILAYAS, MOUGHATAAS, MAP_BBOX, WILAYA_SVG_PATHS, MOUGHATAA_SVG_PATHS } from "./data.gen.js";

const DEFAULT_FILL = "#4a90c2";
const HOVER_FILL = "#f2a541";

function esc(s: string | null | undefined): string {
  if (s === null || s === undefined) return "";
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function viewBoxHeight(): number {
  const [minX, minY, maxX, maxY] = MAP_BBOX;
  return Math.round(1000 * (maxY - minY) / (maxX - minX) * 10) / 10;
}

/** SVG path ("d" attribute) of one wilaya; era 13 merges Nouakchott. */
export function getWilayaSvgPath(code: string | number, era: Era = 15): string | null {
  const c = String(code).padStart(2, "0");
  if (era === 13) {
    if (c === "13") {
      return [WILAYA_SVG_PATHS["13"], WILAYA_SVG_PATHS["14"], WILAYA_SVG_PATHS["15"]]
        .filter(Boolean).join(" ");
    }
    if (c === "14" || c === "15") return null;
    return WILAYA_SVG_PATHS[c] ?? null;
  }
  return WILAYA_SVG_PATHS[c] ?? null;
}

/** SVG path ("d" attribute) of one moughataa (4-digit code). */
export function getMoughataaSvgPath(code: string | number): string | null {
  return MOUGHATAA_SVG_PATHS[String(code).padStart(4, "0")] ?? null;
}

/**
 * Standalone, styled, semantic SVG map of Mauritania.
 * Every path carries id / data-code / data-name-ar / data-name-fr (+ ISO code
 * or wilaya code) so you can bind events or style regions from CSS.
 */
export function getMapSvg(options: MapOptions = {}): string {
  const era: Era = options.era === 13 ? 13 : 15;
  const moughataas = options.includeMoughataas === true;
  const className = options.className ? ` class="${esc(options.className)}"` : "";
  const h = viewBoxHeight();

  const parts: string[] = [];
  parts.push(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 ${h}"` +
    ` role="img" aria-label="Map of Mauritania (${moughataas ? 63 : era === 13 ? 13 : 15} regions)"${className}>`);
  parts.push("<title>Mauritania</title>");
  parts.push(
    "<style>" +
    `.${moughataas ? "moughataa" : "wilaya"}{fill:${DEFAULT_FILL};stroke:#fff;` +
    `stroke-width:${moughataas ? 0.5 : 1.2};cursor:pointer;transition:fill .15s ease}` +
    `.${moughataas ? "moughataa" : "wilaya"}:hover{fill:${HOVER_FILL}}` +
    "</style>");
  if (moughataas) {
    for (const m of MOUGHATAAS) {
      const d = MOUGHATAA_SVG_PATHS[m.code];
      if (!d) continue;
      parts.push(
        `<path class="moughataa" id="moughataa-${m.code}" data-code="${m.code}"` +
        ` data-name-ar="${esc(m.name_ar)}" data-name-fr="${esc(m.name_fr)}"` +
        ` data-wilaya-code="${m.wilaya_code}" d="${d}"/>`);
    }
  } else if (era === 13) {
    const nkc = WILAYAS.find((w) => w.code === "13")!;
    const d = getWilayaSvgPath("13", 13)!;
    parts.push(
      `<path class="wilaya" id="wilaya-13" data-code="13"` +
      ` data-name-ar="${esc(nkc.name_ar)}" data-name-fr="Nouakchott"` +
      ` data-iso-code="MR-NKC" d="${d}"/>`);
    for (const w of WILAYAS) {
      if (w.code === "13" || w.code === "14" || w.code === "15") continue;
      const pd = WILAYA_SVG_PATHS[w.code];
      if (!pd) continue;
      parts.push(
        `<path class="wilaya" id="wilaya-${w.code}" data-code="${w.code}"` +
        ` data-name-ar="${esc(w.name_ar)}" data-name-fr="${esc(w.name_fr)}"` +
        ` data-iso-code="${w.iso_code}" d="${pd}"/>`);
    }
  } else {
    for (const w of WILAYAS) {
      const d = WILAYA_SVG_PATHS[w.code];
      if (!d) continue;
      parts.push(
        `<path class="wilaya" id="wilaya-${w.code}" data-code="${w.code}"` +
        ` data-name-ar="${esc(w.name_ar)}" data-name-fr="${esc(w.name_fr)}"` +
        ` data-iso-code="${w.iso_code}" data-capital="${esc(w.capital)}"` +
        ` data-moughataas="${w.moughataas_count}" data-communes="${w.communes_count}"` +
        ` d="${d}"/>`);
    }
  }
  parts.push("</svg>");
  return parts.join("");
}
