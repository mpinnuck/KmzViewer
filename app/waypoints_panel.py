"""
waypoints_panel.py
Bottom panel — displays parsed waypoints from wpmz/waylines.wpml.

Layout:
  ┌─ Mission Config summary bar ─────────────────────────────────────┐
  ├─ Waypoint table (Treeview) ──────────────────────────────────────┤
  └─ Detail pane (selected waypoint actions / full fields) ──────────┘
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.kmz_parser import WaylinesData, Waypoint, WaypointAction
from app import theme as T


# ---------------------------------------------------------------------------
# Column definitions for the main Treeview
# ---------------------------------------------------------------------------

_COLUMNS = [
    # (id,               heading,          width, anchor)
    ("index",            "#",              40,    tk.CENTER),
    ("latitude",         "Latitude",      110,    tk.CENTER),
    ("longitude",        "Longitude",     110,    tk.CENTER),
    ("altitude",         "Alt (m)",        70,    tk.CENTER),
    ("altitude_mode",    "Alt Mode",       78,    tk.CENTER),
    ("speed",            "Speed",         190,    tk.CENTER),
    ("waypoint_type",    "Type",           64,    tk.CENTER),
    ("gimbal_pitch",     "Gimbal °",       70,    tk.CENTER),
    ("actions",          "Actions",        65,    tk.CENTER),
]


def _fmt_altitude_m(raw: str) -> str:
    if not raw:
        return "—"
    try:
        return f"{float(raw):.1f} m"
    except (ValueError, TypeError):
        return f"{raw} m"


def _fmt_speed_with_kmh(raw: str) -> str:
    if not raw:
        return "—"
    try:
        mps = float(raw)
        kmh = mps * 3.6
        return f"{mps:.2f} m/s ({kmh:.2f} km/h)"
    except (ValueError, TypeError):
        return raw


# ---------------------------------------------------------------------------
# Helper: styled Treeview
# ---------------------------------------------------------------------------

def _build_treeview(parent: tk.Widget) -> ttk.Treeview:
    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "KMZ.Treeview",
        background=T.BG_TREE,
        foreground=T.FG_TREE,
        fieldbackground=T.BG_TREE,
        font=T.FONT_TREE,
        rowheight=T.ROW_HEIGHT,
        borderwidth=0,
    )
    style.configure(
        "KMZ.Treeview.Heading",
        background=T.BG_HEADER,
        foreground=T.FG_ACCENT,
        font=T.FONT_TREE_HEAD,
        relief="flat",
        borderwidth=0,
    )
    style.map(
        "KMZ.Treeview",
        background=[("selected", T.BG_TREE_SEL)],
        foreground=[("selected", T.FG_TREE_SEL)],
    )
    style.map(
        "KMZ.Treeview.Heading",
        background=[("active", T.BG_HEADER)],
    )

    cols = [c[0] for c in _COLUMNS]
    tv = ttk.Treeview(parent, columns=cols, show="headings", style="KMZ.Treeview",
                      selectmode="browse")

    for col_id, heading, width, anchor in _COLUMNS:
        tv.heading(col_id, text=heading)
        tv.column(col_id, width=width, minwidth=40, anchor=anchor, stretch=(col_id == "altitude_mode"))

    tv.tag_configure("odd",  background=T.BG_TREE)
    tv.tag_configure("even", background=T.BG_TREE_ALT)
    tv.tag_configure("action_gimbal", foreground=T.FG_GOOD)

    return tv


# ---------------------------------------------------------------------------
# Detail pane (actions for selected waypoint)
# ---------------------------------------------------------------------------

class _DetailPane(tk.Frame):
    """Shows full details / actions for the selected waypoint."""

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent, bg=T.BG_PANEL, **kw)

        # Header
        hdr = tk.Frame(self, bg=T.BG_HEADER, height=T.HEADER_H)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        self._title = tk.Label(
            hdr, text="WAYPOINT DETAIL", font=T.FONT_HEADER,
            bg=T.BG_HEADER, fg=T.FG_ACCENT, padx=T.PAD,
        )
        self._title.pack(side=tk.LEFT, pady=0)

        # Scrollable text area
        text_frame = tk.Frame(self, bg=T.BG_PANEL)
        text_frame.pack(fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        self._text = tk.Text(
            text_frame, bg=T.BG_ENTRY, fg=T.FG_VALUE,
            font=T.FONT_VALUE, wrap=tk.WORD,
            relief="flat", borderwidth=0,
            yscrollcommand=sb.set,
            state=tk.DISABLED,
            padx=T.PAD, pady=T.PAD_SMALL,
            cursor="arrow",
        )
        sb.config(command=self._text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure text tags for colouring
        self._text.tag_configure("label",   foreground=T.FG_LABEL,     font=T.FONT_LABEL)
        self._text.tag_configure("value",   foreground=T.FG_VALUE,     font=T.FONT_VALUE)
        self._text.tag_configure("section", foreground=T.FG_ACCENT,    font=T.FONT_HEADER)
        self._text.tag_configure("none",    foreground=T.FG_SECONDARY, font=T.FONT_LABEL)
        self._text.tag_configure("good",    foreground=T.FG_GOOD,      font=T.FONT_VALUE)
        self._text.tag_configure("warn",    foreground=T.FG_WARN,      font=T.FONT_VALUE)

    def show_waypoint(self, wp: Waypoint) -> None:
        self._title.config(text=f"WAYPOINT  {wp.index}  —  DETAIL")
        self._write(wp)

    def clear(self) -> None:
        self._title.config(text="WAYPOINT DETAIL")
        self._set_text("")
        self._append("  Select a waypoint row above to see full details.", "none")

    # ------------------------------------------------------------------

    def _write(self, wp: Waypoint) -> None:
        self._set_text("")

        def row(label: str, value: str, tag: str = "value"):
            self._append(f"  {label:<28}", "label")
            self._append(f"{value}\n", tag)

        self._append("  COORDINATES & ALTITUDE\n", "section")
        row("Latitude",           wp.latitude  or "—")
        row("Longitude",          wp.longitude or "—")
        row("Altitude",           _fmt_altitude_m(wp.altitude))
        row("Altitude Mode",      wp.altitude_mode or "—")

        self._append("\n  SPEED & BEHAVIOUR\n", "section")
        speed_str = _fmt_speed_with_kmh(wp.speed)
        try:
            spd = float(wp.speed)
            speed_tag = "good" if spd <= 15 else "warn"
        except (ValueError, TypeError):
            speed_tag = "value"
        row("Speed",              speed_str, speed_tag)
        row("Waypoint Type",      wp.waypoint_type or "—")
        gimbal_tag = "good" if wp.gimbal_pitch_source == "action" else "value"
        row("Gimbal Pitch",       f"{wp.gimbal_pitch_angle}°" if wp.gimbal_pitch_angle else "—", gimbal_tag)
        row("Use Global Speed",   wp.use_global_speed or "—")
        row("Use Global Height",  wp.use_global_height_mode or "—")

        if wp.actions:
            self._append(f"\n  ACTIONS  ({len(wp.actions)})\n", "section")
            for i, act in enumerate(wp.actions, start=1):
                self._append(f"\n  [{i}] Action ID {act.action_id} — ", "label")
                self._append(f"{act.action_actuator_func}\n", "value")
                for pname, pval in act.params.items():
                    self._append(f"       {pname:<26}", "label")
                    self._append(f"{pval}\n", "value")
        else:
            self._append("\n  ACTIONS\n", "section")
            self._append("  (none)\n", "none")

    def _set_text(self, content: str) -> None:
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        if content:
            self._text.insert(tk.END, content)
        self._text.config(state=tk.DISABLED)

    def _append(self, text: str, tag: str = "value") -> None:
        self._text.config(state=tk.NORMAL)
        self._text.insert(tk.END, text, tag)
        self._text.config(state=tk.DISABLED)


# ---------------------------------------------------------------------------
# Mission config summary bar
# ---------------------------------------------------------------------------

class _MissionSummaryBar(tk.Frame):
    """Compact one-line summary of mission config from waylines.wpml."""

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent, bg=T.BG_HEADER, height=28, **kw)
        self.pack_propagate(False)

        self._vars: dict[str, tk.StringVar] = {}

        pills = [
            ("Drone",        "drone"),
            ("Finish",       "finish"),
            ("RC Lost",      "rc_lost"),
            ("Transit Spd",  "transit"),
            ("Height Mode",  "height"),
        ]

        for label, key in pills:
            var = tk.StringVar(value="—")
            self._vars[key] = var
            pill = tk.Frame(self, bg=T.BG_HEADER)
            pill.pack(side=tk.LEFT, padx=(T.PAD, 0))
            tk.Label(pill, text=f"{label}:", font=T.FONT_SMALL,
                     bg=T.BG_HEADER, fg=T.FG_LABEL).pack(side=tk.LEFT)
            tk.Label(pill, textvariable=var, font=T.FONT_VALUE,
                     bg=T.BG_HEADER, fg=T.FG_VALUE).pack(side=tk.LEFT, padx=(2, 0))

        # Waypoint count badge (right-aligned)
        self._count_var = tk.StringVar(value="0 waypoints")
        tk.Label(
            self, textvariable=self._count_var,
            font=T.FONT_BADGE, bg=T.BG_BADGE_GOOD, fg=T.FG_BADGE,
            padx=8, pady=2,
        ).pack(side=tk.RIGHT, padx=T.PAD, pady=3)

    def update_from(self, data: WaylinesData) -> None:
        mc = data.mission_config
        self._count_var.set(f"{len(data.waypoints)} waypoints")

        di = mc.drone_info
        self._vars["drone"].set(di.drone_name if di.drone_name else "—")

        def _spd(raw: str) -> str:
            try:
                return f"{float(raw):.1f} m/s"
            except (ValueError, TypeError):
                return raw or "—"

        self._vars["finish"].set(mc.finish_action or "—")
        self._vars["rc_lost"].set(mc.execute_rc_lost_action or "—")
        self._vars["transit"].set(_spd(mc.global_transitional_speed))
        self._vars["height"].set(mc.global_waypoint_height_mode or "—")

    def clear(self) -> None:
        for v in self._vars.values():
            v.set("—")
        self._count_var.set("0 waypoints")


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

class WaypointsPanel(tk.Frame):
    """Bottom panel — waypoints table + detail pane."""

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent, bg=T.BG_PANEL, **kw)
        self._waypoints: list[Waypoint] = []
        self._build_ui()
        self.clear()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load(self, data: WaylinesData) -> None:
        """Populate table from WaylinesData."""
        self._waypoints = data.waypoints
        self._summary_bar.update_from(data)
        self._populate_table(data.waypoints)
        self._detail.clear()

    def clear(self) -> None:
        self._waypoints = []
        self._summary_bar.clear()
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._detail.clear()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Summary bar at top
        self._summary_bar = _MissionSummaryBar(self)
        self._summary_bar.pack(fill=tk.X)

        # Horizontal paned window: table left, detail right
        paned = tk.PanedWindow(
            self, orient=tk.HORIZONTAL,
            bg=T.BG_DIVIDER, sashwidth=4, sashrelief="flat",
        )
        paned.pack(fill=tk.BOTH, expand=True)

        # --- Left: Treeview + scrollbar ---
        tree_frame = tk.Frame(paned, bg=T.BG_PANEL)
        paned.add(tree_frame, minsize=400, stretch="always")

        # Section header
        hdr = tk.Frame(tree_frame, bg=T.BG_HEADER, height=T.HEADER_H)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="WAYPOINTS", font=T.FONT_HEADER,
            bg=T.BG_HEADER, fg=T.FG_ACCENT, padx=T.PAD,
        ).pack(side=tk.LEFT)

        # Treeview
        tv_container = tk.Frame(tree_frame, bg=T.BG_PANEL)
        tv_container.pack(fill=tk.BOTH, expand=True)

        self._tree = _build_treeview(tv_container)

        vsb = ttk.Scrollbar(tv_container, orient=tk.VERTICAL,   command=self._tree.yview)
        hsb = ttk.Scrollbar(tv_container, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT,  fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # --- Right: Detail pane ---
        self._detail = _DetailPane(paned)
        paned.add(self._detail, minsize=280, stretch="never")

        # Set initial split to 2/3 from the left edge after layout settles.
        def _set_initial_split_from_left(attempt: int = 0) -> None:
            try:
                total_w = paned.winfo_width()
                if total_w <= 1 and attempt < 5:
                    self.after(20, lambda: _set_initial_split_from_left(attempt + 1))
                    return

                sash_x = (2 * max(total_w, 1)) // 3
                paned.sash_place(0, sash_x, 0)
            except tk.TclError:
                pass

        self.after_idle(_set_initial_split_from_left)

    # ------------------------------------------------------------------
    # Table population
    # ------------------------------------------------------------------

    def _populate_table(self, waypoints: list[Waypoint]) -> None:
        for row in self._tree.get_children():
            self._tree.delete(row)

        for i, wp in enumerate(waypoints):
            tag = "even" if i % 2 == 0 else "odd"
            tags = [tag]
            if wp.gimbal_pitch_source == "action":
                tags.append("action_gimbal")
            speed_str = _fmt_speed_with_kmh(wp.speed)

            lat_str = f"{float(wp.latitude):.7f}"  if wp.latitude  else ""
            lon_str = f"{float(wp.longitude):.7f}" if wp.longitude else ""
            alt_str = f"{float(wp.altitude):.1f}" if wp.altitude else ""

            self._tree.insert(
                "", tk.END,
                iid=str(i),
                values=(
                    wp.index,
                    lat_str,
                    lon_str,
                    alt_str,
                    wp.altitude_mode or "—",
                    speed_str,
                    wp.waypoint_type or "—",
                    f"{wp.gimbal_pitch_angle}°" if wp.gimbal_pitch_angle else "—",
                    len(wp.actions) if wp.actions else 0,
                ),
                tags=tuple(tags),
            )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _on_select(self, _event: tk.Event) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(self._waypoints):
            self._detail.show_waypoint(self._waypoints[idx])
