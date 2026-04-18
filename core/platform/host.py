from __future__ import annotations

import platform


def platform_key() -> str:
    name = platform.system().lower()
    if "windows" in name:
        return "windows"
    if "linux" in name:
        return "linux"
    raise RuntimeError(f"Unsupported platform: {name}")
