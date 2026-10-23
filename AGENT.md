# AGENT.md — Maintainer Guide for Artcraft Suite Fedora RPM Specs

This document guides AI agents and maintainers on how to inspect, maintain, update, and build Fedora RPM specs for the **Storytold Artcraft Suite** in this Copr collection repository.

---

## 1. Repository Purpose & Architecture

This repository maintains compile-from-source Fedora RPM spec files for the 13 applications in the Storytold Artcraft suite (`https://github.com/orgs/storytold/repositories`).

### Key Principles
- **Compiled From Source**: All packages compile directly from official upstream GitHub release tarballs using `cargo build --release --locked -p <app> -p <app>-cli`. Precompiled binary tarballs are not used.
- **Dual Binaries**: Every app builds and installs two executables into `%{_bindir}`:
  - `%{name}` (the graphical desktop application)
  - `%{name}-cli` (the headless CLI tool / converter / command runner)
- **Standard Desktop Integration**:
  - Desktop entry: `%{_datadir}/applications/%{app_id}.desktop`
  - AppStream Metainfo: `%{_metainfodir}/%{app_id}.metainfo.xml` (templated from upstream `.metainfo.xml.in` via `sed`)
  - MIME type registration: `%{_datadir}/mime/packages/%{app_id}.xml`
  - Icons: standard `hicolor` hierarchy copied from `assets/app-icon/hicolor`
- **Dynamic Library Requirements**:
  - The Rust binaries link directly with `glibc` and `libgcc_s`.
  - Windowing (`x11`, `wayland`, `xkbcommon`) and GPU (`vulkan`, `egl`) runtimes are loaded via `dlopen()` at runtime. They are explicitly declared under `Requires:` and `Recommends:`.
- **Audio Apps**:
  - Four applications include audio features: `filmcraft`, `effectcraft`, `deckcraft`, and `soundcraft`.
  - These apps require `BuildRequires: pkgconfig(alsa)` and runtime `Requires: alsa-lib`.
  - `soundcraft` also declares `Recommends: (pipewire-alsa or alsa-plugins-pulseaudio)`.

---

## 2. Directory & Tooling Layout

```
.
├── *.spec                     # 13 RPM spec files (one per application)
├── fetch_things.sh            # Version checker, drift detector & source fetcher
├── fetch_nfpm.sh              # Mass-downloader for upstream packaging/linux/nfpm.yaml
├── reference/
│   └── upstream-nfpm/         # Cached upstream nfpm.yaml files for reference
├── README.md                  # Human-facing project overview and Copr build guide
└── AGENT.md                   # Agent maintenance guide (this file)
```

---

## 3. Maintenance Scripts

### Checking Upstream Versions & Drift
```bash
# Compare local spec versions against latest upstream GitHub tags:
./fetch_things.sh --versions

# Validate all upstream source tarball URLs and detect version drift:
./fetch_things.sh --check
```

### Refreshing Upstream NFPM Packaging References
Each upstream repository contains `packaging/linux/nfpm.yaml`, which specifies upstream dependencies, descriptions, and file maps.
```bash
# Refresh all 13 cached nfpm.yaml files:
./fetch_nfpm.sh
```
Cached reference files are stored in `reference/upstream-nfpm/<app>-nfpm.yaml`. Consult these whenever upstream alters dependencies or runtime requirements.

---

## 4. How to Update an Application Spec

When `./fetch_things.sh --versions` or `--check` reports that an application is outdated (`drift` or `stale`):

1. **Check Upstream Release Notes & NFPM**:
   ```bash
   ./fetch_nfpm.sh
   git diff reference/upstream-nfpm/<app>-nfpm.yaml
   ```
   Check if upstream changed:
   - Rust MSRV (`rust-version` in `Cargo.toml`)
   - Direct or dlopened runtime dependencies
   - New binary targets or renamed desktop files

2. **Edit the Spec File (`<app>.spec`)**:
   - Update `Version: <new_version>`
   - Reset `Release: 1%{?dist}`
   - Add a changelog entry at the bottom:
     ```spec
     %changelog
     * Fri Oct 23 2026 Your Name <your.email@example.com> - <new_version>-1
     - Update to <new_version>.
     ```

3. **Verify the Updated Spec**:
   ```bash
   # 1. Check syntax and Fedora RPM guidelines
   rpmlint <app>.spec

   # 2. Verify upstream Source0 archive can be resolved and downloaded
   spectool -g -S <app>.spec

   # 3. Verify suite status with maintenance script
   ./fetch_things.sh --check
   ```

4. **Test Local Build (Optional)**:
   ```bash
   rpkg local --spec <app>.spec
   ```

5. **Commit Your Changes**:
   ```bash
   git add <app>.spec reference/upstream-nfpm/
   git commit -m "chore(<app>): update to <new_version>"
   ```

---

## 5. Fedora Copr Configuration Rules

When triggering or configuring Copr builds for this repository:

1. **Enable Internet Access**:
   - In Copr: **Settings -> Build options -> Enable internet access during build**.
   - **Reason**: The build process executes `cargo build --release --locked`. Cargo needs access to `crates.io` and the Storytold `craft-libs` git repository to download and compile dependencies.
2. **SCM Build Settings**:
   - Point Copr SCM to the repository URL and branch `artcraft`.
   - Set the spec file path to the corresponding application (e.g. `photocraft.spec`).

---

## 6. Applications Reference Table

| Package | App ID | Upstream Repo | Audio (ALSA) | Special Notes |
|:---|:---|:---|:---:|:---|
| `photocraft` | `ai.storyteller.photocraft` | `storytold/photocraft` | No | Photo editor |
| `pdfcraft` | `ai.storyteller.pdfcraft` | `storytold/pdfcraft` | No | `Recommends: cups-client` |
| `filmcraft` | `ai.storyteller.filmcraft` | `storytold/filmcraft` | **Yes** | Video editor / scopes |
| `wordcraft` | `ai.storyteller.wordcraft` | `storytold/wordcraft` | No | Word processor |
| `lightcraft` | `ai.storyteller.lightcraft` | `storytold/lightcraft` | No | RAW photo developer |
| `vectorcraft` | `ai.storyteller.vectorcraft` | `storytold/vectorcraft` | No | Vector illustration |
| `effectcraft` | `ai.storyteller.effectcraft` | `storytold/effectcraft` | **Yes** | VFX / motion graphics |
| `cadcraft` | `ai.storyteller.cadcraft` | `storytold/cadcraft` | No | 2D CAD drafting |
| `gridcraft` | `ai.storyteller.gridcraft` | `storytold/gridcraft` | No | Spreadsheet editor |
| `designcraft` | `ai.storyteller.designcraft` | `storytold/designcraft` | No | Desktop publishing |
| `deckcraft` | `ai.storyteller.deckcraft` | `storytold/deckcraft` | **Yes** | Presentation editor |
| `soundcraft` | `ai.storyteller.soundcraft` | `storytold/soundcraft` | **Yes** | DAW; `Recommends: pipewire-alsa` |
| `figcraft` | `ai.storyteller.figcraft` | `storytold/figcraft` | No | Interface design & prototyping |
