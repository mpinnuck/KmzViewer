import tkinter as tk
import unittest

from app.kmz_parser import MissionConfig, TemplateKMLData
from app.template_panel import TemplatePanel


class TemplatePanelTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
        self.root.withdraw()

    def tearDown(self) -> None:
        if hasattr(self, "root"):
            self.root.destroy()

    def test_load_does_not_raise_for_finish_action_badge(self) -> None:
        panel = TemplatePanel(self.root)

        panel.load(
            TemplateKMLData(
                mission_config=MissionConfig(
                    finish_action="goHome",
                    fly_to_wayline_mode="safely",
                )
            )
        )

        self.assertIn("goHome", panel._b_finish._badge.cget("text"))
        panel.clear()
        self.assertIn("—", panel._b_finish._badge.cget("text"))


if __name__ == "__main__":
    unittest.main()