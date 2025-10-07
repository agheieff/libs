from __future__ import annotations
import os
import tempfile

try:
    from openrouter import build_or_messages
except Exception:
    build_or_messages = None


def test_build_or_messages_inline():
    if build_or_messages is None:
        print("openrouter not importable; skipping")
        return
    msgs = [{"role": "user", "content": "See file"}]
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "note.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("hello")
        atts = [{"rel": "note.txt", "name": "note.txt", "size": 5, "content_type": "text/plain"}]
        def resolver(att):
            return p
        out = build_or_messages(msgs, attachments=atts, resolver=resolver)
        last = out[-1]
        content = last.get("content", [])
        assert any(part.get("type") == "text" for part in content)


if __name__ == "__main__":
    test_build_or_messages_inline()
    print("openrouter build_or_messages test passed")
