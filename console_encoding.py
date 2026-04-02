"""Ensure stdout/stderr use UTF-8 on Windows so ₹, emoji, and JSON print safely."""
from __future__ import annotations

import sys
from typing import TextIO


def ensure_utf8_stdio() -> None:
    if sys.platform != "win32":
        return
    stream: TextIO
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError, TypeError):
            pass
