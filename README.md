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
