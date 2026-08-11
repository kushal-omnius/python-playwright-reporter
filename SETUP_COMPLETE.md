# separate copy — modifications over upstream

This is a standalone copy of the `python/` folder from
[qa-gary-parker/playwright-smart-reporter](https://github.com/qa-gary-parker/playwright-smart-reporter),
maintained separately under the MIT licence.


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

### `_bundled_dist/`
- Added the compiled JS generators and committed
  them to this repo. This makes the package self-contained when installed from
  GitHub — no separate download or build step is needed.
- To update: see the "Updating the bundled JS generators" section in
  [DEVELOPMENT.md](DEVELOPMENT.md).

## Installation

From this repo (local):
```bash
pip install -e .
```

From GitHub (e.g. as a dependency in another project):
```bash
pip install "python-playwright-reporter @ git+https://github.com/kushal-omnius/python-playwright-reporter.git"
```
