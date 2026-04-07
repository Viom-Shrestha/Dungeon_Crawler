#Author Viom Shrestha
"""Backwards-compatible GUI entrypoint.

The implementation now lives in MVC modules under `src/mvc/`.
"""

from mvc.controller import DungeonCrawlerController, main


class DungeonCrawlerGUI(DungeonCrawlerController):
    """Compatibility alias for older imports."""

