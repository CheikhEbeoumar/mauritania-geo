"""Tests for mauritania_geo — stdlib unittest, zero dependencies."""
import json
import unittest

import mauritania_geo as geo


class TestCounts(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(geo.get_wilayas()), 15)
        self.assertEqual(len(geo.get_all_moughataas()), 63)
        self.assertEqual(len(geo.get_all_communes()), 238)
        self.assertEqual(geo.DATASET_META["counts"]["wilayas"], 15)
        self.assertEqual(geo.DATASET_META["counts"]["moughataas"], 63)
        self.assertEqual(geo.DATASET_META["counts"]["communes"], 238)


class TestWilayaLookup(unittest.TestCase):
    def test_by_code(self):
        w = geo.get_wilaya("03")
        self.assertEqual(w.name_fr, "Assaba")
        self.assertEqual(w.iso_code, "MR-03")
        self.assertEqual(w.capital, "Kiffa")

    def test_by_int_and_iso_and_pcode(self):
        self.assertEqual(geo.get_wilaya(3).code, "03")
        self.assertEqual(geo.get_wilaya("MR-03").name_fr, "Assaba")
        self.assertEqual(geo.get_wilaya("MR03").name_fr, "Assaba")

    def test_by_names(self):
        self.assertEqual(geo.get_wilaya("العصابة").name_fr, "Assaba")
        self.assertEqual(geo.get_wilaya("كيفة").name_fr, "Assaba")  # capital_ar
        self.assertEqual(geo.get_wilaya("Guidimaka").code, "10")    # alias
        self.assertEqual(geo.get_wilaya("Hodh Chargui").code, "01") # alias

    def test_misses(self):
        self.assertIsNone(geo.get_wilaya(16))
        self.assertIsNone(geo.get_wilaya("Atlantis"))

    def test_attributes(self):
        self.assertEqual(geo.get_wilaya("13").name_fr, "Nouakchott-Ouest")
        self.assertEqual(geo.get_wilaya("13").moughataas_count, 3)
        self.assertGreater(geo.get_wilaya("11").area_sqkm, 250000)
        self.assertEqual(geo.get_wilaya("01").communes_count, 37)


class TestMoughataasCommunes(unittest.TestCase):
    def test_moughataa(self):
        m = geo.get_moughataa("0304")
        self.assertEqual(m.name_fr, "Kankossa")
        self.assertEqual(m.name_ar, "كنكوصة")
        self.assertEqual(geo.get_moughataa("MR035").name_fr, "Kiffa")

    def test_commune(self):
        c = geo.get_commune("130101")
        self.assertEqual(c.name_fr, "Ksar")
        self.assertIsNone(geo.get_commune("999999"))
        k = geo.get_commune("030501")
        self.assertEqual(k.wilaya_code, "03")
        self.assertEqual(k.moughataa_code, "0305")

    def test_hierarchy(self):
        self.assertEqual(len(geo.get_moughataas("01")), 8)
        self.assertEqual(len(geo.get_moughataas("14")), 3)
        self.assertEqual(len(geo.get_communes("01")), 37)
        self.assertEqual(len(geo.get_communes_by_moughataa("0101")), 5)
        self.assertEqual(geo.get_moughataa_by_commune("140301").name_fr, "Teyarett")
        self.assertEqual(geo.get_wilaya_by_commune("030501").name_fr, "Assaba")

    def test_teyarett_toujounine_fix(self):
        communes = {c.name_fr: c for c in geo.get_all_communes()
                    if c.wilaya_code == "14"}
        self.assertEqual(communes["Teyarett"].moughataa_code, "1403")
        self.assertEqual(communes["Toujounine"].moughataa_code, "1401")


