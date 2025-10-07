from __future__ import annotations
import os
import tempfile
from workspace_fs import safe_join, sanitize_filename, human_size


def test_safe_join_basic():
    with tempfile.TemporaryDirectory() as td:
        p = safe_join(td, "sub/dir")
        assert p.startswith(os.path.abspath(td))


def test_safe_join_escape():
    with tempfile.TemporaryDirectory() as td:
        try:
            safe_join(td, "../etc/passwd")
        except Exception:
            pass
        else:
            raise AssertionError("path escape not blocked")


def test_sanitize_and_human_size():
    assert sanitize_filename("a/b:c\\d.txt") == "a_b_c_d.txt"
    assert human_size(1536).endswith("KB")


if __name__ == "__main__":
    test_safe_join_basic()
    test_safe_join_escape()
    test_sanitize_and_human_size()
    print("workspace_fs tests passed")
