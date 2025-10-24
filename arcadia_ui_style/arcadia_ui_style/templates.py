from __future__ import annotations

"""Legacy compatibility wrapper.

All implementation has moved to templates_v2. This module re-exports the
public API to preserve import paths for consuming apps.
"""

from .templates_v2 import ensure_templates as ensure_templates  # re-export

__all__ = ["ensure_templates"]
