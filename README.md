# KMZ Inspector

A lightweight Tkinter desktop app for inspecting DJI WPML KMZ mission files.

## Structure

```
kmz_inspector/
├── kmz_inspector.py          # entry point
└── app/
    ├── __init__.py
    ├── app.py                # main window, toolbar, layout
    ├── kmz_parser.py         # ZIP extraction + XML parsing
    ├── template_panel.py     # top panel  — template.kml fields
    ├── waypoints_panel.py    # bottom panel — waypoints table + detail
    └── theme.py              # colours, fonts, layout constants
```

## Usage

```bash
# Launch with file picker
python kmz_inspector.py

# Pre-load a specific KMZ
python kmz_inspector.py path/to/mission.kmz
```

## GitHub Release On Tag

This repo includes a GitHub Actions workflow at [.github/workflows/release.yml](.github/workflows/release.yml).
When you push a tag like `v1.2.3`, GitHub will:

- Build Windows artifact (`KMZInspector-windows.zip`)
- Build macOS artifact (`KMZInspector-macos.zip`)
- Create/update the GitHub Release for that tag and attach both files

Commands to trigger a release build:

```bash
git add .
git commit -m "Prepare release v1.2.3"
git push origin main

git tag v1.2.3
git push origin v1.2.3
```

## Requirements

- Python 3.10+
- tkinter (included with standard Python on macOS and Windows)
- No third-party packages required

## KMZ Format

DJI WPML KMZ files are ZIP archives containing:

```
wpmz/
  template.kml    — mission metadata, drone/payload config
  waylines.wpml   — waypoint definitions with actions
```

## What's Displayed

**Top panel — template.kml**
- Document metadata (author, timestamps, WPML version, template type/ID)
- Drone identity (enum → human-readable name)
- Payload identity
- Full mission config (finish action, RC-lost behaviour, speeds, height mode, turn mode)

**Bottom panel — waylines.wpml**
- Mission config summary bar
- Waypoint table: index, lat, lon, altitude, altitude mode, speed, type, gimbal pitch, action count
- Detail pane (click any row): full coordinate data, all waypoint actions with parameters

Gimbal pitch display note:
- In the waypoint table, gimbal pitch is shown at the segment end waypoint (`actionGroupEndIndex`).
- This means the pitch shown on a row typically comes from the previous waypoint's action group when that group ends at the current waypoint.

## Button Guide

The toolbar includes six action buttons. Only **Open KMZ** is active at startup.
After a KMZ is loaded successfully, the other five toolbar buttons become available.

### 1) Open KMZ
- Label: `⊕ Open KMZ`
- What it does: Opens a file picker to select a `.kmz` file.
- Result: Parses the archive and populates both panels (`template.kml` and `waylines.wpml`).
- Tip: You can also launch from terminal with a file path argument:
  - `python kmz_inspector.py path/to/mission.kmz`

### 2) Reload
- Label: `↺ Reload`
- Availability: Enabled after a file is loaded.
- What it does: Re-reads the currently loaded KMZ from disk.
- Use when: The file was edited or replaced externally and you want fresh data in the UI.

### 3) Copy All
- Label: `⧉ Copy All`
- Availability: Enabled after a file is loaded.
- What it does: Copies a combined export of template metadata and waypoint data to clipboard.
- Result: You can paste into notes, issue reports, or chat for quick sharing.

### 4) Map View
- Label: `◉ Map View`
- Availability: Enabled after a file is loaded.
- What it does: Opens an interactive browser map with waypoint markers, a connected path line, and small side labels showing each waypoint number and altitude.

### 5) Google Earth
- Label: `🌍 Google Earth`
- Availability: Enabled after a file is loaded.
- What it does: Exports waypoints to a temporary `.kml` file and tries to open it directly in Google Earth Pro.
- Fallback: If Google Earth Pro is not installed, the app opens the generated KML with your default app.

### 6) View WPML
- Label: `≡ View WPML`
- Availability: Enabled after a file is loaded.
- What it does: Opens a separate window showing formatted raw `waylines.wpml` XML with line numbers and syntax coloring.
- In that window: Use **Copy To Clipboard** to copy the raw WPML text exactly as loaded.
