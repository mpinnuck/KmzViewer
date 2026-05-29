
"""
KMZ Inspector
Entry point — run this file to launch the app.

Usage:
    # Activate virtual environment
    source .venv/bin/activate

    # Build app (Apple Silicon / arm64)
    /Users/markpinnuck/Dev/GitHub/KmzViewer/.venv/bin/python -m PyInstaller --clean --noconfirm kmz_inspector.spec

    # Run app
    python kmz_inspector.py
    python kmz_inspector.py path/to/mission.kmz   # optional pre-load
"""

import sys
from app.app import KMZInspectorApp


def main() -> None:
    preload_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = KMZInspectorApp(preload_path=preload_path)
    app.run()


if __name__ == "__main__":
    main()
