# workspace-fs

Small filesystem helpers for web apps.

- `safe_join(root, rel)`: prevent directory traversal; returns an absolute path under `root`.
- `sanitize_filename(name, allow_space=True)`: strip path components and replace unsafe chars.
- `guess_mime(name, fallback='application/octet-stream')`.
- `human_size(nbytes)`: human-readable size.

Install (editable):
uv add -e ../libs/workspace_fs
