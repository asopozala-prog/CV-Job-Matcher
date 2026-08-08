# Render a local HTML document into PDF with the installed Google Chrome.

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


CHROME_EXECUTABLE = Path(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)


def render_html_to_pdf(
    html_path: str,
    output_pdf_path: str,
) -> str:
    """Render one local HTML file into a PDF and return the output path."""
    source_path = Path(html_path).expanduser()
    output_path = Path(output_pdf_path).expanduser()

    if not source_path.is_file():
        raise FileNotFoundError(f"HTML file does not exist: {source_path}")
    if not CHROME_EXECUTABLE.is_file():
        raise FileNotFoundError(
            f"Google Chrome executable does not exist: {CHROME_EXECUTABLE}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=str(CHROME_EXECUTABLE),
                headless=True,
            )
            try:
                page = browser.new_page()
                page.goto(
                    source_path.resolve().as_uri(),
                    wait_until="networkidle",
                )
                page.wait_for_function(
                    """() => Array.from(document.images).every(
                        image => image.complete && image.naturalWidth > 0
                    )"""
                )
                page.pdf(
                    path=str(output_path.resolve()),
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to render PDF '{output_path}' from '{source_path}': {exc}"
        ) from exc

    return str(output_path.resolve())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a local HTML file into PDF with Google Chrome."
    )
    parser.add_argument("html_path")
    parser.add_argument("output_pdf_path")
    args = parser.parse_args()

    result = render_html_to_pdf(
        args.html_path,
        args.output_pdf_path,
    )
    print(result)


if __name__ == "__main__":
    main()
