"""
theme.py
Centralised colour and font constants for the KMZ Inspector UI.
Light technical theme.
"""

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
BG_ROOT        = "#f3f6fb"   # main window background
BG_PANEL       = "#ffffff"   # panel / frame background
BG_HEADER      = "#e7eef8"   # section header bar
BG_TREE        = "#ffffff"   # Treeview background
BG_TREE_SEL    = "#cfe2ff"   # Treeview selected row
BG_TREE_ALT    = "#f7f9fd"   # alternate row colour
BG_ENTRY       = "#f2f5fa"   # entry / text widget background
BG_BUTTON      = "#7fc2ff"   # primary button
BG_BUTTON_HOV  = "#99d0ff"   # primary button hover
BG_BADGE_GOOD  = "#2f8f4f"   # green badge
BG_BADGE_WARN  = "#b98600"   # amber badge
BG_BADGE_ERR   = "#b63a3a"   # red badge
BG_DIVIDER     = "#cfd8e6"   # separator / divider line
BG_STATUS      = "#e7eef8"   # status bar

FG_PRIMARY     = "#1b2430"   # primary text
FG_SECONDARY   = "#5f6f86"   # secondary / muted text
FG_ACCENT      = "#0066cc"   # accent / link colour
FG_VALUE       = "#243447"   # field value text
FG_LABEL       = "#58708d"   # field label text
FG_HEADER      = "#1b2430"   # section header text
FG_BADGE       = "#ffffff"   # badge text
FG_TREE_SEL    = "#ffffff"
FG_TREE        = "#223246"
FG_STATUS      = "#5f6f86"
FG_GOOD        = "#2f8f4f"
FG_WARN        = "#b98600"
FG_ERR         = "#b63a3a"

# ---------------------------------------------------------------------------
# Fonts  (family, size, weight)
# ---------------------------------------------------------------------------
# Use system monospace for values; use a clean sans for labels.
# On macOS "SF Pro" is available; falls back to Helvetica.

FONT_FAMILY_UI   = "Helvetica"
FONT_FAMILY_MONO = "Menlo"      # macOS; falls back gracefully on Windows

FONT_TITLE       = (FONT_FAMILY_UI,   13, "bold")
FONT_HEADER      = (FONT_FAMILY_UI,   11, "bold")
FONT_LABEL       = (FONT_FAMILY_UI,   10, "normal")
FONT_VALUE       = (FONT_FAMILY_MONO, 10, "normal")
FONT_SMALL       = (FONT_FAMILY_UI,    9, "normal")
FONT_BADGE       = (FONT_FAMILY_UI,    9, "bold")
FONT_STATUS      = (FONT_FAMILY_UI,    9, "normal")
FONT_TREE        = (FONT_FAMILY_MONO, 10, "normal")
FONT_TREE_HEAD   = (FONT_FAMILY_UI,   10, "bold")
FONT_BUTTON      = (FONT_FAMILY_UI,   10, "bold")

# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
WINDOW_MIN_W  = 1000
WINDOW_MIN_H  = 700
WINDOW_START  = "1200x920"
PAD           = 10
PAD_SMALL     = 5
PAD_LARGE     = 16
CORNER_RADIUS = 4      # for reference; ttk doesn't support rounded corners natively
ROW_HEIGHT    = 22
HEADER_H      = 32
STATUS_H      = 24
