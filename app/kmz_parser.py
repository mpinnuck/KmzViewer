"""
kmz_parser.py
Parses a DJI WPML KMZ file and returns structured data for display.

A DJI KMZ is a ZIP archive containing:
    wpmz/template.kml   - mission metadata / drone config
    wpmz/waylines.wpml  - waypoint definitions
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# XML namespace helpers
# ---------------------------------------------------------------------------

KML_NS  = "http://www.opengis.net/kml/2.2"
WPML_NS = "http://www.dji.com/wpmz/1.0.2"
WPML_NS_ALT = "http://www.dji.com/wpmz/1.0.5"  # newer firmware
WPML_NS_106 = "http://www.dji.com/wpmz/1.0.6"
WPML_NS_UAV = "http://www.uav.com/wpmz/1.0.2"


def _tag(ns: str, local: str) -> str:
    return f"{{{ns}}}{local}"


def _find_text(element: ET.Element, ns: str, *path: str) -> str:
    """Walk a chain of WPML-namespaced child tags and return stripped text, or ''."""
    node = element
    for part in path:
        found = node.find(_tag(ns, part))
        if found is None:
            for fallback_ns in (WPML_NS, WPML_NS_ALT, WPML_NS_106, WPML_NS_UAV):
                if fallback_ns == ns:
                    continue
                found = node.find(_tag(fallback_ns, part))
                if found is not None:
                    break
        if found is None:
            return ""
        node = found
    return (node.text or "").strip()


def _find_first_text(element: ET.Element, ns: str, *paths: tuple[str, ...]) -> str:
    """Return the first non-empty value from the provided tag paths."""
    for path in paths:
        value = _find_text(element, ns, *path)
        if value:
            return value
    return ""


def _detect_wpml_ns(root: ET.Element) -> str:
    """Return whichever WPML namespace variant is actually used in this document."""
    raw = ET.tostring(root, encoding="unicode")
    if WPML_NS_106 in raw:
        return WPML_NS_106
    if WPML_NS_UAV in raw:
        return WPML_NS_UAV
    if WPML_NS_ALT in raw:
        return WPML_NS_ALT
    return WPML_NS


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DroneInfo:
    drone_enum_value: str = ""
    drone_sub_enum_value: str = ""
    drone_name: str = ""        # human-readable label resolved from enum


@dataclass
class PayloadInfo:
    payload_enum_value: str = ""
    payload_sub_enum_value: str = ""
    payload_name: str = ""


@dataclass
class MissionConfig:
    fly_to_wayline_mode: str = ""
    finish_action: str = ""
    exit_on_rc_lost: str = ""
    execute_rc_lost_action: str = ""
    takeoff_security_height: str = ""
    global_transitional_speed: str = ""
    drone_info: DroneInfo = field(default_factory=DroneInfo)
    payload_info: PayloadInfo = field(default_factory=PayloadInfo)
    global_waypoint_height_mode: str = ""
    global_waypoint_turn_mode: str = ""
    global_waypoint_speed: str = ""


@dataclass
class WaypointAction:
    action_id: str = ""
    action_actuator_func: str = ""
    params: dict[str, str] = field(default_factory=dict)


@dataclass
class Waypoint:
    index: int = 0
    latitude: str = ""
    longitude: str = ""
    altitude: str = ""
    altitude_mode: str = ""
    speed: str = ""
    waypoint_type: str = ""
    gimbal_pitch_angle: str = ""
    use_global_speed: str = ""
    use_global_height_mode: str = ""
    actions: list[WaypointAction] = field(default_factory=list)


@dataclass
class TemplateKMLData:
    """Parsed content of wpmz/template.kml"""
    raw_xml: str = ""
    wpml_namespace: str = ""
    mission_config: MissionConfig = field(default_factory=MissionConfig)
    author: str = ""
    create_time: str = ""
    update_time: str = ""
    wpml_version: str = ""
    template_type: str = ""
    template_id: str = ""


@dataclass
class WaylinesData:
    """Parsed content of wpmz/waylines.wpml"""
    raw_xml: str = ""
    wpml_namespace: str = ""
    mission_config: MissionConfig = field(default_factory=MissionConfig)
    waypoints: list[Waypoint] = field(default_factory=list)


@dataclass
class KMZData:
    file_path: str = ""
    file_name: str = ""
    file_size_kb: float = 0.0
    members: list[str] = field(default_factory=list)
    template: Optional[TemplateKMLData] = None
    waylines: Optional[WaylinesData] = None
    error: str = ""


# ---------------------------------------------------------------------------
# Drone / Payload enum maps  (common DJI values)
# ---------------------------------------------------------------------------

DRONE_ENUM_MAP: dict[str, str] = {
    "67": "DJI Air 3",
    "77": "DJI Air 3S",
    "60": "DJI Mavic 3",
    "58": "DJI Mavic 3 Classic",
    "63": "DJI Mavic 3 Pro",
    "68": "DJI Mini 4 Pro",
    "44": "DJI Mini 3 Pro",
    "1":  "DJI Phantom 4",
    "66": "DJI Matrice 30",
    "73": "DJI Matrice 350 RTK",
}

PAYLOAD_ENUM_MAP: dict[str, str] = {
    "53": "DJI Air 3 Wide Camera",
    "54": "DJI Air 3 Tele Camera",
    "66": "DJI Air 3S Wide Camera",
    "42": "DJI Mavic 3 Wide",
    "43": "DJI Mavic 3 Tele",
    "52": "DJI Mavic 3 Classic Camera",
    "90042": "DJI Mini 4 Pro Camera",
}


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class KMZParser:

    @staticmethod
    def parse(kmz_path: str) -> KMZData:
        data = KMZData()
        data.file_path = kmz_path
        p = Path(kmz_path)
        data.file_name = p.name
        try:
            data.file_size_kb = round(p.stat().st_size / 1024, 1)
        except OSError:
            pass

        try:
            with zipfile.ZipFile(kmz_path, "r") as zf:
                data.members = zf.namelist()

                # --- template.kml ---
                template_member = KMZParser._find_member(zf, "template.kml")
                if template_member:
                    raw = zf.read(template_member).decode("utf-8", errors="replace")
                    data.template = KMZParser._parse_template(raw)
                else:
                    data.template = TemplateKMLData(raw_xml="(template.kml not found in archive)")

                # --- waylines.wpml ---
                waylines_member = KMZParser._find_member(zf, "waylines.wpml")
                if waylines_member:
                    raw = zf.read(waylines_member).decode("utf-8", errors="replace")
                    data.waylines = KMZParser._parse_waylines(raw)
                else:
                    data.waylines = WaylinesData(raw_xml="(waylines.wpml not found in archive)")

        except zipfile.BadZipFile:
            data.error = "Not a valid ZIP/KMZ file."
        except Exception as exc:
            data.error = f"Unexpected error: {exc}"

        return data

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_member(zf: zipfile.ZipFile, filename: str) -> Optional[str]:
        for name in zf.namelist():
            if name.endswith(filename):
                return name
        return None

    @staticmethod
    def _parse_template(raw_xml: str) -> TemplateKMLData:
        tpl = TemplateKMLData(raw_xml=raw_xml)
        try:
            root = ET.fromstring(raw_xml)
            ns = _detect_wpml_ns(root)
            tpl.wpml_namespace = ns
            doc = root.find(_tag(KML_NS, "Document"))
            if doc is None:
                doc = root

            tpl.author           = _find_text(doc, ns, "author")
            tpl.create_time      = _find_text(doc, ns, "createTime")
            tpl.update_time      = _find_text(doc, ns, "updateTime")
            tpl.wpml_version     = _find_text(doc, ns, "wpmlVersion")
            tpl.template_type    = _find_text(doc, ns, "templateType")
            tpl.template_id      = _find_text(doc, ns, "templateId")
            tpl.mission_config   = KMZParser._parse_mission_config(doc, ns)

        except ET.ParseError as exc:
            tpl.raw_xml = f"XML parse error: {exc}\n\n{raw_xml}"
        return tpl

    @staticmethod
    def _parse_waylines(raw_xml: str) -> WaylinesData:
        wl = WaylinesData(raw_xml=raw_xml)
        try:
            root = ET.fromstring(raw_xml)
            ns = _detect_wpml_ns(root)
            wl.wpml_namespace = ns
            doc = root.find(_tag(KML_NS, "Document"))
            if doc is None:
                doc = root

            wl.mission_config = KMZParser._parse_mission_config(doc, ns)

            folder = doc.find(_tag(KML_NS, "Folder"))
            if folder is None:
                folder = doc

            folder_execute_height_mode = _find_text(folder, ns, "executeHeightMode")

            for pm in folder.findall(_tag(KML_NS, "Placemark")):
                wp = KMZParser._parse_placemark(pm, ns, wl.mission_config, folder_execute_height_mode)
                wl.waypoints.append(wp)

            # Sort by index in case they're out of order
            wl.waypoints.sort(key=lambda w: w.index)

        except ET.ParseError as exc:
            wl.raw_xml = f"XML parse error: {exc}\n\n{raw_xml}"
        return wl

    @staticmethod
    def _parse_mission_config(doc: ET.Element, ns: str) -> MissionConfig:
        mc = MissionConfig()
        cfg_node = doc.find(_tag(ns, "missionConfig"))
        if cfg_node is None:
            for fallback_ns in (WPML_NS_ALT, WPML_NS_106, WPML_NS_UAV):
                cfg_node = doc.find(_tag(fallback_ns, "missionConfig"))
                if cfg_node is not None:
                    break
        if cfg_node is None:
            return mc

        mc.fly_to_wayline_mode        = _find_text(cfg_node, ns, "flyToWaylineMode")
        mc.finish_action              = _find_text(cfg_node, ns, "finishAction")
        mc.exit_on_rc_lost            = _find_text(cfg_node, ns, "exitOnRCLost")
        mc.execute_rc_lost_action     = _find_text(cfg_node, ns, "executeRCLostAction")
        mc.takeoff_security_height    = _find_text(cfg_node, ns, "takeOffSecurityHeight")
        mc.global_transitional_speed  = _find_text(cfg_node, ns, "globalTransitionalSpeed")
        mc.global_waypoint_height_mode = _find_text(cfg_node, ns, "globalWaypointHeightMode")
        mc.global_waypoint_turn_mode  = _find_text(cfg_node, ns, "globalWaypointTurnMode")
        mc.global_waypoint_speed      = _find_text(cfg_node, ns, "globalWaypointSpeed")

        # Drone info
        drone_node = cfg_node.find(_tag(ns, "droneInfo"))
        if drone_node is None:
            for fallback_ns in (WPML_NS_ALT, WPML_NS_106, WPML_NS_UAV):
                drone_node = cfg_node.find(_tag(fallback_ns, "droneInfo"))
                if drone_node is not None:
                    break
        if drone_node is not None:
            ev = _find_text(drone_node, ns, "droneEnumValue")
            sv = _find_text(drone_node, ns, "droneSubEnumValue")
            mc.drone_info = DroneInfo(
                drone_enum_value=ev,
                drone_sub_enum_value=sv,
                drone_name=DRONE_ENUM_MAP.get(ev, f"Unknown (enum {ev})"),
            )

        # Payload info
        payload_node = cfg_node.find(_tag(ns, "payloadInfo"))
        if payload_node is None:
            for fallback_ns in (WPML_NS_ALT, WPML_NS_106, WPML_NS_UAV):
                payload_node = cfg_node.find(_tag(fallback_ns, "payloadInfo"))
                if payload_node is not None:
                    break
        if payload_node is not None:
            ev = _find_text(payload_node, ns, "payloadEnumValue")
            sv = _find_text(payload_node, ns, "payloadSubEnumValue")
            mc.payload_info = PayloadInfo(
                payload_enum_value=ev,
                payload_sub_enum_value=sv,
                payload_name=PAYLOAD_ENUM_MAP.get(ev, f"Unknown (enum {ev})"),
            )

        return mc

    @staticmethod
    def _parse_placemark(pm: ET.Element, ns: str, mission_config: MissionConfig, default_altitude_mode: str = "") -> Waypoint:
        wp = Waypoint()

        idx_text = _find_text(pm, ns, "index")
        try:
            wp.index = int(idx_text)
        except ValueError:
            wp.index = 0

        # Coordinates live in <Point><coordinates>lon,lat,alt</coordinates></Point>
        # Some WPML files omit altitude there and store it in waypoint-specific tags.
        point = pm.find(_tag(KML_NS, "Point"))
        if point is not None:
            coords_text = _find_text(point, KML_NS, "coordinates")
            if coords_text:
                parts = coords_text.strip().split(",")
                if len(parts) >= 2:
                    wp.longitude = parts[0].strip()
                    wp.latitude  = parts[1].strip()
                if len(parts) >= 3:
                    wp.altitude  = parts[2].strip()

        wp.altitude = wp.altitude or _find_first_text(
            pm,
            ns,
            ("executeHeight",),
            ("waypointHeight",),
            ("ellipsoidHeight",),
            ("height",),
        )
        wp.altitude_mode = _find_first_text(
            pm,
            ns,
            ("waypointHeightMode",),
            ("heightMode",),
            ("altitudeMode",),
        )
        if not wp.altitude_mode:
            wp.altitude_mode = default_altitude_mode
        wp.speed = _find_first_text(
            pm,
            ns,
            ("waypointSpeed",),
            ("speed",),
        )
        wp.waypoint_type         = _find_text(pm, ns, "waypointType")
        wp.gimbal_pitch_angle = _find_first_text(
            pm,
            ns,
            ("waypointGimbalHeadingParam", "waypointGimbalPitchAngle"),
            ("waypointGimbalPitchAngle",),
            ("gimbalPitchAngle",),
            ("gimbalPitchRotateAngle",),
        )
        wp.use_global_speed      = _find_text(pm, ns, "useGlobalSpeed")
        wp.use_global_height_mode = _find_text(pm, ns, "useGlobalWaypointHeightMode")

        if not wp.speed and wp.use_global_speed.lower() == "true":
            wp.speed = mission_config.global_waypoint_speed

        # Actions
        action_group = pm.find(_tag(ns, "actionGroup"))
        if action_group is None:
            action_group = pm.find(_tag(WPML_NS_ALT, "actionGroup"))
        if action_group is not None:
            for action_node in action_group.findall(_tag(ns, "action")):
                wa = WaypointAction()
                wa.action_id = _find_text(action_node, ns, "actionId")
                wa.action_actuator_func = _find_text(action_node, ns, "actionActuatorFunc")
                actuator_params = action_node.find(_tag(ns, "actionActuatorFuncParam"))
                if actuator_params is None:
                    actuator_params = action_node.find(_tag(WPML_NS_ALT, "actionActuatorFuncParam"))
                if actuator_params is not None:
                    for child in actuator_params:
                        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        wa.params[local] = (child.text or "").strip()
                wp.actions.append(wa)

        return wp
