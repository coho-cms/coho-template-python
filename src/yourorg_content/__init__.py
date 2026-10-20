"""
Typed content, generated from Coho CMS.

`coho/` is generated from the project's content types: after a schema change, run
`uv run coho-codegen pull` and `uv run coho-codegen generate`, and never edit it by hand.
Your own reads go in `reads.py`, beside it.
"""

# Every generated type, and the clients. A star import, so a type added to the project needs
# no change here; `coho/__init__.py` lists what it exports.
from .coho import *  # noqa: F403
from .reads import homepage as homepage