class TestEras(unittest.TestCase):
    def test_era13(self):
        ws = geo.get_wilayas(13)
        self.assertEqual(len(ws), 13)
        nkc = [w for w in ws if w.code == "13"][0]
        self.assertEqual(nkc.name_fr, "Nouakchott")
        self.assertEqual(nkc.iso_code, "MR-NKC")
        self.assertEqual(nkc.moughataas_count, 9)
        self.assertEqual(nkc.communes_count, 9)
        self.assertEqual(geo.get_wilaya("14", era=13).name_fr, "Nouakchott")
        self.assertEqual(geo.get_wilaya("Nouakchott", era=13).moughataas_count, 9)
        self.assertIsNone(geo.get_wilaya("Nouakchott", era=15))
        self.assertEqual(len(geo.get_moughataas("13", era=13)), 9)
        self.assertEqual(len(geo.get_communes("13", era=13)), 9)
        self.assertEqual(geo.get_wilaya_by_commune("150201", era=13).code, "13")
        self.assertEqual(geo.get_wilaya_by_commune("150201", era=15).code, "15")


class TestSearch(unittest.TestCase):
    def test_french(self):
        res = geo.search("Kiffa")
        self.assertGreaterEqual(len(res.wilayas), 1)
        self.assertEqual(res.wilayas[0].item.code, "03")
        self.assertGreaterEqual(res.wilayas[0].score, 0.9)
        self.assertEqual(res.best.item.code, "03")

    def test_arabic(self):
        res = geo.search("كيفة")
        self.assertTrue(any(s.item.code == "03" for s in res.wilayas))
        self.assertTrue(any(s.item.name_fr == "Kiffa" for s in res.communes))

    def test_ascii_variants(self):
        self.assertTrue(any(s.item.code == "04" for s in geo.search("Kaedi").wilayas))
        self.assertTrue(any(s.item.code == "0102" for s in geo.search("Bassiknou").moughataas))

    def test_empty_and_limit(self):
        self.assertIsNone(geo.search("").best)
        self.assertLessEqual(len(geo.search("Nouadhibou", limit=3).communes), 3)


class TestDropdowns(unittest.TestCase):
    def test_fr(self):
        opts = geo.to_dropdown_options("fr")
        self.assertEqual(len(opts), 15)
        self.assertEqual(opts[0]["value"], "01")

    def test_ar(self):
        for o in geo.to_dropdown_options("ar"):
            self.assertTrue(any("\u0600" <= ch <= "\u06FF" for ch in o["label"]))

    def test_era13(self):
        self.assertEqual(len(geo.to_dropdown_options("fr", era=13)), 13)


class TestMap(unittest.TestCase):
    def test_paths(self):
        self.assertEqual(len(geo.WILAYA_SVG_PATHS), 15)
        self.assertEqual(len(geo.MOUGHATAA_SVG_PATHS), 63)
        self.assertTrue(geo.WILAYA_SVG_PATHS["01"].startswith("M"))
        self.assertGreater(len(geo.get_wilaya_svg_path("01")), 50)
        self.assertIsNone(geo.get_wilaya_svg_path("99"))
        merged = geo.get_wilaya_svg_path("13", era=13)
        single = geo.get_wilaya_svg_path("13", era=15) or ""
        self.assertTrue(merged and "M" in merged and len(merged) > len(single))
        self.assertTrue(geo.get_moughataa_svg_path("0305").startswith("M"))

    def test_svg(self):
        svg = geo.get_map_svg()
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn('id="wilaya-01"', svg)
        self.assertIn('data-name-ar="الحوض الشرقي"', svg)
        self.assertEqual(svg.count('class="wilaya"'), 15)
        self.assertEqual(geo.get_map_svg(era=13).count('class="wilaya"'), 13)
        self.assertEqual(
            geo.get_map_svg(include_moughataas=True).count('class="moughataa"'), 63)


class TestSerialization(unittest.TestCase):
    def test_to_dict_json(self):
        c = geo.get_commune("030501")
        s = json.dumps(c.to_dict(), ensure_ascii=False)
        self.assertIn("Kiffa", s)
        self.assertIn("كيفة", s)


if __name__ == "__main__":
    unittest.main()
