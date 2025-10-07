from __future__ import annotations
import os
from typing import Any, Dict

from workspace_fs import sanitize_filename


def ensure_unique_name(dir_path: str, name: str) -> str:
    base = os.path.splitext(name)[0]
    ext = os.path.splitext(name)[1]
    cand = name
    i = 1
    while os.path.exists(os.path.join(dir_path, cand)):
        cand = f"{base}-{i}{ext}"
        i += 1
    return cand


def enforce_max_size(file_obj: Any, cap_bytes: int) -> None:
    try:
        pos = file_obj.file.tell()
        file_obj.file.seek(0, os.SEEK_END)
        size = file_obj.file.tell()
        file_obj.file.seek(pos, os.SEEK_SET)
        if size > cap_bytes:
            raise ValueError("File too large")
    except Exception:
        # best-effort: cannot determine size reliably; skip
        pass


def save_upload(dest_dir: str, upload: Any, *, max_bytes: int = 25 * 1024 * 1024, unique: bool = True, sanitize: bool = True) -> Dict[str, Any]:
    """Save a web upload-like object with attributes .filename, .file, .content_type.

    Returns: dict with rel, name, size, content_type
    """
    os.makedirs(dest_dir, exist_ok=True)
    name = getattr(upload, "filename", None) or "upload.bin"
    if sanitize:
        name = sanitize_filename(name)
    if unique:
        name = ensure_unique_name(dest_dir, name)

    size = 0
    dest = os.path.join(dest_dir, name)
    with open(dest, "wb") as out:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("File too large")
            out.write(chunk)
    content_type = getattr(upload, "content_type", "") or ""
    return {"rel": name, "name": name, "size": size, "content_type": content_type}
