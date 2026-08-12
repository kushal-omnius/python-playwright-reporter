"""
Bridge to call the Node.js Playwright Smart Reporter from Python.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .converter import convert_pytest_json

# Injected after the Node.js generator writes the HTML.
# Adds a small clipboard button after every .test-title and .test-file element;
# buttons are invisible until the row is hovered so they don't clutter passing tests.
_COPY_BUTTONS_SNIPPET = """\
<style>
.copy-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: 5px;
  padding: 1px 5px;
  font-size: 10px;
  line-height: 1.4;
  background: transparent;
  border: 1px solid currentColor;
  border-radius: 3px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s;
  vertical-align: middle;
  color: inherit;
  user-select: none;
}
.test-title-row:hover .copy-btn,
.test-meta-row:hover .copy-btn,
.copy-btn.copied { opacity: 0.55; }
.copy-btn:hover  { opacity: 1 !important; }
.copy-btn.copied { color: #22c55e; border-color: #22c55e; }
</style>
<script>
(function () {
  function copyText(text) {
    var el = document.createElement('textarea');
    el.value = text;
    el.setAttribute('readonly', '');
    el.style.cssText = 'position:absolute;left:-9999px;top:0';
    document.body.appendChild(el);
    el.focus();
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
  }

  // Event delegation at capture phase — survives DOM re-renders caused by
  // the report's own tab/filter/sort handlers replacing .test-list-content.
  document.addEventListener('click', function (e) {
    var btn = e.target && e.target.closest && e.target.closest('.copy-btn[data-copy]');
    if (!btn) return;
    e.stopPropagation();
    e.preventDefault();
    copyText(btn.getAttribute('data-copy'));
    btn.textContent = '✓';
    btn.classList.add('copied');
    setTimeout(function () {
      btn.textContent = '⎘';
      btn.classList.remove('copied');
    }, 1500);
  }, true);

  // Inject copy buttons; text stored as data-copy so it survives re-reads.
  // data-copy-wired on the source element prevents double injection.
  function injectCopyBtns(root) {
    (root || document).querySelectorAll(
      '.test-title:not([data-copy-wired]), .test-file:not([data-copy-wired])'
    ).forEach(function (el) {
      el.setAttribute('data-copy-wired', '1');
      var text = el.textContent.trim();
      var btn = document.createElement('button');
      btn.className = 'copy-btn';
      btn.title = 'Copy to clipboard';
      btn.textContent = '⎘';
      btn.setAttribute('data-copy', text);
      el.after(btn);
    });
  }

  injectCopyBtns();

  // Re-inject when the report rebuilds the list (tab switch, filter, sort).
  var listContent = document.querySelector('.test-list-content');
  if (listContent && window.MutationObserver) {
    new MutationObserver(function (mutations) {
      var hasNewNodes = mutations.some(function (m) {
        return Array.from(m.addedNodes).some(function (n) {
          return n.nodeType === 1 && !n.classList.contains('copy-btn');
        });
      });
      if (hasNewNodes) injectCopyBtns(listContent);
    }).observe(listContent, { childList: true, subtree: true });
  }

  // Panel resizer
  (function () {
    var resizer = document.getElementById('panel-resizer');
    var layout = resizer && resizer.closest('.master-detail-layout');
    if (!resizer || !layout) return;

    var MIN_WIDTH = 200;
    var MAX_WIDTH = 700;
    var startX, startWidth;

    resizer.addEventListener('mousedown', function (e) {
      e.preventDefault();
      startX = e.clientX;
      startWidth = parseInt(getComputedStyle(layout).getPropertyValue('--list-panel-width') || '380', 10);
      resizer.classList.add('dragging');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';

      function onMove(e) {
        var delta = e.clientX - startX;
        var newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidth + delta));
        layout.style.setProperty('--list-panel-width', newWidth + 'px');
      }

      function onUp() {
        resizer.classList.remove('dragging');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      }

      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });

    // Double-click resets to default width
    resizer.addEventListener('dblclick', function () {
      layout.style.setProperty('--list-panel-width', '380px');
    });
  })();
})();
</script>
"""

# Template for the Node.js script. {generators_dir} is injected as an absolute
# path so require() resolves correctly regardless of cwd.  Internal relative
# requires (../utils, ./card-generator, etc.) resolve relative to the loaded
# file's own directory, so the preserved directory structure keeps them working.
_GENERATE_SCRIPT_TEMPLATE = """\
const fs = require('fs');
const path = require('path');
const {{ generateHtml }} = require('{generators_dir}/html-generator');

const inputPath = process.argv[2];
const outputPath = process.argv[3] || 'smart-report.html';

if (!inputPath) {{
  console.error('Usage: node .generate-report.js <data.json> [output.html]');
  process.exit(1);
}}

const data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const html = generateHtml(data);

const outDir = path.dirname(outputPath);
if (outDir && outDir !== '.') {{
  fs.mkdirSync(outDir, {{ recursive: true }});
}}

