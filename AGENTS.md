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
- **Interface Translations (`craft-i18n`)**:
  - Apps transitioning to the shared `storytold/craft-i18n` translation catalog (such as `wordcraft` starting in v0.11.0) pin a commit in `craft-i18n.rev`.
  - Their build script (`crates/ui-egui/build.rs`) embeds translations at compile time via `CRAFT_I18N_DIR`.
  - If `CRAFT_I18N_DIR` is unset during `cargo build`, the interface defaults to English only. Specs for such apps must pull `storytold/craft-i18n` as a Source, extract it in `%prep`, and set `export CRAFT_I18N_DIR=$PWD/craft-i18n` and `export CRAFT_I18N_REQUIRED=1` in `%build`.

---

## 2. Directory & Tooling Layout

```
.
├── *.spec                     # 13 RPM spec files (one per application)
├── trigger_build.sh           # Trigger SCM Git builds in Copr for spec(s)
├── submit_to_copr.sh          # One-click mass submitter for Fedora Copr
├── update_specs.sh            # Automated spec updater with nfpm change detection
├── check_external_hash.sh     # Inspect & align embedded craft-fonts and craft-i18n pins
├── fetch_things.sh            # Version checker, drift detector & source fetcher
├── fetch_nfpm.sh              # Mass-downloader for upstream packaging/linux/nfpm.yaml
├── reference/
│   └── upstream-nfpm/         # Cached upstream nfpm.yaml files for reference
├── README.md                  # Human-facing project overview and Copr build guide
└── AGENT.md                   # Agent maintenance guide (this file)
```

---

## 3. Maintenance Scripts

### Automated Version Updates (`update_specs.sh`)
The primary workflow for updating specs is automated via `update_specs.sh`:
```bash
# Check all apps and auto-update any with new upstream releases (if nfpm.yaml unchanged):
./update_specs.sh

# Run dry-run check without modifying files:
./update_specs.sh --dry-run

# Target specific app(s):
./update_specs.sh photocraft
```
**Decision Flow**:
- **If `nfpm.yaml` is unchanged**: It updates `Version:`, keeps `%autochangelog`, updates the cached reference, and runs `rpmlint`.
- **If `nfpm.yaml` CHANGED**: It stops, alerts with `[ACTION REQUIRED]`, prints the `nfpm.yaml` diff, and stages the new file as `reference/upstream-nfpm/<app>-nfpm.yaml.new` for the agent or user to inspect and update dependencies.

### Checking Upstream Versions & Drift (`fetch_things.sh`)
```bash
# Compare local spec versions against latest upstream GitHub tags:
./fetch_things.sh --versions

# Validate all upstream source tarball URLs and detect version drift:
./fetch_things.sh --check
```

### Checking & Updating Embedded External Assets (`check_external_hash.sh`)
External assets embedded via Git commit pins (`storytold/craft-fonts` via `%global craft_fonts_commit` and `storytold/craft-i18n` via `%global craft_i18n_commit`) are inspected and updated together:
```bash
# Check all apps for both font and i18n commit drift:
./check_external_hash.sh

# Display full 40-character commit hashes:
./check_external_hash.sh --verbose

# Check only fonts or only i18n:
./check_external_hash.sh --fonts
./check_external_hash.sh --i18n

# Automatically update drifted specs to match upstream pins:
./check_external_hash.sh --update
```

### Refreshing Upstream NFPM Packaging References (`fetch_nfpm.sh`)
Each upstream repository contains `packaging/linux/nfpm.yaml`, which specifies upstream dependencies, descriptions, and file maps.
```bash
# Refresh all 13 cached nfpm.yaml files:
./fetch_nfpm.sh
```
Cached reference files are stored in `reference/upstream-nfpm/<app>-nfpm.yaml`. Consult these whenever upstream alters dependencies or runtime requirements.

---

## 4. How to Update an Application Spec Manually (When NFPM Changes)

When `update_specs.sh` reports `[ACTION REQUIRED]` for an application:

1. **Inspect the NFPM Diff**:
   ```bash
   diff -u reference/upstream-nfpm/<app>-nfpm.yaml reference/upstream-nfpm/<app>-nfpm.yaml.new
   ```
   Check if upstream changed:
   - Rust MSRV (`rust-version` in `Cargo.toml`)
   - Direct or dlopened runtime dependencies (`Requires:` or `Recommends:`)
   - New binary targets or renamed desktop/mime files

2. **Edit the Spec File (`<app>.spec`)**:
   - Update `Version: <new_version>`
   - Reset `Release: 1%{?dist}`
   - Adjust `Requires:`, `Recommends:`, or build flags if upstream changed them.
   - Note: Changelogs use the `%autochangelog` macro, so manual changelog entries in the spec are not required.

3. **Promote the Reference File**:
   ```bash
   mv reference/upstream-nfpm/<app>-nfpm.yaml.new reference/upstream-nfpm/<app>-nfpm.yaml
   ```

4. **Verify the Updated Spec**:
   ```bash
   # 1. Check syntax and Fedora RPM guidelines
   rpmlint <app>.spec

   # 2. Verify upstream Source0 archive can be resolved and downloaded
   spectool -g -S <app>.spec

   # 3. Verify suite status with maintenance script
   ./fetch_things.sh --check
   ```

5. **Commit Your Changes**:
   ```bash
   git add <app>.spec reference/upstream-nfpm/
   git commit -m "chore(<app>): update to <new_version>"
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
