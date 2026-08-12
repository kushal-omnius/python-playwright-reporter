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
- Added `_collect_env_info()` — gathers Python version, platform, installed package
  versions (pytest, pytest-playwright, playwright), browsers inferred from node IDs,
  Base URL from pytest metadata, and reporter version. Result is passed as
  `html_data["environment"]` to populate the Overview tab's Environment card.
- `[chromium]` / `[firefox]` / `[webkit]` suffixes are now stripped from test titles
  at the data-conversion layer (via regex) so titles are clean in all views.
- `cspSafe: True` is always set in the `options` dict. This suppresses Google Fonts
  `<link>` tags in the generated HTML so the report opens without browser security
  warnings when accessed via a `file://` URL.

### `bridge.py`
- `generate_report()` accepts and threads an optional `output_dir` parameter down to
  `convert_pytest_json()`.
- Added `_inject_copy_buttons()` — post-processes the generated HTML to insert
  clipboard copy buttons next to every test title and spec file path. Buttons are
  hidden until the row is hovered; clicking copies the text and flashes a ✓ confirm.
  Event delegation at capture phase and `MutationObserver` re-injection keep buttons
  alive after the report's own JS replaces `.test-list-content` on tab/filter/sort.
  Fails silently so it can never break report generation.
- Added drag-to-resize panel handle (injected alongside copy buttons): a 5 px
  `#panel-resizer` div between the test list and detail panels, with CSS custom
  property `--list-panel-width` on `.master-detail-layout`. Drag to 200–700 px;
  double-click resets to 380 px.

### `plugin.py`
- `pytest_sessionfinish` now reads `config.option.output` (the pytest-playwright
  `--output` dir) and passes it to `bridge.generate_report()` as `output_dir`, so
  screenshots are embedded automatically without any extra configuration.
- Added `--smart-reporter-title` CLI flag for setting a custom report title.
- Both `output_dir` and `pytest_json` paths are resolved to absolute paths
  (`.resolve()`) before being handed to the bridge, making screenshot lookup reliable
  regardless of the working directory at `pytest_sessionfinish` time.

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
