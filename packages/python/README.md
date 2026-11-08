# mauritania-geo (Python)

The zero-runtime-dependency geospatial & administrative dataset for
Mauritania: **15 wilayas, 63 moughataas, 238 communes**, a historical era
view (13 wilayas, pre-2014 unified Nouakchott) and cross-script fuzzy search
(French / ASCII / Arabic).

```python
import mauritania_geo as geo

wilaya = geo.get_wilaya("03")      # or 3, "MR-03", "العصابة", "Kiffa"
print(wilaya.name_fr)              # Assaba
print(wilaya.communes_count)       # 26

print(geo.search("Tidjikja").best.item.name_ar)      # تكانت
print(len(geo.get_moughataas("13", era=13)))         # 9 (pre-2014 NKC)
```

Typed (PEP 561 `py.typed`), stdlib-only, Python ≥ 3.10.
Full documentation, the TypeScript edition and the raw distributions
(JSON / CSV / SQL / SVG / GeoJSON): see the repository [README](../../README.md).

## Data sources

OCHA COD-AB (CC-BY 4.0; geometry partly © OpenStreetMap contributors, ODbL
1.0), ISO 3166-2:MR, French/Arabic Wikipedia (CC-BY-SA 4.0).
See NOTICE in the repository root.
