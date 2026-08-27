"""
JSON converter: pytest-json-report format -> Playwright Smart Reporter format
"""
import base64
import importlib.metadata
import json
import platform
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def _collect_env_info(data: Dict[str, Any], tests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Collect runtime environment metadata to display in the report overview."""
    def _pkg(name: str) -> str:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return ""

    # Browsers: infer from raw nodeids (before browser suffix is stripped from title)
    browser_map = {"chromium": "Chromium", "firefox": "Firefox", "webkit": "WebKit"}
    found_browsers = []
    for test in tests:
        nodeid = test.get("nodeid", "")
        for key, label in browser_map.items():
            if nodeid.endswith(f"[{key}]") and label not in found_browsers:
                found_browsers.append(label)

    # Base URL: written by root conftest into pytest-metadata → pytest-json-report environment
    pytest_env = data.get("environment") or {}
    base_url = pytest_env.get("Base URL", "")

    reporter_version = _pkg("python-playwright-reporter")

    packages: Dict[str, str] = {}
    for pkg in ("pytest", "pytest-playwright", "playwright"):
        v = _pkg(pkg)
        if v:
            packages[pkg] = v

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": packages,
        "browsers": found_browsers,
        "base_url": base_url,
        "reporter_version": reporter_version,
    }


def _to_ms(seconds: Optional[Union[float, int]]) -> int:
    """Convert seconds to milliseconds."""
    if seconds is None:
        return 0
    try:
        return int(float(seconds) * 1000)
    except (TypeError, ValueError):
        return 0


def _extract_error(test: Dict[str, Any]) -> Optional[str]:
    """Extract error message from pytest test result."""
    for phase in ("call", "setup", "teardown"):
        data = test.get(phase) or {}
        longrepr = data.get("longrepr")
        if longrepr:
            if isinstance(longrepr, str):
                return longrepr
            if isinstance(longrepr, dict):
                return longrepr.get("message") or json.dumps(longrepr)
            return str(longrepr)
    return None


def _status_from_outcome(outcome: Optional[str]) -> str:
    """Map pytest outcome to Playwright status."""
    if outcome == "passed":
        return "passed"
    if outcome == "failed":
        return "failed"
    if outcome == "skipped":
        return "skipped"
    return "failed"


def _playwright_outcome(outcome: Optional[str]) -> str:
    """Map pytest outcome to Playwright outcome enum."""
    if outcome == "passed":
        return "expected"
    if outcome == "skipped":
        return "skipped"
    return "unexpected"


def _screenshots_for_nodeid(output_dir: Path, nodeid: str) -> List[str]:
    """Return base64 data URIs for all PNGs saved under output_dir for nodeid.

    pytest-playwright names the artifact folder by replacing every run of
    non-alphanumeric characters in the nodeid with a single hyphen, then
    stripping leading/trailing hyphens.
    """
    folder_name = re.sub(r"[^a-zA-Z0-9]+", "-", nodeid).strip("-")
    if len(folder_name) > 255:
        folder_name = folder_name[:100] + "..." + folder_name[-100:]
    test_dir = output_dir / folder_name
    if not test_dir.exists():
        return []
    return [
        "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
        for p in sorted(test_dir.glob("*.png"))
    ]


def convert_pytest_json(
    pytest_json_path: Path,
    output_dir: Optional[Path] = None,
    report_title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert pytest JSON report to Playwright Smart Reporter data format.

    Args:
        pytest_json_path: Path to pytest-json-report output file
        output_dir: Optional path to pytest-playwright's --output directory.
            When supplied, failure screenshots are embedded as data URIs so the
            gallery view can display them.
        report_title: Optional title shown in the browser tab and report header.
            Defaults to 'Smart Report'.

    Returns:
        Dictionary in Smart Reporter HtmlGeneratorData format
    """
    data = json.loads(pytest_json_path.read_text(encoding="utf-8"))
    created = data.get("created") or datetime.utcnow().timestamp()
    tests: List[Dict[str, Any]] = data.get("tests", [])

    results: List[Dict[str, Any]] = []

    for test in tests:
        nodeid = test.get("nodeid", "unknown::test")

        # Parse test file and name from nodeid
        if "::" in nodeid:
            parts = nodeid.split("::")
            file_part = parts[0]
            title = "::".join(parts[1:])
        else:
            file_part, title = "unknown", nodeid

        # Strip pytest-playwright browser parametrize suffix.
        # Handles standalone [chromium] and combined [param-chromium] cases.
        title = re.sub(r"-(chromium|firefox|webkit)\]$", "]", title)
        title = re.sub(r"\[(chromium|firefox|webkit)\]$", "", title).rstrip()

        outcome = test.get("outcome")
        duration = test.get("duration")
        error = _extract_error(test)

        # Extract additional metadata
        keywords = test.get("keywords", [])

        screenshots: List[str] = []
        if output_dir is not None and outcome == "failed":
            screenshots = _screenshots_for_nodeid(output_dir, nodeid)

        results.append(
            {
                "testId": nodeid,
                "title": title,
                "file": file_part,
                "status": _status_from_outcome(outcome),
                "duration": _to_ms(duration),
                "error": error,
                "retry": 0,
                "outcome": _playwright_outcome(outcome),
                "expectedStatus": "skipped" if outcome == "skipped" else "passed",
                "steps": [],
                "history": [],
                "tags": keywords if isinstance(keywords, list) else [],
                "attachments": {
                    "screenshots": screenshots,
                    "videos": [],
                    "traces": [],
                    "custom": [],
                },
            }
        )

    has_screenshots = any(r["attachments"]["screenshots"] for r in results)

    html_data: Dict[str, Any] = {
        "results": results,
        "history": {
            "runs": [],
            "tests": {},
            "summaries": [],
        },
        "startTime": int(float(created) * 1000),
        "environment": _collect_env_info(data, tests),
        "options": {
            # Feature flags - enable what makes sense for pytest
            "enableTraceViewer": False,
            "enableNetworkLogs": False,
            "enableGalleryView": has_screenshots,
            "enableComparison": False,
            "enableHistoryDrilldown": False,
            "enableAIRecommendations": True,
            "enableTrendsView": True,
            "enableStabilityScore": True,
            "enableFailureClustering": True,
            "enableRetryAnalysis": False,
            # Reports are opened as file:// URLs where external resources are blocked.
            # cspSafe skips Google Fonts <link> tags and uses system fonts instead.
            "cspSafe": True,
            **({"title": report_title} if report_title else {}),
        },
    }

    return html_data
