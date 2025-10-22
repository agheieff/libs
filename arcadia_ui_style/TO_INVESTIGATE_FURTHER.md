Sticky footer not applied in test_app

Observation
- test_app pages still do not pin the footer to the bottom on short content after the recent style changes.

Notes
- The sticky footer CSS (flex column layout) is injected inside the generated _header.html in ensure_templates.
- ensure_templates only rewrites _header.html when a set of conditions trigger (needs_write).
- Existing projects (like test_app) may already have a header that passes those checks, so the new CSS wasn’t written.

Hypothesis
- The gating logic prevented updating _header.html, leaving old CSS in place; without the global flex layout, #arcadia-content won’t expand and the footer won’t stick to the page bottom.

Next steps
- Loosen needs_write conditions or version the header block and rewrite when version mismatch.
- Alternatively, move the layout CSS into /ui-static/arcadia_theme.css so apps get it without header rewrite.
