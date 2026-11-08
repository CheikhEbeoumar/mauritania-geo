# Publishing to npm & PyPI

The install commands in the README — `npm install mauritania-geo` and
`pip install mauritania-geo` — resolve against the **npm registry** and
**PyPI**. They start working for every user on Earth the moment the two
packages are published from this repository. This guide covers the whole
flow.

> Registry status (checked 2026-11-08): both `mauritania-geo` on
> [npmjs.com](https://www.npmjs.com/package/mauritania-geo) and
> [pypi.org](https://pypi.org/project/mauritania-geo/) are published at
> **v1.0.0**. Use this guide for subsequent releases.

---

## 0. One-time preparation (before the first release)

1. **Replace the placeholder URLs.** Search the repo for
   `github.com/example/mauritania-geo` and replace `example` with the real
   GitHub owner, in:
   - `packages/typescript/package.json` (`homepage`, `repository.url`)
   - `packages/python/pyproject.toml` (`[project.urls]`)
   - `README.md`, `README.fr.md`, `README.ar.md` (badges & clone commands)
2. **Run the full test suite locally** (both must be green):
   ```bash
   (cd packages/typescript && npm install && npm test)
   (cd packages/python      && python -m unittest discover tests -v)
   ```

---

## 1. npm — publishing `mauritania-geo`

### One-time setup

Legacy (classic) npm tokens were removed in November 2025, so the old
"Automation" token type no longer exists. Use a **Granular Access Token**:

1. Create an account at <https://www.npmjs.com/signup> and **verify your
   email** (the first publish is blocked otherwise).
2. Enable 2FA (Settings → Two-Factor Authentication).
3. Create a token at
   <https://www.npmjs.com/settings/YOUR_USERNAME/tokens> →
   **Generate New Token** → **Granular Access Token**:
   - Permissions: **Read and write**
   - Packages: **All packages** for the very first publish (restrict it to
     `mauritania-geo` afterwards)
   - ✅ **Bypass two-factor authentication (2FA)** — required for
     non-interactive `npm publish`
   - Short expiration (e.g. 30 days)

> [!NOTE]
> Bypass-2FA tokens still allow direct `npm publish` until **January 2027**.
> After that they can only stage a publish, so move automated releases to
> trusted publishing (see §3) or `npm stage publish`.

### Publish (manual)

```bash
cd packages/typescript
# Create .npmrc (git-ignored) with the line:
#   //registry.npmjs.org/:_authToken=${NODE_AUTH_TOKEN}
export NODE_AUTH_TOKEN=npm_xxx       # PowerShell: $env:NODE_AUTH_TOKEN="npm_xxx"
npm whoami                           # confirms the token identity
npm publish                          # the "prepack" hook runs the full build first
```

That's it — the tarball (23 files, ~70 kB, ESM + CJS + `.d.ts`) is on the
registry at `https://www.npmjs.com/package/mauritania-geo` within a minute,
and `npm install mauritania-geo` works immediately.

Verify before publishing what would be shipped:

```bash
npm pack --dry-run   # lists every file in the tarball
```

### First release only

The very first publish of an unscoped package must also be done by the
package **owner** account (the account that will maintain it). If the name
is taken later, fall back to a scoped name (`@your-org/mauritania-geo`) and
update the README accordingly.

Trusted publishing (OIDC) can only be configured once the package exists, so
publish the first version with a token, then switch CI to OIDC.

---

## 2. PyPI — publishing `mauritania-geo`

### One-time setup

```bash
# Create an account at https://pypi.org/account/register/
# Then create an API token: https://pypi.org/manage/account/token/
#   (scope it to "project: mauritania-geo" after the first upload)
pip install --upgrade build twine
```

### Publish (manual)

```bash
cd packages/python
rm -rf dist/                       # never re-upload stale artifacts
python -m build                    # produces sdist + wheel
twine check dist/*                 # metadata sanity check
twine upload dist/*                # paste the API token as username "__token__"
```

Verify before uploading what the wheel contains:

```bash
python -m zipfile -l dist/mauritania_geo-*.whl | grep -E "py.typed|data.py"
```

### Trusted publishing (tokenless alternative)

PyPI supports **trusted publishing** via OpenID Connect: link this GitHub
repository at <https://pypi.org/manage/account/publishing/> (project name
`mauritania-geo`, owner/repo set to your fork, workflow filename
`release.yml`). The bundled `.github/workflows/release.yml` then publishes
without any stored secret.

---

## 3. Automated release (recommended)

`.github/workflows/release.yml` publishes **both** packages whenever a
version tag is pushed, using **trusted publishing (OIDC)** — no long-lived
registry tokens are stored in GitHub.

**One-time trusted-publisher setup** (required before the first tagged
release):

1. **npm** — <https://www.npmjs.com/package/mauritania-geo/access> →
   **Trusted publishing** → add a GitHub Actions publisher:
   - Organization/user: `cheikhEbeoumar`
   - Repository: `mauritania-geo`
   - Workflow filename: `release.yml`
   - Environment: *(leave blank)*
2. **PyPI** — <https://pypi.org/manage/project/mauritania-geo/settings/publishing/>
   → **Add a new publisher** → GitHub:
   - Owner: `cheikhEbeoumar`
   - Repository: `mauritania-geo`
   - Workflow: `release.yml`
   - Environment: *(leave blank)*

The npm job runs on Node 24 (npm ≥ 11.5.1) with
`permissions: id-token: write`; PyPI uses
`pypa/gh-action-pypi-publish`. No `NPM_TOKEN` / `PYPI_API_TOKEN` secrets are
needed. A granular npm token with **Bypass 2FA** is still required for
*manual* `npm publish` from your machine (see §1).

**Cutting a release:**

```bash
# 1. Bump BOTH versions in lockstep:
#    packages/typescript/package.json  →  "version": "1.1.0"
#    packages/python/pyproject.toml    →  version = "1.1.0"
# 2. Commit, then tag and push:
git add -A && git commit -m "release: v1.1.0"
git tag v1.1.0 && git push origin main v1.1.0
```

The workflow re-runs the full test suites, checks that the tag matches the
package versions, builds, and uploads. Versions of the two packages are
always kept in lockstep because both wrap the same dataset snapshot.

### Versioning policy

| Change                                             | Bump    |
|----------------------------------------------------|---------|
| Data corrections (name, coordinate, P-code fixes)  | patch   |
| New divisions added by OCHA / new dataset snapshot | minor   |
| New API helpers                                    | minor   |
| Breaking API change                                | major   |

---

## 4. Checklist for a first release

- [ ] Placeholder `example` URLs replaced (see §0)
- [ ] `npm test` and `python -m unittest discover tests` green
- [ ] npm account created, email verified, Granular token (Read/Write + Bypass 2FA) ready for manual publishes
- [ ] PyPI account created, API token ready for the first manual upload
- [ ] Trusted publishers configured on npm and PyPI (repo `cheikhEbeoumar/mauritania-geo`, workflow `release.yml`) — no CI secrets needed
- [ ] `npm pack --dry-run` reviewed (only `dist/`, README, LICENSE ship)
- [ ] Tag pushed → both packages live → `npm install mauritania-geo` and
      `pip install mauritania-geo` now work for everyone
- [ ] Announce: npm page `https://www.npmjs.com/package/mauritania-geo`,
      PyPI page `https://pypi.org/project/mauritania-geo/`

---

## 5. Getting the library *without* the registries

For users who want the code before (or instead of) a registry release:

```bash
git clone https://github.com/cheikhEbeoumar/mauritania-geo.git
cd mauritania-geo

# Node.js / TypeScript — builds automatically on install
npm install ./packages/typescript

# Python
pip install ./packages/python
```

Both install-from-source paths are exercised in CI; the npm `prepare`
script compiles `dist/` on install, so no manual build step is needed.
