# separate copy — modifications over upstream

This is a standalone copy of the `python/` folder from
[qa-gary-parker/playwright-smart-reporter](https://github.com/qa-gary-parker/playwright-smart-reporter),
maintained separately under the MIT licence.

## Changes relative to upstream (v1.0.8)

### `converter.py`
- Added `_screenshots_for_nodeid(output_dir, nodeid)` — scans the pytest-playwright
  artifact directory for PNG screenshots using the same nodeid-sanitisation formula
  as pytest-playwright's own `--output` folder naming.
- `convert_pytest_json()` now accepts an optional `output_dir` parameter; when
  supplied, failure screenshots are embedded as base64 data URIs in
  `attachments.screenshots` for each failed test.
- `enableGalleryView` is now set dynamically (`True` when any screenshots were found)
  instead of being hardcoded to `False`.

### `bridge.py`
- `generate_report()` accepts and threads an optional `output_dir` parameter down to
  `convert_pytest_json()`.
- Added `_inject_copy_buttons()` — post-processes the generated HTML to insert
  clipboard copy buttons next to every test title and spec file path. Buttons are
  hidden until the row is hovered; clicking copies the text and flashes a ✓ confirm.
  Fails silently so it can never break report generation.

### `plugin.py`
- `pytest_sessionfinish` now reads `config.option.output` (the pytest-playwright
  `--output` dir) and passes it to `bridge.generate_report()` as `output_dir`, so
  screenshots are embedded automatically without any extra configuration.

## Installation

```bash
pip install -e .
```
