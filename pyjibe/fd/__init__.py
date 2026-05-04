"""Force-distance analysis UI package.

This package intentionally avoids importing Qt-heavy modules at import time to
prevent circular imports with `pyjibe.registry` / `pyjibe.head`.
"""

from __future__ import annotations

__all__ = ["UiForceDistance"]


def __getattr__(name: str):
    if name == "UiForceDistance":
        from .main import UiForceDistance
        return UiForceDistance
    raise AttributeError(name)
