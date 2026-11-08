import { test } from "node:test";
import assert from "node:assert/strict";
import {
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
  toDropdownOptions,
  search,
  getMapSvg,
  getWilayaSvgPath,
  getMoughataaSvgPath,
  WILAYA_SVG_PATHS,
  MOUGHATAA_SVG_PATHS,
  DATASET_META,
} from "../dist/esm/index.js";

test("dataset counts", () => {
  assert.equal(getWilayas().length, 15);
  assert.equal(getAllMoughataas().length, 63);
  assert.equal(getAllCommunes().length, 238);
  assert.equal(DATASET_META.counts.wilayas, 15);
  assert.equal(DATASET_META.counts.moughataas, 63);
  assert.equal(DATASET_META.counts.communes, 238);
});

test("wilaya lookup by code, number, ISO and name", () => {
  const assaba = getWilaya("03");
  assert.equal(assaba?.name_fr, "Assaba");
  assert.equal(assaba?.iso_code, "MR-03");
  assert.equal(assaba?.capital, "Kiffa");
  assert.equal(getWilaya(3)?.code, "03");
  assert.equal(getWilaya("MR-03")?.name_fr, "Assaba");
  assert.equal(getWilaya("MR03")?.name_fr, "Assaba");
  // capital Arabic name resolves to the wilaya it belongs to
  assert.equal(getWilaya("كيفة")?.name_fr, "Assaba");
  assert.equal(getWilaya("Guidimaka")?.code, "10"); // alias
  assert.equal(getWilaya("Hodh Chargui")?.code, "01"); // alias
  assert.equal(getWilaya(16), null);
  assert.equal(getWilaya("Atlantis"), null);
});

test("wilaya attributes", () => {
  const nkc = getWilaya("13");
  assert.equal(nkc?.name_fr, "Nouakchott-Ouest");
  assert.equal(nkc?.moughataas_count, 3);
  const tz = getWilaya("11");
  assert.ok(tz?.area_sqkm > 250000); // largest wilaya
  assert.equal(getWilaya("01")?.communes_count, 37);
});

test("moughataa and commune lookups", () => {
  const kankossa = getMoughataa("0304");
  assert.equal(kankossa?.name_fr, "Kankossa");
  assert.equal(kankossa?.name_ar, "كنكوصة");
  assert.equal(getMoughataa("MR035")?.name_fr, "Kiffa"); // p-code
  const ksar = getCommune("130101");
  assert.equal(ksar?.name_fr, "Ksar");
  assert.equal(getCommune("999999"), null);
  const kiffa = getCommune("030501");
  assert.equal(kiffa?.wilaya_code, "03");
  assert.equal(kiffa?.moughataa_code, "0305");
});

test("hierarchy helpers", () => {
  assert.equal(getMoughataas("01").length, 8);
  assert.equal(getMoughataas("14").length, 3);
  assert.equal(getCommunes("01").length, 37);
  assert.equal(getCommunesByMoughataa("0101").length, 5);
  assert.equal(getMoughataaByCommune("140301")?.name_fr, "Teyarett");
  assert.equal(getWilayaByCommune("030501")?.name_fr, "Assaba");
});

test("the verified OCHA Teyarett/Toujounine fix", () => {
  // commune Teyarett must belong to moughataa Teyarett (1403)
  const c = getAllCommunes().find((x) => x.name_fr === "Teyarett");
  assert.equal(c?.moughataa_code, "1403");
  const t = getAllCommunes().find((x) => x.name_fr === "Toujounine");
  assert.equal(t?.moughataa_code, "1401");
});

test("historical era 13 (pre-2014, unified Nouakchott)", () => {
  const wilayas13 = getWilayas(13);
  assert.equal(wilayas13.length, 13);
  const nkc = wilayas13.find((w) => w.code === "13");
  assert.equal(nkc?.name_fr, "Nouakchott");
  assert.equal(nkc?.iso_code, "MR-NKC");
  assert.equal(nkc?.moughataas_count, 9);
  assert.equal(nkc?.communes_count, 9);
  assert.equal(getWilaya("14", 13)?.name_fr, "Nouakchott");
  assert.equal(getWilaya("Nouakchott", 13)?.moughataas_count, 9);
  assert.equal(getWilaya("Nouakchott", 15), null);
  assert.equal(getMoughataas("13", 13).length, 9);
  assert.equal(getCommunes("13", 13).length, 9);
  assert.equal(getWilayaByCommune("150201", 13)?.code, "13");
  assert.equal(getWilayaByCommune("150201", 15)?.code, "15");
});

test("cross-script fuzzy search", () => {
  const fr = search("Kiffa");
  assert.ok(fr.wilayas.length >= 1);
  assert.equal(fr.wilayas[0].item.code, "03");
  assert.ok(fr.wilayas[0].score >= 0.9);
  const ar = search("كيفة");
  assert.ok(ar.wilayas.some((s) => s.item.code === "03"));
  assert.ok(ar.communes.some((s) => s.item.name_fr === "Kiffa"));
  const ascii = search("Kaedi"); // no accent
  assert.ok(ascii.wilayas.some((s) => s.item.code === "04"));
  const alias = search("Bassiknou"); // OCHA spelling
  assert.ok(alias.moughataas.some((s) => s.item.code === "0102"));
  assert.equal(search("").best, null);
  assert.ok(search("Nouadhibou", { limit: 3 }).communes.length <= 3);
});

test("dropdown options", () => {
  const fr = toDropdownOptions("fr");
  assert.equal(fr.length, 15);
  assert.equal(fr[0].value, "01");
  const ar = toDropdownOptions("ar");
  assert.ok(ar.every((o) => /[\u0600-\u06FF]/.test(o.label)));
  const era13 = toDropdownOptions("fr", 13);
  assert.equal(era13.length, 13);
});

test("SVG map helpers", () => {
  assert.equal(Object.keys(WILAYA_SVG_PATHS).length, 15);
  assert.equal(Object.keys(MOUGHATAA_SVG_PATHS).length, 63);
  assert.ok(WILAYA_SVG_PATHS["01"].startsWith("M"));
  const p01 = getWilayaSvgPath("01");
  assert.ok(p01 && p01.length > 50);
  assert.equal(getWilayaSvgPath("99"), null);
  const merged = getWilayaSvgPath("13", 13);
  const single = getWilayaSvgPath("13", 15) ?? "";
  assert.ok(merged && merged.includes("M") && merged.length > single.length);
  const svg = getMapSvg();
  assert.ok(svg.startsWith("<svg"));
  assert.ok(svg.includes('id="wilaya-01"'));
  assert.ok(svg.includes('data-name-ar="الحوض الشرقي"'));
  assert.equal((svg.match(/class="wilaya"/g) || []).length, 15);
  const svg13 = getMapSvg({ era: 13 });
  assert.equal((svg13.match(/class="wilaya"/g) || []).length, 13);
  const svgM = getMapSvg({ includeMoughataas: true });
  assert.equal((svgM.match(/class="moughataa"/g) || []).length, 63);
  const mp = getMoughataaSvgPath("0305");
  assert.ok(mp && mp.startsWith("M"));
});
