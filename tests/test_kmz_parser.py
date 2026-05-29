import unittest

from app.kmz_parser import KMZParser


class ParseWaylinesTests(unittest.TestCase):
    def test_waypoint_fallback_fields_are_parsed(self) -> None:
        raw = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.5">
  <Document>
    <wpml:missionConfig>
      <wpml:globalWaypointSpeed>7.5</wpml:globalWaypointSpeed>
    </wpml:missionConfig>
    <Folder>
      <Placemark>
        <wpml:index>1</wpml:index>
        <Point>
          <coordinates>-1.23,52.34</coordinates>
        </Point>
        <wpml:executeHeight>43.2</wpml:executeHeight>
        <wpml:heightMode>relativeToStartPoint</wpml:heightMode>
        <wpml:useGlobalSpeed>true</wpml:useGlobalSpeed>
        <wpml:waypointGimbalPitchAngle>-45</wpml:waypointGimbalPitchAngle>
      </Placemark>
    </Folder>
  </Document>
</kml>
'''

        waylines = KMZParser._parse_waylines(raw)

        self.assertEqual(len(waylines.waypoints), 1)
        waypoint = waylines.waypoints[0]
        self.assertEqual(waypoint.altitude, "43.2")
        self.assertEqual(waypoint.altitude_mode, "relativeToStartPoint")
        self.assertEqual(waypoint.speed, "7.5")
        self.assertEqual(waypoint.gimbal_pitch_angle, "-45")

    def test_waypoint_prefers_coordinate_altitude_when_present(self) -> None:
        raw = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="http://www.dji.com/wpmz/1.0.2">
  <Document>
    <Folder>
      <Placemark>
        <wpml:index>2</wpml:index>
        <Point>
          <coordinates>-1.23,52.34,80.0</coordinates>
        </Point>
        <wpml:executeHeight>43.2</wpml:executeHeight>
        <wpml:waypointSpeed>6</wpml:waypointSpeed>
        <wpml:gimbalPitchAngle>-30</wpml:gimbalPitchAngle>
      </Placemark>
    </Folder>
  </Document>
</kml>
'''

        waylines = KMZParser._parse_waylines(raw)
        waypoint = waylines.waypoints[0]

        self.assertEqual(waypoint.altitude, "80.0")
        self.assertEqual(waypoint.speed, "6")
        self.assertEqual(waypoint.gimbal_pitch_angle, "-30")


if __name__ == "__main__":
    unittest.main()