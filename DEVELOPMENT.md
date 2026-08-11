# Development Guide

## Structure

```
python-playwright-reporter/
├── pyproject.toml
├── README.md
├── DEVELOPMENT.md
├── SETUP_COMPLETE.md          ← changelog vs upstream
├── python_playwright_reporter/
│   ├── __init__.py
│   ├── bridge.py              ← Node.js bridge + copy-button injection
│   ├── converter.py           ← pytest JSON → Smart Reporter format + screenshots
│   └── plugin.py              ← pytest plugin (auto-wires --output dir)
└── examples/
    ├── test_basic.py
    └── run_example.py
```

The compiled JavaScript report generator is bundled inside the package under
`_bundled_dist/`. No `npm install` or TypeScript build is needed — Node.js must
only be available at runtime to execute it.

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

### Bundled JS generators
The HTML generator is compiled TypeScript from the upstream repo. To update it,
grab a fresh `_bundled_dist/` from a new upstream release and drop it in.

## Troubleshooting

### "Cannot find compiled Smart Reporter JS files"
The `_bundled_dist/` directory is missing. Reinstall the package or copy it from
an upstream release.

### "Node.js not found"
Install Node.js 18+ from https://nodejs.org — it is needed at runtime to execute
the HTML generator.

### Report not generating
1. Check Node.js is installed: `node --version`
2. Check the package is installed: `pip show python-playwright-reporter`
3. Check `_bundled_dist/generators/html-generator.js` exists inside the package.
