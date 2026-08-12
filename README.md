# Playwright Smart Reporter - Python

Python integration for Playwright tests - brings AI-powered failure analysis, flakiness detection, and beautiful HTML reports to your pytest test suites.

> **copy notice:** this directory is a verbatim copy of the `python/` folder from
> [qa-gary-parker/playwright-smart-reporter](https://github.com/qa-gary-parker/playwright-smart-reporter),
> used and modified separately under the terms of the MIT licence. The original copyright notice is
> retained in [LICENSE](LICENSE). It is not affiliated with or endorsed by the upstream project.

## Features

- **AI Failure Analysis** - Claude/OpenAI/Gemini powered suggestions
- **Smart Analytics** - Flakiness detection, performance regression alerts
- **Trend Charts** - Visual history of test health over time
- **Stability Scoring** - A+ to F grades for test reliability
- **Failure Clustering** - Group similar errors automatically
- **Modern Dashboard** - Interactive sidebar navigation, light/dark themes, drag-to-resize panels
- **Environment Card** - Python version, platform, package versions, and detected browsers shown in the Overview tab

## Prerequisites

- Python 3.9+
- Node.js 18+ (runtime only - no `npm install` needed)

## Installation

From this repo (local / editable):

```bash
pip install -e .
```

From GitHub:

```bash
pip install "python-playwright-reporter @ git+https://github.com/kushal-omnius/python-playwright-reporter.git"
```

The compiled JavaScript report generator (`_bundled_dist/`) is committed to this
repo and bundled into the installed package — no `npm install` or build step is
needed. Node.js must be available at runtime to execute it.

## Quick Start

### Option 1: Pytest Plugin (Automatic)

Run your tests with the `--smart-reporter` flag:

```bash
pytest --json-report --smart-reporter
```

Report automatically generated at `smart-report.html`.

Optional flags:
- `--smart-reporter-output=<path>` — change the output file (default: `smart-report.html`)
- `--smart-reporter-title=<text>` — set a custom title shown in the report header

### Option 2: Manual Generation

```python
from python_playwright_reporter import SmartReporterBridge

bridge = SmartReporterBridge()
bridge.generate_report(
    pytest_json_path=".pytest-report.json",
    output_html="smart-report.html"
)
```

### Option 3: Re-render from existing data JSON

If you have a previously-generated `.smart-reporter-data.json` and want to rebuild
the HTML (e.g. after modifying the data file):

```python
from python_playwright_reporter import regenerate_html

regenerate_html(
    data_json_path=".smart-reporter-data.json",
    output_html="smart-report.html"
)
```

## Configuration

### pytest.ini / pyproject.toml

```ini
[pytest]
addopts =
    --json-report
    --json-report-file=.pytest-report.json
    --smart-reporter
    --smart-reporter-title="Smart Reports"
    --smart-reporter-output=test-reports/smart-report.html
```

### Environment Variables

```bash
# AI Analysis (optional)
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."
```

> **Note:** Reports are always generated with `cspSafe` mode enabled. This means
> Google Fonts `<link>` tags are omitted and system fonts are used instead, which
> prevents browser security warnings when opening the report from a `file://` URL.
> This is intentional and not configurable from the CLI.

## How It Works

1. **pytest** runs tests; `plugin.py` collects the JSON report and the
   pytest-playwright `--output` artifacts directory
2. **`converter.py`** maps the pytest JSON to the Smart Reporter data format and
   embeds any failure screenshots as base64 data URIs
3. **`bridge.py`** writes the converted data to a temp JSON file, generates a
   throwaway `.generate-report.js` script that `require()`s the bundled
   `html-generator.js`, and invokes `node` on it — Node.js writes `smart-report.html`
4. **`bridge.py`** post-processes the HTML to inject copy-to-clipboard buttons
   and a drag-to-resize panel handle

## Development

```bash
pip install -e ".[dev]"   # editable install with dev dependencies
pytest tests/ -v          # run the package's own tests
```

## Troubleshooting

### Node.js not found

The package needs Node.js at runtime to execute the report generator:

```bash
# macOS
brew install node

# Linux
sudo apt install nodejs

# Windows
# Download from https://nodejs.org
```

## License

MIT - See [LICENSE](LICENSE).
