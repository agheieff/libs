# web-upload

Utilities for saving web uploads safely.

- `save_upload(dest_dir, upload, max_bytes=25MB, unique=True, sanitize=True)` writes the file and returns metadata `{rel, name, size, content_type}`.
- `ensure_unique_name(dir, name)` de-duplicates by appending `-N` before the extension.
- `enforce_max_size(file_obj, cap_bytes)` best-effort size guard.
- Uses `workspace_fs.sanitize_filename` to clean names.

Install (editable):
uv add -e ../libs/web_upload