fs.writeFileSync(outputPath, html, 'utf8');
"""


def _get_dist_root() -> Path:
    """
    Locate the dist directory containing the compiled JS generators.

    Checks in order:
    1. Bundled dist shipped inside the Python package (PyPI install)
    2. Monorepo dist/ at the repository root (development)

    Returns the directory that contains generators/html-generator.js.
    """
    # 1) Bundled inside the installed package
    bundled = Path(__file__).resolve().parent / "_bundled_dist"
    if (bundled / "generators" / "html-generator.js").is_file():
        return bundled

    # 2) Monorepo layout
    monorepo = _find_monorepo_root()
    if monorepo is not None:
        dist = monorepo / "dist"
        if (dist / "generators" / "html-generator.js").is_file():
            return dist

    raise RuntimeError(
        "Cannot find the compiled Smart Reporter JS files.\n"
        "If installed via pip, the package may be corrupt - try reinstalling.\n"
        "If developing separately, run 'npm run build' from the repo root."
    )


def _find_monorepo_root() -> Optional[Path]:
    """
    Walk upward looking for the playwright-smart-reporter package.json.

    Returns the repo root Path or None.
    """
    # This file: python/python_playwright_reporter/bridge.py
    # Two parents up → monorepo root
    candidate = Path(__file__).resolve().parent.parent.parent
    if _is_valid_root(candidate):
        return candidate

    # Also try walking up from cwd (covers editable installs run from subdir)
    current = Path.cwd()
    for _ in range(6):
        if _is_valid_root(current):
            return current
        current = current.parent

    return None


def _is_valid_root(p: Path) -> bool:
    pj = p / "package.json"
    if not pj.exists():
        return False
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
        return data.get("name") == "playwright-smart-reporter"
    except Exception:
        return False


class SmartReporterBridge:
    """
    Bridge to generate Playwright Smart Reports from pytest results.

    This class handles:
    1. Converting pytest JSON to Smart Reporter format
    2. Locating the compiled JS generators (bundled or monorepo)
    3. Calling the Node.js HTML generator
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._dist_root = _get_dist_root()

    def generate_report(
        self,
        pytest_json_path: Path,
        output_html: Path,
        data_json_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        report_title: Optional[str] = None,
    ) -> None:
        """
        Generate Smart Report from pytest JSON results.

        Args:
            pytest_json_path: Path to pytest-json-report output
            output_html: Path for output HTML report
            data_json_path: Optional path to save intermediate data JSON
            output_dir: Optional path to pytest-playwright's --output directory.
                When supplied, failure screenshots are embedded in the report.
            report_title: Optional title for the report browser tab and header.
        """
        # Convert pytest JSON to Smart Reporter format
        html_data = convert_pytest_json(pytest_json_path, output_dir=output_dir, report_title=report_title)

        # Save intermediate data
        if data_json_path is None:
            data_json_path = self.project_root / ".smart-reporter-data.json"
        data_json_path.write_text(json.dumps(html_data, indent=2), encoding="utf-8")

        # Build the generator script with absolute path to generators dir
        generators_dir = (self._dist_root / "generators").resolve()
        # Normalise to forward slashes for Node.js on all platforms
        gen_dir_str = str(generators_dir).replace("\\", "/")
        script_content = _GENERATE_SCRIPT_TEMPLATE.format(generators_dir=gen_dir_str)

        script_path = self.project_root / ".generate-report.js"
        script_path.write_text(script_content, encoding="utf-8")

        try:
            node_cmd = "node.exe" if sys.platform.startswith("win") else "node"
            cmd = [
                node_cmd,
                str(script_path),
                str(Path(data_json_path).resolve()),
                str(Path(output_html).resolve()),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                stderr = result.stderr or result.stdout
                raise RuntimeError(f"Report generation failed:\n{stderr}")

            _inject_copy_buttons(Path(output_html))
        finally:
            # Clean up the temporary script
            if script_path.exists():
                script_path.unlink()


def _inject_copy_buttons(html_path: Path) -> None:
    """Append copy-to-clipboard buttons for test title and file into the report HTML."""
    try:
        html = html_path.read_text(encoding="utf-8")
        if "</body>" not in html:
            return
        html = html.replace("</body>", _COPY_BUTTONS_SNIPPET + "</body>", 1)
        html_path.write_text(html, encoding="utf-8")
    except Exception:
        pass  # never break report generation over a cosmetic feature


def regenerate_html(data_json_path: Path, output_html: Path) -> bool:
    """Re-generate the Smart Report HTML from an already-enriched data JSON file.

    Use this when the intermediate .smart-reporter-data.json has been modified
    after initial report generation (e.g. AI suggestions or screenshots injected)
    and the HTML needs to be rebuilt to reflect those changes.

    Runs the bundled Node.js HTML generator then injects copy-to-clipboard buttons.
    Returns True on success, False on any error (never raises).
    """
    try:
        dist_root = _get_dist_root()
        gen_dir = str((dist_root / "generators").resolve()).replace("\\", "/")
        script_content = _GENERATE_SCRIPT_TEMPLATE.format(generators_dir=gen_dir)

        script_path = Path(output_html).parent / ".generate-report.js"
        script_path.write_text(script_content, encoding="utf-8")
        try:
            node_cmd = "node.exe" if sys.platform.startswith("win") else "node"
            result = subprocess.run(
                [node_cmd, str(script_path),
                 str(Path(data_json_path).resolve()),
                 str(Path(output_html).resolve())],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                return False
            _inject_copy_buttons(Path(output_html))
            return True
        finally:
            if script_path.exists():
                script_path.unlink()
    except Exception:
        return False
