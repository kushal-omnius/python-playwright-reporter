# Development Guide

## Structure

```
python-playwright-reporter/
├── pyproject.toml
├── README.md
├── DEVELOPMENT.md
├── SETUP_COMPLETE.md                  ← changelog vs upstream
├── python_playwright_reporter/
│   ├── __init__.py
│   ├── bridge.py                      ← Node.js bridge + copy-button injection
│   ├── converter.py                   ← pytest JSON → Smart Reporter format + screenshots
│   ├── plugin.py                      ← pytest plugin (auto-wires --output dir)
│   └── _bundled_dist/                 ← compiled JS from upstream (committed)
│       ├── generators/
│       │   ├── html-generator.js      ← entry point called by bridge.py
│       │   ├── card-generator.js
│       │   ├── gallery-generator.js
│       │   └── ...
│       ├── utils/
│       └── vendors/
└── examples/
    ├── test_basic.py
    └── run_example.py
```

## How HTML generation works

```
pytest run
  └─ plugin.py: pytest_sessionfinish
       └─ bridge.py: generate_report()
            ├─ converter.py: convert_pytest_json()   [pure Python]
            │    ├─ maps pytest JSON → Smart Reporter data format
            │    └─ embeds failure screenshots as base64 data URIs
            ├─ writes .smart-reporter-data.json
            ├─ spawns: node _bundled_dist/generators/html-generator.js
            │    └─ reads data JSON → writes smart-report.html
            └─ _inject_copy_buttons()                [pure Python, post-process]
                 └─ appends <style>+<script> before </body>
```

Node.js is used only because `html-generator.js` is compiled TypeScript from the
upstream repo. Python has no native JS runtime, so `bridge.py` calls `node` as a
subprocess and passes the data JSON path as an argument. No `npm install` is needed —
all JS is self-contained inside `_bundled_dist/`.

## Setup

```bash
pip install -e ".[dev]"
```

## Running the examples

```bash
cd examples
python run_example.py
```

## Making changes

### Python code
Edit files in `python_playwright_reporter/`. With an editable install changes
take effect immediately — no reinstall needed.

### Updating the bundled JS generators
`_bundled_dist/` is committed to this repo. It is taken from the upstream
`playwright-smart-reporter-python` wheel and does not need rebuilding.

To update it when upstream releases a new version:

```bash
# 1. Download the new upstream wheel (no install)
pip download playwright-smart-reporter-python==<new-version> --no-deps -d /tmp/psr-wheel

# 2. Extract _bundled_dist from the wheel (wheels are zip files)
cd /tmp/psr-wheel
python - <<'EOF'
import zipfile, pathlib
whl = next(pathlib.Path('.').glob('playwright_smart_reporter_python-*.whl'))
dest = pathlib.Path('C:/WORK/python-playwright-reporter/python_playwright_reporter/_bundled_dist')
with zipfile.ZipFile(whl) as z:
    for m in [m for m in z.namelist() if '_bundled_dist/' in m]:
        rel = pathlib.Path(m).relative_to('playwright_smart_reporter_python/_bundled_dist')
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(z.read(m))
EOF

# 3. Commit
git add python_playwright_reporter/_bundled_dist
git commit -m "chore: update _bundled_dist to upstream v<new-version>"
```

## Troubleshooting

### "Cannot find compiled Smart Reporter JS files"
`_bundled_dist/generators/html-generator.js` is missing. This should not happen
with a normal install from this repo — check that the directory was not accidentally
gitignored or deleted.

### "Node.js not found"
Install Node.js 18+ from https://nodejs.org — it is needed at runtime to execute
the HTML generator.

### Report not generating
1. Check Node.js is installed: `node --version`
2. Check the package is installed: `pip show python-playwright-reporter`
3. Verify `_bundled_dist/generators/html-generator.js` exists inside the installed package.
