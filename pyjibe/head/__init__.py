"""Main application package.

Keep imports lazy to avoid circular imports when other modules import
`pyjibe.head.*` utilities (e.g. custom widgets) while `pyjibe.head.main` pulls
in the registry.
"""

from __future__ import annotations

__all__ = ["PyJibe"]


def __getattr__(name: str):
    if name == "PyJibe":
        from .main import PyJibe
        return PyJibe
    raise AttributeError(name)
