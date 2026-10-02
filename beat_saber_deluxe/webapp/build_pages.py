#!/usr/bin/env python3
"""
build_pages.py — build the static GitHub Pages bundle from webapp/.

One UI bundle, two deploys (plan §2): the SAME static/ files run as the local
backend's UI and as the Pages command-builder. In Pages mode `/api/ping` fails
→ app.js switches to command-builder mode (Deploy buttons become "copy the
generated command").

This script copies the UI into a build dir and adds:
- index.html with a `data-mode="pages"` marker (belt + suspenders: instant
  mode detection, no ping round-trip) and a Pages-mode banner
- all static assets unchanged
- a copy of dumper.cfg (the Dump Guide's download link stays functional)

Usage: python3 webapp/build_pages.py [--out DIR]   (default: pages-dist/)
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

WEBAPP = Path(__file__).resolve().parent
STATIC = WEBAPP / "static"

PAGES_BANNER = """\
<div id="pages-banner" class="pages-banner" hidden>
  <b>Command-builder mode</b> — this hosted page cannot reach your PS4 or your
  game dump. Configure your loadout here, then copy the generated command and
  run it on the machine with your <code>ps4_dump/</code> + PS4. For the full
  point-and-click experience, run the local backend from the release:
  <code>python3 webapp/server.py</code>
  <button id="pages-banner-dismiss" class="link">hide</button>
</div>"""


def build(out_dir: Path) -> list[Path]:
    if not STATIC.is_dir():
        raise SystemExit(f"static UI not found: {STATIC}")
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for asset in STATIC.iterdir():
        if asset.is_file():
            shutil.copy2(asset, out_dir / asset.name)
            written.append(out_dir / asset.name)

    # index.html: stamp the pages mode + banner
    index = (out_dir / "index.html")
    html = index.read_text(encoding="utf-8")
    html = html.replace(
        "<html lang=\"en\">",
        "<html lang=\"en\" data-mode=\"pages\">", 1)
    if "pages-banner" not in html:
        html = html.replace("<main>", PAGES_BANNER + "\n\n<main>", 1)
        html = html.replace(
            "document.addEventListener(\"DOMContentLoaded\", () => {",
            "document.addEventListener(\"DOMContentLoaded\", () => {\n"
            "  const banner = document.getElementById('pages-banner');\n"
            "  if (banner && document.documentElement.dataset.mode === 'pages') {\n"
            "    banner.hidden = false;\n"
            "    document.getElementById('pages-banner-dismiss').onclick = () =>"
            " banner.hidden = true;\n"
            "  }", 1)
    index.write_text(html, encoding="utf-8")
    written.append(index)

    # app.js: honor the data-mode marker immediately (no ping wait)
    appjs = (out_dir / "app.js")
    js = appjs.read_text(encoding="utf-8")
    if "data-mode" not in js:
        js = js.replace(
            "async function detectMode() {",
            "async function detectMode() {\n"
            "  if (document.documentElement.dataset.mode === 'pages') {\n"
            "    state.mode = 'pages';\n"
            "    const badge = $(\"mode-badge\");\n"
            "    badge.textContent = \"\\u25D0 pages mode (command builder)\";\n"
            "    badge.className = \"pages\";\n"
            "    document.querySelectorAll(\".local-only\").forEach("
            "el => el.classList.add(\"hidden\"));\n"
            "    return;\n"
            "  }", 1)
        appjs.write_text(js, encoding="utf-8")
    written.append(appjs)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Pages bundle")
    parser.add_argument("--out", default=str(WEBAPP.parent / "pages-dist"),
                        help="output dir (default: pages-dist/ next to webapp/)")
    args = parser.parse_args()
    files = build(Path(args.out))
    print(f"Pages bundle: {len(files)} files -> {args.out}")
    for f in files:
        print(f"  {f}")


if __name__ == "__main__":
    main()
