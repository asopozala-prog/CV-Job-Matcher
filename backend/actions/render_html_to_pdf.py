# Render HTML to PDF through Kiron's PDF service, with a local Node fallback.

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_RENDER_CLI = PROJECT_ROOT / "pdf-service" / "render_cli.js"
FILE_URI_PATTERN = re.compile(r"file://[^\"'\s)<]+")


def _require_file(path: Path, label: str) -> Path:
    """Validate one required local file."""
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")
    return resolved


def _file_uri_to_data_uri(match: re.Match[str]) -> str:
    """Embed one local file URI so another service can render the HTML."""
    uri = match.group(0)
    parsed = urlparse(uri)
    local_path = Path(unquote(parsed.path))

    if not local_path.is_file():
        raise FileNotFoundError(
            f"HTML references a local file that does not exist: {local_path}"
        )

    mime_type, _ = mimetypes.guess_type(local_path.name)
    mime_type = mime_type or "application/octet-stream"
    encoded = base64.b64encode(local_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _make_html_portable(html: str) -> str:
    """Replace local file:// references with embedded data URIs."""
    return FILE_URI_PATTERN.sub(_file_uri_to_data_uri, html)


def _render_via_service(
    html: str,
    output_path: Path,
    service_url: str,
) -> None:
    """Send self-contained HTML to the private PDF service."""
    endpoint = urljoin(service_url.rstrip("/") + "/", "render")
    payload = json.dumps({"html": _make_html_portable(html)}).encode("utf-8")

    request = Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/pdf",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            content_type = response.headers.get("Content-Type", "")
            pdf_bytes = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"PDF service returned HTTP {exc.code}: {detail}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach PDF service: {exc}") from exc

    if "application/pdf" not in content_type.lower():
        raise RuntimeError(
            f"PDF service returned unexpected content type: {content_type}"
        )
    if not pdf_bytes.startswith(b"%PDF"):
        raise RuntimeError("PDF service response is not a valid PDF.")

    output_path.write_bytes(pdf_bytes)


def _render_locally(
    source_path: Path,
    output_path: Path,
) -> None:
    """Use the Node PDF renderer with the locally installed Chrome."""
    node = shutil.which("node")
    if node is None:
        raise RuntimeError(
            "Node.js is required for local PDF rendering but was not found."
        )
    if not LOCAL_RENDER_CLI.is_file():
        raise FileNotFoundError(
            f"Local PDF renderer does not exist: {LOCAL_RENDER_CLI}"
        )

    subprocess.run(
        [
            node,
            str(LOCAL_RENDER_CLI),
            str(source_path),
            str(output_path),
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


def render_html_to_pdf(
    html_path: str,
    output_pdf_path: str,
) -> str:
    """Render one HTML file locally or through the bound PDF service."""
    source_path = _require_file(Path(html_path), "HTML file")
    output_path = Path(output_pdf_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    service_url = os.environ.get("PDF_SERVICE_URL", "").strip()

    if service_url:
        html = source_path.read_text(encoding="utf-8")
        _render_via_service(html, output_path, service_url)
    else:
        _render_locally(source_path, output_path)

    if not output_path.is_file():
        raise RuntimeError(f"PDF renderer did not create: {output_path}")
    if output_path.read_bytes()[:4] != b"%PDF":
        raise RuntimeError(f"Rendered file is not a valid PDF: {output_path}")

    return str(output_path)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Render HTML to PDF locally or through Kiron's PDF service."
    )
    parser.add_argument("html_path")
    parser.add_argument("output_pdf_path")
    args = parser.parse_args()

    print(render_html_to_pdf(args.html_path, args.output_pdf_path))


if __name__ == "__main__":
    main()
