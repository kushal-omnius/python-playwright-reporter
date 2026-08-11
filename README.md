# Playwright Smart Reporter - Python

Python integration for Playwright tests - brings AI-powered failure analysis, flakiness detection, and beautiful HTML reports to your pytest test suites.

> **separate copy notice:** this directory is a verbatim copy of the `python/` folder from
> [qa-gary-parker/playwright-smart-reporter](https://github.com/qa-gary-parker/playwright-smart-reporter),
> used and modified separately under the terms of the MIT licence. The original copyright notice is
> retained in [LICENSE](LICENSE). It is not affiliated with or endorsed by the upstream project.

## Features

- **AI Failure Analysis** - Claude/OpenAI/Gemini powered suggestions
- **Smart Analytics** - Flakiness detection, performance regression alerts
- **Trend Charts** - Visual history of test health over time
- **Stability Scoring** - A+ to F grades for test reliability
- **Failure Clustering** - Group similar errors automatically
- **Modern Dashboard** - Interactive sidebar navigation, light/dark themes

## Prerequisites

- Python 3.9+
- Node.js 18+ (runtime only - no `npm install` needed)

## Installation

Install directly from this directory:

```bash
pip install -e .
```

The package is self-contained. The compiled JavaScript report generator is bundled inside - Node.js is only needed at runtime to execute it.

## Quick Start

### Option 1: Pytest Plugin (Automatic)

Run your tests with the `--smart-reporter` flag:

```bash
pytest --json-report --smart-reporter
```

Report automatically generated at `smart-report.html`.

### Option 2: Manual Generation

```python
from python_playwright_reporter import SmartReporterBridge

bridge = SmartReporterBridge()
bridge.generate_report(
    pytest_json_path=".pytest-report.json",
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
    --smart-reporter-output=test-reports/smart-report.html
```

### Environment Variables

```bash
# AI Analysis (optional)
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."
```

## How It Works

1. **pytest** runs your tests with JSON reporting enabled
2. **Converter** transforms pytest JSON to Playwright Smart Reporter format
3. **Node.js bridge** calls the bundled HTML generator
4. **Output** interactive HTML report

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
