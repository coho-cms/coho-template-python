"""
Reads of your own, built on the generated ones.

Regeneration never touches this file, and a schema change that removes something these reads
use fails this library's type check rather than an app at runtime.
"""

from __future__ import annotations

from .coho import AnyEntry, Coho


def homepage(coho: Coho) -> AnyEntry | None:
    """
    An example of a read of your own: the home page, and everything it links to two levels
    deep, in one request. Replace it with yours, or remove it.
    """
    return coho.by_slug("home-page", depth=2)
