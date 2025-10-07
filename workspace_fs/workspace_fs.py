from __future__ import annotations
import os
import mimetypes
from typing import Tuple


def safe_join(root: str, rel: str) -> str:
    root_abs = os.path.abspath(root)
    dest = os.path.abspath(os.path.join(root_abs, rel or "."))
    if not dest.startswith(root_abs + os.sep) and dest != root_abs:
        raise ValueError("Invalid path")
    return dest


def sanitize_filename(name: str, *, allow_space: bool = True) -> str:
    base = os.path.basename(name or "")
    allowed = set("-_. ") if allow_space else set("-_.")
    out = ''.join(c if (c.isalnum() or c in allowed) else '_' for c in base).strip()
    return out or "file"


def guess_mime(name: str, fallback: str = "application/octet-stream") -> str:
    m, _ = mimetypes.guess_type(name)
    return m or fallback


def human_size(nbytes: int) -> str:
    try:
        n = float(nbytes)
    except Exception:
        return "unknown size"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "TB":
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{nbytes}B"
