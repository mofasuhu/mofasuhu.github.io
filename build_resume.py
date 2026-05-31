#!/usr/bin/env python3
"""
Build index.html and PDF resume from resume.json (single source of truth).

Usage:
  python build_resume.py html     # regenerate index.html
  python build_resume.py pdf        # Muhammad_Farouk_Resume_<timestamp>.pdf
  python build_resume.py all        # html + pdf

PDF engines (first available): wkhtmltopdf → Playwright → WeasyPrint
Install wkhtmltopdf for closest match to the legacy Muhammad_Farouk.pdf layout.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
RESUME_JSON = ROOT / "resume.json"
TEMPLATE_DIR = ROOT / "templates"
INDEX_HTML = ROOT / "index.html"
PDF_PREFIX = "Muhammad_Farouk_Resume_"


def load_resume_data() -> dict:
    with RESUME_JSON.open(encoding="utf-8") as f:
        return json.load(f)


def get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_html(data: dict, *, for_pdf: bool = False) -> str:
    env = get_jinja_env()
    template = env.get_template("resume.html.j2")
    return template.render(data=data, for_pdf=for_pdf)


def build_index_html(data: dict) -> Path:
    html = render_html(data, for_pdf=False)
    INDEX_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {INDEX_HTML}")
    return INDEX_HTML


def find_wkhtmltopdf() -> str | None:
    custom = os.environ.get("WKHTMLTOPDF_PATH")
    if custom and Path(custom).is_file():
        return custom
    return shutil.which("wkhtmltopdf")


def _write_pdf_wkhtmltopdf(html_path: Path, output_path: Path) -> None:
    binary = find_wkhtmltopdf()
    if not binary:
        raise FileNotFoundError("wkhtmltopdf not found")

    cmd = [
        binary,
        "--enable-local-file-access",
        "--print-media-type",
        "--page-size",
        "A4",
        "--margin-top",
        "11mm",
        "--margin-bottom",
        "11mm",
        "--margin-left",
        "9mm",
        "--margin-right",
        "9mm",
        "--encoding",
        "UTF-8",
        "--title",
        "Muhammad Farouk's Resume",
        str(html_path),
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def _write_pdf_playwright(html_path: Path, output_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    file_url = html_path.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.emulate_media(media="print")
        page.goto(file_url, wait_until="networkidle")
        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={"top": "7mm", "right": "8mm", "bottom": "7mm", "left": "8mm"},
        )
        browser.close()


def _write_pdf_weasyprint(html_path: Path, output_path: Path) -> None:
    from weasyprint import HTML

    HTML(filename=str(html_path), base_url=str(ROOT)).write_pdf(str(output_path))


def build_pdf(data: dict) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = ROOT / f"{PDF_PREFIX}{timestamp}.pdf"
    temp_html = ROOT / ".resume_pdf_build.html"

    try:
        temp_html.write_text(render_html(data, for_pdf=True), encoding="utf-8")
        engines: list[tuple[str, callable]] = []
        if find_wkhtmltopdf():
            engines.append(("wkhtmltopdf", _write_pdf_wkhtmltopdf))
        engines.extend(
            [
                ("playwright", _write_pdf_playwright),
                ("weasyprint", _write_pdf_weasyprint),
            ]
        )

        last_error: Exception | None = None
        for name, writer in engines:
            try:
                writer(temp_html, output_path)
                print(f"Wrote {output_path} (engine: {name})")
                if name == "wkhtmltopdf":
                    print("  Tip: wkhtmltopdf matches the legacy PDF layout best.")
                elif name != "wkhtmltopdf" and not find_wkhtmltopdf():
                    print(
                        "  Tip: Install wkhtmltopdf for closer match to Muhammad_Farouk.pdf — "
                        "https://wkhtmltopdf.org/downloads.html",
                        file=sys.stderr,
                    )
                return output_path
            except ImportError as exc:
                last_error = exc
                continue
            except FileNotFoundError as exc:
                last_error = exc
                continue
            except subprocess.CalledProcessError as exc:
                last_error = exc
                print(f"Warning: {name} failed: {exc.stderr or exc}", file=sys.stderr)
                continue
            except Exception as exc:
                last_error = exc
                print(f"Warning: {name} failed: {exc}", file=sys.stderr)
                continue

        raise RuntimeError(
            "Could not generate PDF. Install dependencies:\n"
            "  pip install -r requirements.txt\n"
            "  playwright install chromium\n"
            "Optional (legacy layout): wkhtmltopdf — set WKHTMLTOPDF_PATH if needed\n"
            f"Last error: {last_error}"
        ) from last_error
    finally:
        if temp_html.exists():
            temp_html.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build resume HTML and PDF from resume.json")
    parser.add_argument(
        "target",
        choices=["html", "pdf", "all"],
        help="What to generate",
    )
    args = parser.parse_args()

    if not RESUME_JSON.exists():
        print(f"Missing {RESUME_JSON}", file=sys.stderr)
        return 1

    data = load_resume_data()

    if args.target in ("html", "all"):
        build_index_html(data)
    if args.target in ("pdf", "all"):
        build_pdf(data)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
