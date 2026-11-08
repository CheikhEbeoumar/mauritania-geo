# Contributing to mauritania-geo

Thank you for considering a contribution! This project lives or dies by the
correctness of its data, so a few rules keep it trustworthy.

## Project layout

```
data/         canonical dataset (committed, human-reviewable JSON)
data/geo/     simplified WGS84 boundaries (committed)
dist/         built distributions (committed, generated — do not hand-edit)
scripts/      import_source.py (raw → data), build.py (data → dist + packages)
packages/     the TypeScript and Python libraries
```

## Reporting a data problem

Open an issue with:

1. the division concerned (code + French name + wilaya),
2. what you believe is correct,
3. a **source**: an official decree, the Journal officiel, or at minimum two
   independent references (Wikipedia + citypopulation.de, for example).

## Changing data

1. Edit `scripts/canonical_names.py` (names, aliases, Arabic names) or
   `scripts/import_source.py` (structure logic). `data/*.json` is generated —
   regenerate it rather than editing it directly:

   ```bash
   # requires the raw OCHA COD-AB files (see README §Building from Source)
   python scripts/import_source.py --raw-dir <path-to-raw> && python scripts/build.py
   ```

2. If you cannot re-run the import (raw files are large), you may patch
   `data/*.json` directly **and** mirror the change in
   `scripts/canonical_names.py` so the next import keeps it.

3. Always run the validators:

   ```bash
   python scripts/build.py --check
   (cd packages/python && python -m unittest discover -s tests)
   (cd packages/typescript && npm test)
   ```

## Code changes

- TypeScript: strict mode, no new runtime dependencies — the whole point of
  this library is zero dependencies and instant in-memory lookups.
- Python: `py.typed`, stdlib only, same API names as the TypeScript package
  (snake_case).
- Both ecosystems must stay in feature parity; if you add a function, add it
  to both plus tests in both.

## Adding Arabic names

`name_ar` is `null` for a number of post-2018/2021 communes. Good sources are
Arabic Wikipedia articles of the moughataa or wilaya, or Mauritanian official
gazettes. Add the mapping to `COMMUNE_ARABIC` in `scripts/canonical_names.py`
(keyed by the OCHA spelling), re-run the build, and mention your source.
