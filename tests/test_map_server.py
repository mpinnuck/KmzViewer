import unittest
from unittest.mock import Mock
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from app.map_server import MapServer
from app.app import KMZInspectorApp


class MapServerTests(unittest.TestCase):
    def test_serves_distinct_maps_only_while_running(self) -> None:
        server = MapServer()
        try:
            first = server.add("<html>first</html>")
            second = server.add("<html>second</html>")
            self.assertNotEqual(first, second)
            for url, expected in ((first, b"<html>first</html>"), (second, b"<html>second</html>")):
                with urlopen(url) as response:
                    self.assertEqual(response.read(), expected)
                    self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
                    self.assertEqual(response.headers["Cache-Control"], "no-store")

            with self.assertRaises(HTTPError) as unknown:
                urlopen(first + "unknown")
            self.assertEqual(unknown.exception.code, 404)

            with self.assertRaises(HTTPError) as wrong_host:
                urlopen(Request(first, headers={"Host": "example.com"}))
            self.assertEqual(wrong_host.exception.code, 403)
        finally:
            server.close()

        with self.assertRaises(URLError):
            urlopen(first, timeout=1)

    def test_map_close_returns_focus_on_tk_thread(self) -> None:
        app = KMZInspectorApp.__new__(KMZInspectorApp)
        app._root = Mock()
        app._map_server = Mock()
        app._map_server.consume_closed.side_effect = [False, True]

        app._check_map_closed()
        app._root.focus_force.assert_not_called()
        app._check_map_closed()
        app._root.deiconify.assert_called_once()
        app._root.lift.assert_called_once()
        app._root.focus_force.assert_called_once()
        self.assertEqual(app._root.after.call_count, 2)

    def test_map_close_notifications_require_valid_page_and_origin(self) -> None:
        server = MapServer()
        try:
            url = server.add("<html>map</html>")
            parts = urlsplit(url)
            origin = f"{parts.scheme}://{parts.netloc}"
            self.assertFalse(server.consume_closed())

            for path, request_origin, expected in (
                (url + "/closed", "https://example.com", 403),
                (origin + "/unknown/closed", origin, 404),
            ):
                request = Request(path, data=b"", headers={"Origin": request_origin})
                with self.assertRaises(HTTPError) as error:
                    urlopen(request)
                self.assertEqual(error.exception.code, expected)
                self.assertFalse(server.consume_closed())

            request = Request(url + "/closed", data=b"", headers={"Origin": origin})
            with urlopen(request) as response:
                self.assertEqual(response.status, 204)
            self.assertTrue(server.consume_closed())
            self.assertFalse(server.consume_closed())
        finally:
            server.close()


if __name__ == "__main__":
    unittest.main()
