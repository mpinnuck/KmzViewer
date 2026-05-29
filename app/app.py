"""
app.py
Main application class — window setup, toolbar, layout, and
wires the parser to the two panels.
"""

from __future__ import annotations

from datetime import datetime
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path

from app.kmz_parser import KMZParser, KMZData
from app.template_panel import TemplatePanel
from app.waypoints_panel import WaypointsPanel
from app import theme as T


class KMZInspectorApp:

    APP_TITLE = "KMZ Inspector"
    APP_VERSION = "v1.0"

    def __init__(self, preload_path: str | None = None) -> None:
        self._root = tk.Tk()
        self._root.title(self.APP_TITLE)
        self._root.geometry(T.WINDOW_START)
        self._root.minsize(T.WINDOW_MIN_W, T.WINDOW_MIN_H)
        self._root.configure(bg=T.BG_ROOT)

        self._current_path: str | None = None
        self._current_data: KMZData | None = None
        self._preload_path = preload_path

        self._configure_ttk_styles()
        self._build_ui()
        self._center_window()

        if preload_path:
            self._root.after(100, lambda: self._open_file(preload_path))

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run(self) -> None:
        self._root.mainloop()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Toolbar ───────────────────────────────────────────────────
        toolbar = tk.Frame(self._root, bg=T.BG_HEADER, height=44)
        toolbar.pack(fill=tk.X, side=tk.TOP)
        toolbar.pack_propagate(False)

        right_box = tk.Frame(toolbar, bg=T.BG_HEADER)
        right_box.pack(side=tk.RIGHT, padx=T.PAD, pady=6)

        tk.Label(
            right_box,
            text=self.APP_VERSION,
            font=T.FONT_SMALL,
            bg=T.BG_HEADER,
            fg=T.FG_SECONDARY,
        ).pack(side=tk.RIGHT)

        # Open button
        open_btn = tk.Button(
            toolbar,
            text="  ⊕  Open KMZ",
            font=T.FONT_BUTTON,
            bg=T.BG_BUTTON, fg="#000000",
            activebackground=T.BG_BUTTON_HOV, activeforeground="#000000",
            relief="flat", bd=0, padx=T.PAD, pady=6,
            cursor="hand2",
            command=self._on_open_clicked,
        )
        open_btn.pack(side=tk.LEFT, padx=T.PAD, pady=6)
        open_btn.bind("<Enter>", lambda e: open_btn.config(bg=T.BG_BUTTON_HOV))
        open_btn.bind("<Leave>", lambda e: open_btn.config(bg=T.BG_BUTTON))

        # Reload button
        self._reload_btn = tk.Button(
            toolbar,
            text="  ↺  Reload",
            font=T.FONT_BUTTON,
            bg=T.BG_HEADER, fg=T.FG_SECONDARY,
            activebackground=T.BG_PANEL, activeforeground=T.FG_PRIMARY,
            relief="flat", bd=0, padx=T.PAD_SMALL, pady=6,
            cursor="hand2",
            command=self._on_reload_clicked,
            state=tk.DISABLED,
        )
        self._reload_btn.pack(side=tk.LEFT, padx=(0, T.PAD), pady=6)

        # Copy all button
        self._copy_btn = tk.Button(
            toolbar,
            text="  ⧉  Copy All",
            font=T.FONT_BUTTON,
            bg=T.BG_HEADER, fg=T.FG_SECONDARY,
            activebackground=T.BG_PANEL, activeforeground=T.FG_PRIMARY,
            relief="flat", bd=0, padx=T.PAD_SMALL, pady=6,
            cursor="hand2",
            command=self._on_copy_clicked,
            state=tk.DISABLED,
        )
        self._copy_btn.pack(side=tk.LEFT, padx=(0, T.PAD), pady=6)

        # File path label
        self._path_var = tk.StringVar(value="No file loaded")
        tk.Label(
            toolbar,
            textvariable=self._path_var,
            font=T.FONT_SMALL,
            bg=T.BG_HEADER, fg=T.FG_SECONDARY,
            anchor="w",
        ).pack(side=tk.LEFT, padx=T.PAD, fill=tk.X, expand=True)

        # File size badge
        self._size_var = tk.StringVar(value="")
        self._size_badge = tk.Label(
            right_box,
            textvariable=self._size_var,
            font=T.FONT_BADGE,
            bg=T.BG_BADGE_GOOD, fg=T.FG_BADGE,
            padx=8, pady=2,
        )
        self._size_badge.pack(side=tk.RIGHT, padx=(0, T.PAD), pady=2)
        self._size_badge.pack_forget()   # hidden until file loaded

        # ── Main area: vertical paned window ─────────────────────────
        paned = tk.PanedWindow(
            self._root, orient=tk.VERTICAL,
            bg=T.BG_DIVIDER, sashwidth=5, sashrelief="flat",
        )
        paned.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Top panel — template.kml
        top_container = tk.Frame(paned, bg=T.BG_PANEL)
        self._add_panel_header(top_container, "template.kml  —  Mission Metadata")
        self._template_panel = TemplatePanel(top_container)
        self._template_panel.pack(fill=tk.BOTH, expand=True)
        paned.add(top_container, minsize=160, stretch="always")

        # Bottom panel — waylines.wpml
        bottom_container = tk.Frame(paned, bg=T.BG_PANEL)
        self._add_panel_header(bottom_container, "waylines.wpml  —  Waypoints")
        self._waypoints_panel = WaypointsPanel(bottom_container)
        self._waypoints_panel.pack(fill=tk.BOTH, expand=True)
        paned.add(bottom_container, minsize=200, stretch="always")

        # Set initial sash position after window is drawn
        self._root.update_idletasks()
        try:
            total_h = max(paned.winfo_height(), 1)
            # Keep all top metadata rows visible on launch.
            top_h = min(460, total_h - 200)
            paned.sash_place(0, 0, top_h)
        except tk.TclError:
            pass

        # ── Status bar ────────────────────────────────────────────────
        status_bar = tk.Frame(self._root, bg=T.BG_STATUS, height=T.STATUS_H)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self._status_var = tk.StringVar(value="Ready  —  open a .kmz file to begin")
        tk.Label(
            status_bar,
            textvariable=self._status_var,
            font=T.FONT_STATUS,
            bg=T.BG_STATUS, fg=T.FG_STATUS,
            anchor="w", padx=T.PAD,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Archive members count
        self._members_var = tk.StringVar(value="")
        tk.Label(
            status_bar,
            textvariable=self._members_var,
            font=T.FONT_STATUS,
            bg=T.BG_STATUS, fg=T.FG_STATUS,
            anchor="e", padx=T.PAD,
        ).pack(side=tk.RIGHT)

    @staticmethod
    def _add_panel_header(parent: tk.Widget, title: str) -> None:
        bar = tk.Frame(parent, bg=T.BG_ROOT, height=3)
        bar.pack(fill=tk.X)

    # ------------------------------------------------------------------
    # File open / reload
    # ------------------------------------------------------------------

    def _on_open_clicked(self) -> None:
        path = filedialog.askopenfilename(
            title="Open KMZ File",
            filetypes=[("KMZ files", "*.kmz"), ("All files", "*.*")],
        )
        if path:
            self._open_file(path)

    def _on_reload_clicked(self) -> None:
        if self._current_path:
            self._open_file(self._current_path)

    def _on_copy_clicked(self) -> None:
        if not self._current_data:
            self._status("Nothing to copy yet")
            return

        text = self._build_clipboard_export(self._current_data)
        self._root.clipboard_clear()
        self._root.clipboard_append(text)
        self._root.update()
        self._status("Copied template data and waypoint list to clipboard")

    def _open_file(self, path: str) -> None:
        self._status("Parsing…")
        self._root.update_idletasks()

        data: KMZData = KMZParser.parse(path)

        if data.error:
            messagebox.showerror("KMZ Inspector", f"Failed to open file:\n{data.error}")
            self._status(f"Error: {data.error}")
            return

        self._current_path = path
        self._current_data = data
        self._path_var.set(path)

        # Size badge
        self._size_var.set(f"  {data.file_size_kb} KB  ")
        self._size_badge.pack(side=tk.RIGHT, padx=T.PAD, pady=8)

        # Populate panels
        if data.template:
            self._template_panel.load(data.template)
        if data.waylines:
            self._waypoints_panel.load(data.waylines)

        # Status bar
        wp_count = len(data.waylines.waypoints) if data.waylines else 0
        self._status(
            f"Loaded  {Path(path).name}  —  {wp_count} waypoints  —  "
            f"{len(data.members)} archive member(s)"
        )
        self._members_var.set("  |  ".join(data.members))

        # Enable reload
        self._reload_btn.config(state=tk.NORMAL, fg=T.FG_ACCENT)
        self._copy_btn.config(state=tk.NORMAL, fg=T.FG_ACCENT)

        # Update window title
        self._root.title(f"{self.APP_TITLE}  —  {Path(path).name}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _status(self, message: str) -> None:
        self._status_var.set(message)
        self._root.update_idletasks()

    @staticmethod
    def _fmt_wpml_time(raw: str) -> str:
        if not raw:
            return "—"

        value = raw.strip()
        try:
            ts = float(value)
        except ValueError:
            return value

        if abs(ts) > 1e11:
            ts = ts / 1000.0

        try:
            local_str = datetime.fromtimestamp(ts).strftime("%d/%m/%y %H:%M:%S")
        except (OverflowError, OSError, ValueError):
            return value

        return f"{value} ({local_str})"

    @staticmethod
    def _fmt_speed_with_kmh(raw: str) -> str:
        if not raw:
            return "—"
        try:
            mps = float(raw)
            return f"{mps:.2f} m/s ({mps * 3.6:.2f} km/h)"
        except (ValueError, TypeError):
            return raw

    def _build_clipboard_export(self, data: KMZData) -> str:
        tpl = data.template
        wl = data.waylines

        lines: list[str] = []
        lines.append(f"{self.APP_TITLE} {self.APP_VERSION}")
        lines.append(f"File: {data.file_path}")
        lines.append("")
        lines.append("[Template Panel]")

        if tpl:
            mc = tpl.mission_config
            lines.extend([
                f"Author: {tpl.author or '—'}",
                f"Created: {self._fmt_wpml_time(tpl.create_time)}",
                f"Updated: {self._fmt_wpml_time(tpl.update_time)}",
                f"WPML Namespace: {tpl.wpml_namespace or '—'}",
                f"WPML Version: {tpl.wpml_version or '—'}",
                f"Template Type: {tpl.template_type or '—'}",
                f"Template ID: {tpl.template_id or '—'}",
                f"Drone: {mc.drone_info.drone_name or '—'}",
                f"Payload: {mc.payload_info.payload_name or '—'}",
                f"Fly to Wayline Mode: {mc.fly_to_wayline_mode or '—'}",
                f"Finish Action: {mc.finish_action or '—'}",
                f"Exit on RC Lost: {mc.exit_on_rc_lost or '—'}",
                f"RC Lost Action: {mc.execute_rc_lost_action or '—'}",
                f"Takeoff Security Height: {mc.takeoff_security_height + ' m' if mc.takeoff_security_height else '—'}",
                f"Global Transit Speed: {self._fmt_speed_with_kmh(mc.global_transitional_speed)}",
                f"Global Height Mode: {mc.global_waypoint_height_mode or '—'}",
                f"Global Turn Mode: {mc.global_waypoint_turn_mode or '—'}",
                f"Global Waypoint Speed: {self._fmt_speed_with_kmh(mc.global_waypoint_speed)}",
            ])
        else:
            lines.append("No template data")

        lines.append("")
        lines.append("[Waypoints]")
        lines.append("Index\tLatitude\tLongitude\tAltitude (m)\tAlt Mode\tSpeed\tType\tGimbal\tActions")

        if wl and wl.waypoints:
            for wp in wl.waypoints:
                try:
                    alt_str = f"{float(wp.altitude):.1f}" if wp.altitude else "—"
                except ValueError:
                    alt_str = wp.altitude or "—"
                lines.append(
                    "\t".join([
                        str(wp.index),
                        wp.latitude or "—",
                        wp.longitude or "—",
                        alt_str,
                        wp.altitude_mode or "—",
                        self._fmt_speed_with_kmh(wp.speed),
                        wp.waypoint_type or "—",
                        f"{wp.gimbal_pitch_angle}°" if wp.gimbal_pitch_angle else "—",
                        str(len(wp.actions)),
                    ])
                )
        else:
            lines.append("No waypoint data")

        return "\n".join(lines)

    def _center_window(self) -> None:
        self._root.update_idletasks()

        width = self._root.winfo_width()
        height = self._root.winfo_height()
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()

        x = max((screen_w - width) // 2, 0)
        y = max((screen_h - height) // 2, 0)
        self._root.geometry(f"{width}x{height}+{x}+{y}")

    def _configure_ttk_styles(self) -> None:
        style = ttk.Style(self._root)
        style.theme_use("default")
        style.configure(
            "Vertical.TScrollbar",
            background=T.BG_PANEL,
            troughcolor=T.BG_ROOT,
            arrowcolor=T.FG_SECONDARY,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=T.BG_PANEL,
            troughcolor=T.BG_ROOT,
            arrowcolor=T.FG_SECONDARY,
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Vertical.TScrollbar",
            background=[("active", T.BG_ENTRY)],
        )
        style.map(
            "Horizontal.TScrollbar",
            background=[("active", T.BG_ENTRY)],
        )
