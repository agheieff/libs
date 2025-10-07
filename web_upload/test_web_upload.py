from __future__ import annotations
import io
import os
import tempfile
from types import SimpleNamespace
from web_upload import save_upload


def test_save_upload_basic():
    with tempfile.TemporaryDirectory() as td:
        data = b"hello world"
        upload = SimpleNamespace(filename="t&e@s#t.txt", file=io.BytesIO(data), content_type="text/plain")
        meta = save_upload(td, upload, max_bytes=1024)
        assert meta["name"].endswith(".txt")
        dest = os.path.join(td, meta["name"]) 
        assert os.path.isfile(dest)
        assert meta["size"] == len(data)


if __name__ == "__main__":
    test_save_upload_basic()
    print("web_upload tests passed")
