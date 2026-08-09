# Render Kiron's matching-evaluation JSON into the evaluation PDF HTML template.

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import re
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEMPLATE = PROJECT_ROOT / "backend" / "templates" / "kiron_evaluation_pdf.html"
DEFAULT_CSS = PROJECT_ROOT / "backend" / "templates" / "kiron_evaluation_pdf.css"

PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")


def _read_utf8(path: Path, label: str) -> str:
    """Read one required UTF-8 text file."""
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} is not valid UTF-8: {path}") from exc


def _load_evaluation(path: Path) -> dict[str, Any]:
    """Load and validate Kiron's evaluation JSON."""
    try:
        data = json.loads(_read_utf8(path, "Evaluation JSON"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid evaluation JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    required = {
        "overall_recommendation",
        "hr_screening_probability",
        "reasoning",
        "good_match",
        "gaps",
        "final_verdict",
        "kiron_support",
    }

    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(
            "Evaluation JSON is missing required fields: "
            + ", ".join(missing)
        )

    return data


def _slug(value: Any) -> str:
    """Convert recommendation text into a CSS-safe slug."""
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _recommendation_icon(slug: str) -> str:
    """Map recommendation status to Kiron's matching icon."""
    mapping = {
        "strong-yes": "kiron_strong_yes.png",
        "yes": "kiron_yes.png",
        "borderline": "kiron_maybe.png",
        "maybe": "kiron_maybe.png",
        "unlikely": "kiron_no.png",
        "no": "kiron_no.png",
        "strong-no": "kiron_strong_no.png",
    }
    return mapping.get(slug, "kiron_recommendation.png")


def _asset_uri(assets_dir: Path, filename: str) -> str:
    """Resolve one required Kiron PNG as a local file URI."""
    path = assets_dir / filename
    if not path.is_file():
        raise FileNotFoundError(f"Kiron asset does not exist: {path}")
    return path.resolve().as_uri()


def _build_context(
    evaluation: dict[str, Any],
    assets_dir: Path,
) -> dict[str, Any]:
    """Build scalar and asset placeholders required by the template."""
    recommendation_slug = _slug(evaluation["overall_recommendation"])

    return {
        **evaluation,
        "overall_recommendation_slug": recommendation_slug,
        "assets": {
            "kiron_analysis": _asset_uri(assets_dir, "kiron_analysis.png"),
            "recommendation_icon": _asset_uri(
                assets_dir,
                _recommendation_icon(recommendation_slug),
            ),
            "kiron_probability": _asset_uri(
                assets_dir,
                "kiron_probability.png",
            ),
            "kiron_personal_profile": _asset_uri(
                assets_dir,
                "kiron_personal_profile.png",
            ),
            "kiron_projects": _asset_uri(
                assets_dir,
                "kiron_projects.png",
            ),
            "kiron_good_match": _asset_uri(
                assets_dir,
                "kiron_good_match.png",
            ),
            "kiron_gaps": _asset_uri(
                assets_dir,
                "kiron_gaps.png",
            ),
            "kiron_support": _asset_uri(
                assets_dir,
                "kiron_support.png",
            ),
        },
    }


def _lookup(context: dict[str, Any], dotted_key: str) -> Any:
    """Resolve one dotted placeholder such as assets.kiron_analysis."""
    current: Any = context

    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_key)
        current = current[part]

    return current


def _replace_placeholders(
    template: str,
    context: dict[str, Any],
) -> str:
    """Replace template placeholders with escaped scalar values."""
    unknown: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        try:
            value = _lookup(context, key)
        except KeyError:
            unknown.add(key)
            return match.group(0)

        if isinstance(value, (dict, list)):
            unknown.add(key)
            return match.group(0)

        return escape("" if value is None else str(value), quote=True)

    rendered = PLACEHOLDER_RE.sub(replace, template)

    if unknown:
        raise ValueError(
            "Unsupported or unresolved template placeholders: "
            + ", ".join(sorted(unknown))
        )

    return rendered


def _inline_css(html: str, css: str) -> str:
    """Replace the evaluation stylesheet link with embedded CSS."""
    link_re = re.compile(
        r'<link\b[^>]*href=["\']kiron_evaluation_pdf\.css["\'][^>]*>',
        flags=re.IGNORECASE,
    )

    style_tag = f"<style>\n{css}\n</style>"

    if link_re.search(html):
        return link_re.sub(style_tag, html, count=1)

    head_end = html.lower().find("</head>")
    if head_end == -1:
        raise ValueError("Evaluation HTML template is missing </head>.")

    return html[:head_end] + style_tag + "\n" + html[head_end:]


def render_evaluation_to_html(
    evaluation_json_path: str,
    output_html_path: str,
    assets_dir: str,
    template_path: str | None = None,
    css_path: str | None = None,
) -> str:
    """Render matching_evaluation.json into Kiron's evaluation HTML."""
    evaluation_path = Path(evaluation_json_path).expanduser()
    output_path = Path(output_html_path).expanduser()
    asset_path = Path(assets_dir).expanduser()

    selected_template = (
        Path(template_path).expanduser()
        if template_path
        else DEFAULT_TEMPLATE
    )
    selected_css = (
        Path(css_path).expanduser()
        if css_path
        else DEFAULT_CSS
    )

    if not asset_path.is_dir():
        raise FileNotFoundError(
            f"Kiron assets directory does not exist: {asset_path}"
        )

    evaluation = _load_evaluation(evaluation_path)
    template = _read_utf8(selected_template, "Evaluation HTML template")
    css = _read_utf8(selected_css, "Evaluation CSS")

    context = _build_context(evaluation, asset_path)
    rendered = _replace_placeholders(template, context)
    rendered = _inline_css(rendered, css)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    return str(output_path.resolve())


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Render Kiron's matching evaluation into HTML."
    )
    parser.add_argument(
        "evaluation_json_path",
        help="Path to matching_evaluation.json",
    )
    parser.add_argument(
        "output_html_path",
        help="Path for generated evaluation HTML",
    )
    parser.add_argument(
        "--assets-dir",
        required=True,
        help="Directory containing Kiron's PNG assets",
    )
    parser.add_argument(
        "--template",
        dest="template_path",
        help="Optional evaluation HTML template override",
    )
    parser.add_argument(
        "--css",
        dest="css_path",
        help="Optional evaluation CSS override",
    )

    args = parser.parse_args()

    print(
        render_evaluation_to_html(
            evaluation_json_path=args.evaluation_json_path,
            output_html_path=args.output_html_path,
            assets_dir=args.assets_dir,
            template_path=args.template_path,
            css_path=args.css_path,
        )
    )


if __name__ == "__main__":
    main()
