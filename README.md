# Artcraft RPM Spec Collection

This repository contains RPM spec files and utilities for packaging the complete [Artcraft suite](https://github.com/storytold) of native creative applications for Fedora Linux via [Fedora Copr](https://copr.fedorainfracloud.org/).

Each application is written in Rust, built with `cargo`, and packaged following modern Fedora packaging standards, including AppStream metadata validation and desktop file verification.

---

## Artcraft Suite Applications

| Application | Spec File | Version | App ID | Description |
| ----------- | --------- | ------- | ------ | ----------- |
| **Photocraft** | `photocraft.spec` | `0.14.0` | `ai.storyteller.photocraft` | Open-source native image editor |
| **PDFcraft** | `pdfcraft.spec` | `0.13.0` | `ai.storyteller.pdfcraft` | Open-source native PDF reader and editor |
| **Filmcraft** | `filmcraft.spec` | `0.12.0` | `ai.storyteller.filmcraft` | Open-source native non-linear video editor |
| **Wordcraft** | `wordcraft.spec` | `0.10.0` | `ai.storyteller.wordcraft` | Open-source native word processor |
| **Lightcraft** | `lightcraft.spec` | `0.13.0` | `ai.storyteller.lightcraft` | Open-source native photo library and raw developer |
| **Vectorcraft** | `vectorcraft.spec` | `0.16.0` | `ai.storyteller.vectorcraft` | Open-source native vector illustration editor |
| **Effectcraft** | `effectcraft.spec` | `0.16.0` | `ai.storyteller.effectcraft` | Open-source native motion graphics and visual effects compositor |
| **CADcraft** | `cadcraft.spec` | `0.12.0` | `ai.storyteller.cadcraft` | Open-source native CAD and drafting application |
| **Gridcraft** | `gridcraft.spec` | `0.11.1` | `ai.storyteller.gridcraft` | Open-source native spreadsheet application |
| **Designcraft** | `designcraft.spec` | `0.12.0` | `ai.storyteller.designcraft` | Open-source native desktop publishing and page layout application |
| **Deckcraft** | `deckcraft.spec` | `0.10.0` | `ai.storyteller.deckcraft` | Open-source native presentation and slide designer |
| **Soundcraft** | `soundcraft.spec` | `0.12.1` | `ai.storyteller.soundcraft` | Open-source native digital audio workstation |
| **Figcraft** | `figcraft.spec` | `0.10.0` | `ai.storyteller.figcraft` | Open-source native interface design and prototyping application |

---

## Fedora Copr Project Configuration & Mass Submission

### 1. One-Click Mass Submission with `submit_to_copr.sh`

An automated submission script `./submit_to_copr.sh` is provided to register all 13 packages into your Copr project:

```bash
# Register all 13 packages into your Copr project (e.g., 'artcraft'):
./submit_to_copr.sh artcraft

# Register AND immediately queue builds:
./submit_to_copr.sh artcraft --build
```

### 2. Manual Copr Project Configuration

When setting up builds in Fedora Copr via the web UI or CLI:

1. **Network Access Requirement**:
   > **CRITICAL**: In Copr project settings (**Settings -> Build options**), ensure **"Enable internet access during build"** is checked (`--enable-net on`).
   > 
   > The Artcraft applications are written in Rust; Cargo resolves dependencies from crates.io and GitHub at compile time during `%build`. Without network access in the build chroot, the build will fail.

2. **SCM Package Settings**:
   - **Source type**: SCM (Git)
   - **Clone URL**: `https://github.com/apicalshark/apicalshark-copr-collection.git`
   - **Committish / Branch**: `artcraft` (or `main` once merged)
   - **Spec file**: `<app_name>.spec` (e.g. `photocraft.spec`, `deckcraft.spec`)
   - **SRPM build method**: `rpkg`

---

## Local Building & Testing Workflow

### 1. Prerequisites

Install the required RPM packaging and build tools:

```bash
sudo dnf install rpkg spectool rpmlint cargo rust gcc gcc-c++ desktop-file-utils appstream
```

### 2. Downloading Sources

Download the upstream release tarball for a given spec file using `spectool`:

```bash
spectool -g -S deckcraft.spec
```

### 3. Validating Spec Files

Check all spec files or a specific spec file for packaging errors and warnings using `rpmlint`:

```bash
# Lint all spec files
rpmlint *.spec

# Lint a single spec
rpmlint deckcraft.spec
```

### 4. Building Locally

Build an RPM package locally in your environment using `rpkg`:

```bash
rpkg local --spec deckcraft.spec
```

---

## Maintenance & Update Utilities

### 1. `update_specs.sh` (Automated Version Updates)

The `update_specs.sh` utility checks upstream GitHub releases and automatically updates spec files:
- **If `packaging/linux/nfpm.yaml` is unchanged**: automatically updates `Version:`, keeps the `%autochangelog` macro, updates the reference cache, and validates via `rpmlint`.
- **If `nfpm.yaml` has changed**: flags `[ACTION REQUIRED]`, prints the packaging diff, and stages the new file as `reference/upstream-nfpm/<app>-nfpm.yaml.new` so maintainers can update dependencies or build options manually.

```bash
# Check and auto-update all 13 specs:
./update_specs.sh

# Dry-run mode:
./update_specs.sh --dry-run
```

### 2. `fetch_things.sh`

The included `fetch_things.sh` helper utility provides quick tools to query upstream GitHub releases, verify archive URLs, and download sources.

- **Check version alignment between GitHub and local specs**:
  ```bash
  ./fetch_things.sh --versions
  ```
  Lists upstream GitHub latest releases, current spec versions, and status (`ok` or `stale`).

- **Verify all upstream archives and spec alignment**:
  ```bash
  ./fetch_things.sh --check
  ```
  Performs HTTP HEAD requests against all 13 GitHub source tarballs and checks that specs match.

- **Download source tarball for an application**:
  ```bash
  ./fetch_things.sh --download deckcraft
  ```
  Fetches the corresponding source archive directly into the current directory.

### 3. `fetch_nfpm.sh`

Downloads the latest `packaging/linux/nfpm.yaml` for all 13 apps into `reference/upstream-nfpm/` for reference and diff detection.

```bash
./fetch_nfpm.sh
```
