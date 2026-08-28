# Changelog

All notable changes to `python-playwright-reporter` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

---

## [1.1.6] — 2026-08-28

### Changed

- **Flaky Tests dedicated view**: flaky tests are no longer represented by a
  sidebar mini-stat card. Instead a "Flaky Tests" navigation tab (with a yellow
  badge count) appears between Tests and Trends. The view lists every flaky test
  as a card showing title, file location, and a flakiness-score bar. An empty
  state is shown when no flaky tests were detected. Clicking a card navigates to
  the test detail in the Tests view.

---

## [1.1.5] — 2026-08-28

### Added

- **SKIPPED stat card in sidebar**: a muted-colour "Skipped" button now appears in
  the sidebar stats row (alongside Passed / Failed / Flaky) whenever the run contains
  at least one skipped test. Clicking it filters the test list to skipped tests via
  `filterByStatus('skipped')`, consistent with the existing mini-bar row behaviour.

---

## [1.1.4] — 2026-08-27

### Added

- **Dedicated skip-reason card for skipped tests**: skipped tests now show a
  `⏭ Skip Reason` section in their detail panel instead of the red `⚠ Error`
  box used by failed tests. The section uses muted styling (grey border/text)
  to visually distinguish an intentional skip from an unexpected failure. The
  "Skipped: " prefix from pytest's longrepr is stripped so only the human-readable
  reason is shown. Both the server-rendered card and the client-side fallback
  renderer apply this treatment.

---

## [1.1.3] — 2026-08-27

### Fixed

- **Skipped tests missing from By Spec group header**: the file-group header in the
  By Spec tab counted only passed and failed tests. Files containing only skipped
  tests showed no stats at all. A `skipped` count is now computed and rendered with
  its own muted-colour badge alongside the passed/failed badges.
- **`expectedStatus` always `"passed"` for skipped tests**: the Playwright data format
  uses `"skipped"` for tests that were intentionally skipped. The converter now sets
  `expectedStatus: "skipped"` when the pytest outcome is `"skipped"` and `"passed"`
  otherwise.

---

## [1.1.2] — 2026-08-12

### Fixed

- **Duplicate option crash when coexisting with upstream package**: after the v1.1.1
  entry point rename, both plugins load cleanly but both attempt to register
  `--smart-reporter` / `--smart-reporter-output`, causing pytest to raise
  `ValueError: option names {'--smart-reporter'} already added`. Each `addoption`
  call is now wrapped in a `try/except ValueError` so whichever plugin registers
  the options first wins and the second silently skips.

---

## [1.1.1] — 2026-08-12

### Fixed

- **Plugin entry point conflict with upstream `playwright-smart-reporter-python`**: both
  packages previously registered their pytest plugin under the same `pytest11` key
  (`playwright_smart_reporter`). When both are installed, Python's entry point resolution
  picked only one — usually the upstream — causing our plugin to never load and
  `--smart-reporter-title` to be treated as an unknown file path. The entry point key is
  now `python_playwright_reporter` (unique to this package); no change to CLI flags or
  user-facing behaviour.

---

## [1.1.0] — 2026-08-12

### Added

- **Environment card** in the Overview tab showing Python version, platform,
  installed package versions (pytest, pytest-playwright, playwright), detected
  browsers (inferred from raw node IDs before suffix stripping), and Base URL
  (from pytest-metadata via pytest-json-report `environment` dict).
- **Copy-to-clipboard buttons** on every test title and test file label.
  Buttons appear on row hover and flash green on success. Uses
  `document.execCommand('copy')` (synchronous, works on `file://` protocol).
  Event delegation at capture phase survives DOM re-renders caused by the
  report's own tab/filter/sort JS; `MutationObserver` re-injects buttons when
  `.test-list-content` is rebuilt.
- **Drag-to-resize panel handle** between the test list and detail panels.
  Drag to any width between 200 px and 700 px; double-click resets to 380 px.
  Implemented via a 5 px `#panel-resizer` div and a CSS custom property
  `--list-panel-width` on `.master-detail-layout`.
- **Reporter version** displayed at the bottom of the sidebar footer, read at
  report-generation time via `importlib.metadata.version('python-playwright-reporter')`.
- **`cspSafe` enabled by default** for Python-generated reports — skips the
  Google Fonts `<link>` tags and uses system fonts instead. Eliminates the
  "Unsafe attempt to load URL file://" console error that Chrome/Chromium throws
  when opening a `file://` report that references external HTTPS resources.

### Changed

- **Top bar redesign**: removed logo subtitle; breadcrumb detail is
  single-line with `overflow: hidden` / `text-overflow: ellipsis`; timestamp
  shows test-run start time (`startTime` from data) with a tooltip; theme label
  hidden to save space.
- **By-Spec expand icon**: changed icon from `▼` to `▶`. The icon now rotates
  90° clockwise when a file group is expanded (pointing down) and returns to 0°
  when collapsed (pointing right), giving clear visual feedback on toggle state.
- **`[chromium]` / `[firefox]` / `[webkit]` suffix** stripped from test titles
  at the data-conversion layer (`converter.py`) rather than via a client-side
  regex, so titles are clean throughout the data and in all views.
- **`plugin.py`**: `output_dir` and `pytest_json` paths are now resolved to
  absolute paths (`.resolve()`) before being passed to the bridge, making
  screenshot lookup reliable regardless of the working directory at
  `pytest_sessionfinish` time.

### Fixed

- **Copy buttons lost after re-render**: the report's own JS replaces
  `.test-list-content` on every tab switch, filter, or sort, destroying any
  previously attached event listeners. Fixed with document-level event
  delegation (capture phase) and `data-copy` attribute storage so clicks work
  on any button regardless of when it was created.
- **Breadcrumbs wrapping to multiple lines**: `.breadcrumbs` CSS restored to
  `flex-wrap: nowrap; white-space: nowrap; overflow: hidden` so the breadcrumb
  row stays on a single line at all viewport widths.
- **`file://` console error on report open**: Google Fonts external `<link>`
  tags caused Chrome to emit "Unsafe attempt to load URL file://…" security
  warnings. Resolved by setting `cspSafe: true` in converter output options.

---

## [1.0.0] — Initial release

- Python bridge (`bridge.py`) wrapping the Node.js Playwright Smart Reporter
  HTML generator.
- `converter.py`: converts pytest-json-report output to Smart Reporter data
  format; embeds failure screenshots as base64 data URIs from the
  pytest-playwright `--output` artifacts directory.
- `plugin.py`: pytest plugin (`--smart-reporter` flag) that auto-generates the
  Smart Report after `pytest_sessionfinish`.
- Bundled `_bundled_dist/` JS generators (fork of
  `playwright-smart-reporter`).
