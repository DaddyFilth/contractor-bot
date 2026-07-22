"""
Vercel entry point.

Vercel's Python runtime discovers the FastAPI ASGI app via the module-level
``app`` variable.  All requests are routed here by ``vercel.json``.
"""

import sys
import os

# Ensure the project root is on the path so ``main`` can be imported.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app  # noqa: F401, E402 — re-exported for Vercel ASGI detection
