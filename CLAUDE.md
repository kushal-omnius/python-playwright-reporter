# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Provenance

This repo is a standalone, separately-maintained copy of the `python/` folder from the upstream
[qa-gary-parker/playwright-smart-reporter](https://github.com/qa-gary-parker/playwright-smart-reporter)
monorepo (MIT licensed). It is not a git submodule or subtree — changes here do not sync
upstream automatically.

## Commands

```bash
pip install -e ".[dev]"     # editable install with dev deps (pytest-playwright, build)
pytest tests/ -v             # run the package's own test suite
pytest tests/test_converter.py::test_name -v   # run a single test
cd examples && python run_example.py           # run the end-to-end example
python scripts/bundle_dist.py                  # refresh _bundled_dist/ from a sibling monorepo checkout (requires ../dist and ../package.json with name "playwright-smart-reporter")
```

There is no lint/format/build config in this repo (no ruff/black/mypy config present).

## Architecture

This package is a **Python-to-Node.js bridge**: pytest produces JSON test results, and a
bundled, pre-compiled JavaScript HTML generator (from the upstream TypeScript project) turns
that data into the interactive Smart Report. There is no TypeScript source or `npm install`
step here — the compiled JS lives in `python_playwright_reporter/_bundled_dist/` (not present
in this checkout; ships via `pyproject.toml`'s `package-data` on install, or is regenerated
separately with `scripts/bundle_dist.py` from a sibling monorepo build).

Pipeline: **plugin.py → converter.py → bridge.py → Node.js**

1. **`plugin.py`** — pytest plugin (registered via the `pytest11` entry point). Adds
   `--smart-reporter` / `--smart-reporter-output` CLI flags, force-enables `pytest-json-report`
   when active, and on `pytest_sessionfinish` reads `.pytest-report.json` plus pytest-playwright's
   `--output` dir (for screenshots) and hands both to `SmartReporterBridge`. Report generation
   failures are caught and printed, never raised — a broken report must not fail the test run.

2. **`converter.py`** — pure data transform: pytest-json-report schema → the Smart Reporter's
   `HtmlGeneratorData` schema (`results`/`history`/`startTime`/`options` feature flags). Also
   locates failure screenshots on disk: `_screenshots_for_nodeid()` reproduces
   pytest-playwright's own nodeid→folder-name sanitization formula (non-alphanumeric runs → `-`,
   trimmed, truncated at 255 chars) to find the matching artifact directory, then embeds PNGs as
   base64 data URIs. This sanitization logic must stay byte-for-byte compatible with
   pytest-playwright's folder naming or screenshot lookup silently returns nothing.

3. **`bridge.py`** — `SmartReporterBridge._get_dist_root()` resolves the compiled JS location,
   checking (1) the bundled `_bundled_dist/` inside the installed package, then (2) a monorepo
   `dist/` by walking up from the file location and from cwd looking for a `package.json` named
   `"playwright-smart-reporter"`. `generate_report()` writes the converted data to a temp JSON
   file, generates a throwaway `.generate-report.js` script (with an absolute path to the
   generators dir substituted in, since Node's `require()` needs it, and paths normalized to
   forward slashes for Windows), invokes `node` as a subprocess, then deletes the script. After
   generation, `_inject_copy_buttons()` post-processes the output HTML to inject a clipboard-copy
   button next to every test title/file — this is a separate addition over upstream, fails silently,
   and must never break report generation.

Because the Node call happens via `subprocess.run(["node", ...])`, Node.js 18+ must be on PATH
at runtime — this is a hard runtime dependency the Python code does not vendor or check for
ahead of time (failures surface as a non-zero exit code from the generator script).

### separate modifications vs. upstream

`SETUP_COMPLETE.md` is the changelog of record for separate-only changes (currently: screenshot
embedding in `converter.py`/`bridge.py`, and the copy-button injection in `bridge.py`). Update it
when adding further separate-only features, so the delta from upstream stays documented in one place.


### Release creation:
- when a new release is created pyproject.toml should be updated
- changelog.md is maintained and used in a new release notes