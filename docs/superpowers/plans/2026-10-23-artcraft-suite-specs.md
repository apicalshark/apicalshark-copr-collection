# Artcraft Suite Fedora RPM Specs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create Fedora RPM spec files and maintenance scripts for all 13 Storytold Artcraft suite applications to compile from source via rpkg for Fedora Copr.

**Architecture:** Each application in the Artcraft suite (`photocraft`, `pdfcraft`, `filmcraft`, `wordcraft`, `lightcraft`, `vectorcraft`, `effectcraft`, `cadcraft`, `gridcraft`, `designcraft`, `deckcraft`, `soundcraft`, `figcraft`) gets its own standalone `.spec` file in the repository root. Each spec pulls upstream source code from GitHub release tags, compiles using `cargo build --release --locked -p <app> -p <app>-cli`, installs the desktop file, icons from `assets/app-icon/hicolor`, MIME definitions, and AppStream metainfo, and validates them via `desktop-file-validate` and `appstreamcli`. A `fetch_things.sh` script queries upstream repositories, tracks versions, and tests source retrieval with spectool.

**Tech Stack:** RPM Spec (Fedora packaging guidelines), Rust/Cargo, rpkg, spectool, rpmlint, Bash.

**Spec:** Converting all 13 Artcraft suite applications into compile-from-source Fedora RPM spec files suitable for rpkg and Fedora Copr builds.

## Global Constraints

- Compile from source using cargo/rust (no repackaged prebuilt binary tarball installs).
- Spec templates follow Fedora packaging guidelines: proper licenses, clean descriptions, exact dependencies, AppStream/desktop validation in `%check`.
- Applications with audio capabilities (`filmcraft`, `effectcraft`, `deckcraft`, `soundcraft`) require `pkgconfig(alsa)` at build time and `alsa-lib` runtime requirements.
- Wayland, X11, and GPU libraries loaded dynamically at runtime are explicitly declared in `Requires:` and `Recommends:`.
- Include `fetch_things.sh` to automate querying releases, checking tags, and validating download URLs.

## Review Focus

1. Source0 archive naming: `#/%{name}-%{version}.tar.gz` must unpack to `%{name}-%{version}`.
2. Icons installation: `assets/app-icon/hicolor` correctly copied to `%{_datadir}/icons/hicolor/`.
3. Metainfo generation: sed substitution of `@VERSION@` and `@DATE@` from `packaging/linux/%{app_id}.metainfo.xml.in`.
4. Audio dependencies: ensure `pkgconfig(alsa)` and `alsa-lib` are only specified for audio-enabled apps.
5. Rpmlint validation: all 13 `.spec` files pass `rpmlint` without fatal errors.

---

### Task 1: Create `fetch_things.sh` utility script

**Files:**
- Create: `fetch_things.sh`

**Interfaces:**
- Produces: Executable Bash script `fetch_things.sh` supporting `--check`, `--versions`, and `--download [app]`.

- [ ] **Step 1: Write `fetch_things.sh`**
Implement the script to iterate through the 13 craft apps, query the GitHub API for latest release tags, display a summary table, and support testing source download via `spectool -gS`.

- [ ] **Step 2: Make executable and test run**
Run: `chmod +x fetch_things.sh && ./fetch_things.sh --versions`
Expected: Lists all 13 apps with their current release versions.

- [ ] **Step 3: Commit**
Run: `git add fetch_things.sh && git commit -m "feat: add fetch_things.sh helper script"`

---

### Task 2: Create Graphic & Image Specs (`photocraft`, `lightcraft`, `vectorcraft`, `cadcraft`)

**Files:**
- Create: `photocraft.spec`
- Create: `lightcraft.spec`
- Create: `vectorcraft.spec`
- Create: `cadcraft.spec`

- [ ] **Step 1: Write `photocraft.spec` (v0.14.0)**
Configure build with `cargo build --release --locked -p photocraft -p photocraft-cli`. Install binary, desktop, mime, metainfo, icons.

- [ ] **Step 2: Write `lightcraft.spec` (v0.13.0)**
Configure build with `cargo build --release --locked -p lightcraft -p lightcraft-cli`. Install binary, desktop, mime, metainfo, icons.

- [ ] **Step 3: Write `vectorcraft.spec` (v0.16.0)**
Configure build with `cargo build --release --locked -p vectorcraft -p vectorcraft-cli`. Install binary, desktop, mime, metainfo, icons.

- [ ] **Step 4: Write `cadcraft.spec` (v0.12.0)**
Configure build with `cargo build --release --locked -p cadcraft -p cadcraft-cli`. Install binary, desktop, mime, metainfo, icons.

