"""
template_panel.py
Top panel — displays parsed content of wpmz/template.kml.
Shows mission config, drone/payload info, and document metadata
as labelled field rows grouped into sections.
"""

from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import ttk

from app.kmz_parser import TemplateKMLData, MissionConfig
from app import theme as T


# ---------------------------------------------------------------------------
# Helper widgets
# ---------------------------------------------------------------------------

class _SectionHeader(tk.Frame):
    """Coloured bar with a section title."""

    def __init__(self, parent: tk.Widget, title: str, **kw):
        super().__init__(parent, bg=T.BG_HEADER, height=T.HEADER_H, **kw)
        self.pack_propagate(False)
        tk.Label(
            self, text=title.upper(), font=T.FONT_HEADER,
            bg=T.BG_HEADER, fg=T.FG_ACCENT, padx=T.PAD,
        ).pack(side=tk.LEFT, pady=0)


class _FieldRow(tk.Frame):
    """A label : value pair on one row."""

    def __init__(self, parent: tk.Widget, label: str, value: str,
                 label_width: int = 26, alt_row: bool = False):
        bg = T.BG_TREE_ALT if alt_row else T.BG_PANEL
        super().__init__(parent, bg=bg)

        tk.Label(
            self, text=label, font=T.FONT_LABEL,
            bg=bg, fg=T.FG_LABEL,
            width=label_width, anchor="e", padx=T.PAD_SMALL,
        ).pack(side=tk.LEFT)

        self._var = tk.StringVar(value=value)
        tk.Label(
            self, textvariable=self._var, font=T.FONT_VALUE,
            bg=bg, fg=T.FG_VALUE, anchor="w", padx=T.PAD_SMALL,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def set(self, value: str) -> None:
        self._var.set(value)


class _BadgeLabel(tk.Frame):
    """Small coloured badge for a status value."""

    def __init__(self, parent: tk.Widget, label: str, value: str,
                 badge_bg: str = T.BG_BADGE_GOOD, label_width: int = 26,
                 alt_row: bool = False):
        bg = T.BG_TREE_ALT if alt_row else T.BG_PANEL
        super().__init__(parent, bg=bg)

        tk.Label(
            self, text=label, font=T.FONT_LABEL,
            bg=bg, fg=T.FG_LABEL,
            width=label_width, anchor="e", padx=T.PAD_SMALL,
        ).pack(side=tk.LEFT)

        self._badge_bg = badge_bg
        self._badge = tk.Label(
            self, text=f"  {value}  ", font=T.FONT_BADGE,
            bg=badge_bg, fg=T.FG_BADGE,
            padx=2, pady=1,
        )
        self._badge.pack(side=tk.LEFT, padx=(T.PAD_SMALL, 0), pady=2)

    def set(self, value: str, badge_bg: str | None = None) -> None:
        self._badge.config(text=f"  {value}  ")
        if badge_bg:
            self._badge.config(bg=badge_bg)


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

class TemplatePanel(tk.Frame):
    """Scrollable panel showing wpmz/template.kml content."""

    _LABEL_W = 28   # character width of label column

    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent, bg=T.BG_PANEL, **kw)

        self._build_ui()
        self.clear()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load(self, data: TemplateKMLData) -> None:
        """Populate all fields from parsed TemplateKMLData."""
        mc = data.mission_config

        # Document metadata
        self._f_author.set(data.author or "—")
        self._f_create.set(self._fmt_wpml_time(data.create_time))
        self._f_update.set(self._fmt_wpml_time(data.update_time))
        self._f_namespace.set(data.wpml_namespace or "—")
        self._f_wpml_ver.set(data.wpml_version or "—")
        self._f_tpl_type.set(data.template_type or "—")
        self._f_tpl_id.set(data.template_id or "—")

        # Drone / payload
        drone = mc.drone_info
        if drone.drone_name:
            self._f_drone.set(
                f"{drone.drone_name}  (enum {drone.drone_enum_value}"
                + (f" / sub {drone.drone_sub_enum_value}" if drone.drone_sub_enum_value else "")
                + ")"
            )
        else:
            self._f_drone.set("—")

        payload = mc.payload_info
        if payload.payload_name:
            self._f_payload.set(
                f"{payload.payload_name}  (enum {payload.payload_enum_value}"
                + (f" / sub {payload.payload_sub_enum_value}" if payload.payload_sub_enum_value else "")
                + ")"
            )
        else:
            self._f_payload.set("—")

        # Mission config
        self._f_fly_mode.set(mc.fly_to_wayline_mode or "—")
        self._f_rc_lost_exit.set(mc.exit_on_rc_lost or "—")
        self._f_rc_lost_action.set(mc.execute_rc_lost_action or "—")
        self._f_takeoff_h.set(
            f"{mc.takeoff_security_height} m" if mc.takeoff_security_height else "—"
        )
        self._f_transit_spd.set(
            self._fmt_speed(mc.global_transitional_speed)
        )
        self._f_height_mode.set(mc.global_waypoint_height_mode or "—")
        self._f_turn_mode.set(mc.global_waypoint_turn_mode or "—")
        self._f_wp_speed.set(
            self._fmt_speed(mc.global_waypoint_speed)
        )

        # Finish action badge colour
        fa = (mc.finish_action or "").lower()
        if "gohome" in fa or "return" in fa:
            badge_bg = T.BG_BADGE_GOOD
        elif "hover" in fa or "noaction" in fa:
            badge_bg = T.BG_BADGE_WARN
        else:
            badge_bg = T.BG_BADGE_ERR
        self._b_finish.set(mc.finish_action or "—", badge_bg)

    def clear(self) -> None:
        """Reset all fields to em-dash placeholders."""
        placeholder = "—"
        for field_widget in self._all_fields:
            field_widget.set(placeholder)
        self._b_finish.set(placeholder, T.BG_PANEL)

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Scrollable canvas
        canvas = tk.Canvas(self, bg=T.BG_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._inner = tk.Frame(canvas, bg=T.BG_PANEL)
        self._canvas_window = canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        ))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            self._canvas_window, width=e.width
        ))
        # Mouse-wheel scrolling
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(
            -1 * (e.delta // 120), "units"
        ))

        self._all_fields: list = []
        lw = self._LABEL_W

        # ── Section: Document Metadata ────────────────────────────────
        _SectionHeader(self._inner, "Document Metadata").pack(fill=tk.X, pady=(0, 1))

        rows_meta = [
            ("Author",          "author"),
            ("Created",         "create"),
            ("Updated",         "update"),
            ("WPML Namespace",  "namespace"),
            ("WPML Version",    "wpml_ver"),
            ("Template Type",   "tpl_type"),
            ("Template ID",     "tpl_id"),
        ]
        for i, (label, key) in enumerate(rows_meta):
            f = _FieldRow(self._inner, label, "—", label_width=lw, alt_row=(i % 2 == 1))
            f.pack(fill=tk.X)
            setattr(self, f"_f_{key}", f)
            self._all_fields.append(f)

        # ── Section: Drone & Payload ──────────────────────────────────
        _SectionHeader(self._inner, "Drone & Payload").pack(fill=tk.X, pady=(T.PAD, 1))

        rows_hw = [
            ("Drone",   "drone"),
            ("Payload", "payload"),
        ]
        for i, (label, key) in enumerate(rows_hw):
            f = _FieldRow(self._inner, label, "—", label_width=lw, alt_row=(i % 2 == 1))
            f.pack(fill=tk.X)
            setattr(self, f"_f_{key}", f)
            self._all_fields.append(f)

        # ── Section: Mission Configuration ───────────────────────────
        _SectionHeader(self._inner, "Mission Configuration").pack(fill=tk.X, pady=(T.PAD, 1))

        # Fly-to-wayline mode
        f = _FieldRow(self._inner, "Fly to Wayline Mode", "—", label_width=lw, alt_row=False)
        f.pack(fill=tk.X)
        self._f_fly_mode = f
        self._all_fields.append(f)

        # Finish action — badge variant
        row_bg = T.BG_TREE_ALT
        finish_row = tk.Frame(self._inner, bg=row_bg)
        finish_row.pack(fill=tk.X)
        tk.Label(
            finish_row, text="Finish Action", font=T.FONT_LABEL,
            bg=row_bg, fg=T.FG_LABEL, width=lw, anchor="e", padx=T.PAD_SMALL,
        ).pack(side=tk.LEFT)
        self._b_finish = _BadgeLabel(
            finish_row, "", "—", badge_bg=T.BG_PANEL, label_width=0, alt_row=True
        )
        self._b_finish.pack(side=tk.LEFT)

        rows_mission = [
            ("Exit on RC Lost",        "rc_lost_exit",   2),
            ("RC Lost Action",         "rc_lost_action", 3),
            ("Takeoff Security Height","takeoff_h",      4),
            ("Global Transit Speed",   "transit_spd",    5),
            ("Global Height Mode",     "height_mode",    6),
            ("Global Turn Mode",       "turn_mode",      7),
            ("Global Waypoint Speed",  "wp_speed",       8),
        ]
        for label, key, i in rows_mission:
            f = _FieldRow(self._inner, label, "—", label_width=lw, alt_row=(i % 2 == 0))
            f.pack(fill=tk.X)
            setattr(self, f"_f_{key}", f)
            self._all_fields.append(f)

    @staticmethod
    def _fmt_speed(raw: str) -> str:
        if not raw:
            return "—"
        try:
            mps = float(raw)
            kmh = mps * 3.6
            return f"{mps:.2f} m/s ({kmh:.2f} km/h)"
        except ValueError:
            return raw

    @staticmethod
    def _fmt_wpml_time(raw: str) -> str:
        if not raw:
            return "—"

        value = raw.strip()
        try:
            ts = float(value)
        except ValueError:
            return value

        # DJI time fields are often Unix milliseconds.
        if abs(ts) > 1e11:
            ts = ts / 1000.0

        try:
            local_str = datetime.fromtimestamp(ts).strftime("%d/%m/%y %H:%M:%S")
        except (OverflowError, OSError, ValueError):
            return value

        return f"{value} ({local_str})"