- [ ] **Step 5: Verify specs with rpmlint**
Run: `rpmlint photocraft.spec lightcraft.spec vectorcraft.spec cadcraft.spec`
Expected: 0 errors.

- [ ] **Step 6: Commit**
Run: `git add photocraft.spec lightcraft.spec vectorcraft.spec cadcraft.spec && git commit -m "feat: add photocraft, lightcraft, vectorcraft, cadcraft specs"`

---

### Task 3: Create Document, Publishing & Spreadsheet Specs (`pdfcraft`, `wordcraft`, `gridcraft`, `designcraft`, `figcraft`)

**Files:**
- Create: `pdfcraft.spec`
- Create: `wordcraft.spec`
- Create: `gridcraft.spec`
- Create: `designcraft.spec`
- Create: `figcraft.spec`

- [ ] **Step 1: Write `pdfcraft.spec` (v0.13.0)**
Configure build with `cargo build --release --locked -p pdfcraft -p pdfcraft-cli`. Recommend `cups-client`.

- [ ] **Step 2: Write `wordcraft.spec` (v0.10.0)**
Configure build with `cargo build --release --locked -p wordcraft -p wordcraft-cli`.

- [ ] **Step 3: Write `gridcraft.spec` (v0.11.1)**
Configure build with `cargo build --release --locked -p gridcraft -p gridcraft-cli`.

- [ ] **Step 4: Write `designcraft.spec` (v0.12.0)**
Configure build with `cargo build --release --locked -p designcraft -p designcraft-cli`.

- [ ] **Step 5: Write `figcraft.spec` (v0.10.0)**
Configure build with `cargo build --release --locked -p figcraft -p figcraft-cli`.

- [ ] **Step 6: Verify specs with rpmlint**
Run: `rpmlint pdfcraft.spec wordcraft.spec gridcraft.spec designcraft.spec figcraft.spec`
Expected: 0 errors.

- [ ] **Step 7: Commit**
Run: `git add pdfcraft.spec wordcraft.spec gridcraft.spec designcraft.spec figcraft.spec && git commit -m "feat: add pdfcraft, wordcraft, gridcraft, designcraft, figcraft specs"`

---

### Task 4: Create Audio & Video Specs (`filmcraft`, `effectcraft`, `deckcraft`, `soundcraft`)

**Files:**
- Create: `filmcraft.spec`
- Create: `effectcraft.spec`
- Create: `deckcraft.spec`
- Create: `soundcraft.spec`

- [ ] **Step 1: Write `filmcraft.spec` (v0.12.0)**
Add `BuildRequires: pkgconfig(alsa)`, `Requires: alsa-lib`. Build `filmcraft` and `filmcraft-cli`.

- [ ] **Step 2: Write `effectcraft.spec` (v0.16.0)**
Add `BuildRequires: pkgconfig(alsa)`, `Requires: alsa-lib`. Build `effectcraft` and `effectcraft-cli`.

- [ ] **Step 3: Write `deckcraft.spec` (v0.10.0)**
Add `BuildRequires: pkgconfig(alsa)`, `Requires: alsa-lib`. Build `deckcraft` and `deckcraft-cli`.

- [ ] **Step 4: Write `soundcraft.spec` (v0.12.1)**
Add `BuildRequires: pkgconfig(alsa)`, `Requires: alsa-lib`. Recommends `pipewire-alsa or alsa-plugins-pulseaudio`. Build `soundcraft` and `soundcraft-cli`.

- [ ] **Step 5: Verify specs with rpmlint**
Run: `rpmlint filmcraft.spec effectcraft.spec deckcraft.spec soundcraft.spec`
Expected: 0 errors.

- [ ] **Step 6: Commit**
Run: `git add filmcraft.spec effectcraft.spec deckcraft.spec soundcraft.spec && git commit -m "feat: add filmcraft, effectcraft, deckcraft, soundcraft specs"`

---

### Task 5: Documentation & End-to-End Spectool Check

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update `README.md`**
Document all 13 specs, build prerequisites in Copr (enabling internet access for cargo dependency resolution), local testing using `rpkg local` and `spectool`, and usage of `fetch_things.sh`.

- [ ] **Step 2: Run rpmlint and spectool check across all specs**
Run `rpmlint *.spec` and test `spectool -g -S deckcraft.spec` (or sample spec) to verify Source0 resolves and fetches properly.

- [ ] **Step 3: Commit**
Run: `git add README.md && git commit -m "docs: update README with artcraft specs documentation and build instructions"`
