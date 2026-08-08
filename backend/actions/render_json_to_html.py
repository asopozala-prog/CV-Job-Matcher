# Render CV content JSON through an external HTML/CSS template.

from __future__ import annotations

import argparse
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import re
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEMPLATE_PATH = PROJECT_ROOT / "backend" / "templates" / "template_01.html"
DEFAULT_CSS_PATH = PROJECT_ROOT / "backend" / "templates" / "template_01.css"

PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")
STYLESHEET_LINK_RE = re.compile(
    r'<link\b[^>]*\brel=["\']stylesheet["\'][^>]*>',
    flags=re.IGNORECASE,
)


def _read_utf8(path: Path, label: str) -> str:
    """Read one required UTF-8 text file."""
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} is not valid UTF-8: {path}") from exc


def _load_json(path: Path) -> dict[str, Any]:
    """Load and minimally validate the CV content JSON."""
    try:
        data = json.loads(_read_utf8(path, "CV JSON file"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in '{path}' at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("CV JSON must contain one top-level object.")

    required_objects = ("candidate", "contact", "render_options")
    required_lists = (
        "experience",
        "education",
        "skills",
        "languages",
        "certifications",
        "projects",
        "additional",
    )

    for key in required_objects:
        if not isinstance(data.get(key), dict):
            raise ValueError(f"CV JSON field '{key}' must be an object.")

    for key in required_lists:
        if not isinstance(data.get(key), list):
            raise ValueError(f"CV JSON field '{key}' must be a list.")

    return data


def _string(value: Any) -> str:
    """Convert a scalar value to a string."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _escaped(value: Any) -> str:
    """Escape user-controlled content for HTML text or attributes."""
    return escape(_string(value), quote=True)


def _lookup(data: dict[str, Any], dotted_key: str) -> Any:
    """Read a dotted scalar path from nested dictionaries."""
    current: Any = data

    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_key)
        current = current[part]

    return current


def _replace_placeholders(
    source: str,
    context: dict[str, Any],
    *,
    allow_unknown: bool = False,
) -> str:
    """Replace dotted placeholders using escaped values."""
    unknown: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)

        try:
            value = _lookup(context, key)
        except KeyError:
            if allow_unknown:
                return match.group(0)
            unknown.add(key)
            return match.group(0)

        if isinstance(value, (dict, list)):
            unknown.add(key)
            return match.group(0)

        return _escaped(value)

    rendered = PLACEHOLDER_RE.sub(replace, source)

    if unknown and not allow_unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"Unsupported or non-scalar placeholders: {names}")

    return rendered


def _extract_marked_block(
    source: str,
    marker_name: str,
) -> tuple[str, str, str] | None:
    """Return text before, inside, and after one marked template block."""
    start = f"<!-- {marker_name}_START -->"
    end = f"<!-- {marker_name}_END -->"

    start_index = source.find(start)
    end_index = source.find(end)

    if start_index == -1 and end_index == -1:
        return None
    if start_index == -1 or end_index == -1 or end_index < start_index:
        raise ValueError(f"Malformed HTML marker pair: {marker_name}")

    before = source[:start_index]
    block = source[start_index + len(start):end_index]
    after = source[end_index + len(end):]
    return before, block, after


def _expand_block(
    source: str,
    marker_name: str,
    items: list[dict[str, Any]],
    render_item: Callable[[str, dict[str, Any]], str],
) -> str:
    """Clone one marked HTML block for every JSON list item."""
    extracted = _extract_marked_block(source, marker_name)
    if extracted is None:
        raise ValueError(f"HTML template is missing markers for {marker_name}")

    before, block, after = extracted
    rendered_items = "".join(render_item(block, item) for item in items)
    return before + rendered_items + after


def _experience_item(
    block: str,
    experience: dict[str, Any],
) -> str:
    """Render one experience item, including its nested bullets."""
    bullets = experience.get("bullets", [])
    if not isinstance(bullets, list):
        raise ValueError("Each experience 'bullets' field must be a list.")

    bullet_block = _extract_marked_block(block, "EXPERIENCE_BULLET")
    if bullet_block is None:
        raise ValueError(
            "HTML template is missing EXPERIENCE_BULLET markers."
        )

    before, bullet_template, after = bullet_block
    rendered_bullets = "".join(
        _replace_placeholders(
            bullet_template,
            {"experience": {"bullet": bullet}},
        )
        for bullet in bullets
    )

    block = before + rendered_bullets + after
    return _replace_placeholders(block, {"experience": experience})


def _simple_item(prefix: str) -> Callable[[str, dict[str, Any]], str]:
    """Create a renderer for one simple repeated item."""

    def render(block: str, item: dict[str, Any]) -> str:
        normalized = deepcopy(item)

        if prefix == "skill":
            items_text = normalized.get("items_text")
            if not items_text:
                items = normalized.get("items", [])
                if isinstance(items, list):
                    items_text = ", ".join(_string(value) for value in items)
                else:
                    items_text = _string(items)
            normalized["items"] = items_text

        return _replace_placeholders(block, {prefix: normalized})

    return render


def _remove_element_by_class(source: str, class_name: str) -> str:
    """Remove HTML elements carrying a specific class.

    This lightweight helper is intentionally limited to the template's
    non-nested contact elements.
    """
    paired = re.compile(
        rf'<(?P<tag>[a-zA-Z0-9]+)\b'
        rf'(?=[^>]*\bclass=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'])'
        rf'[^>]*>.*?</(?P=tag)>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    self_closing = re.compile(
        rf'<[a-zA-Z0-9]+\b'
        rf'(?=[^>]*\bclass=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'])'
        rf'[^>]*/?>',
        flags=re.IGNORECASE,
    )

    source = paired.sub("", source)
    return self_closing.sub("", source)


def _apply_render_options(
    source: str,
    data: dict[str, Any],
) -> str:
    """Apply optional photo, contact, and additional-section visibility."""
    options = data["render_options"]
    candidate = data["candidate"]
    contact = data["contact"]

    show_photo = bool(options.get("show_photo")) and bool(
        candidate.get("photo_path")
    )

    if show_photo:
        source = source.replace(
            'class="resume no-photo"',
            'class="resume has-photo"',
        )
        source = source.replace(
            'class="resume"',
            'class="resume has-photo"',
            1,
        )
    else:
        source = source.replace(
            'class="resume has-photo"',
            'class="resume no-photo"',
        )
        source = _remove_element_by_class(source, "photo-frame")

    optional_rules = (
        ("show_phone", "phone", "phone-contact"),
        ("show_linkedin", "linkedin_url", "linkedin-contact"),
        ("show_portfolio", "portfolio_url", "portfolio-contact"),
    )

    for option_key, value_key, class_name in optional_rules:
        visible = bool(options.get(option_key)) and bool(contact.get(value_key))
        if not visible:
            source = _remove_element_by_class(source, class_name)

    show_additional = bool(options.get("show_additional")) and bool(
        data.get("additional")
    )
    if not show_additional:
        source = _remove_element_by_class(source, "additional-section")

    return source


def _resolve_photo(
    data: dict[str, Any],
    json_path: Path,
    override_photo: Path | None,
) -> None:
    """Resolve the chosen profile photo to a local file URI."""
    candidate = data["candidate"]

    if override_photo is not None:
        photo = override_photo
    else:
        configured = _string(candidate.get("photo_path")).strip()
        if not configured:
            candidate["photo_path"] = ""
            return

        photo = Path(configured).expanduser()
        if not photo.is_absolute():
            photo = json_path.parent / photo

    if not photo.is_file():
        raise FileNotFoundError(f"Profile photo does not exist: {photo}")

    candidate["photo_path"] = photo.resolve().as_uri()


def _inline_css(template_html: str, css_text: str) -> str:
    """Replace the external stylesheet link with embedded CSS."""
    style_tag = f"<style>\n{css_text}\n</style>"

    if STYLESHEET_LINK_RE.search(template_html):
        return STYLESHEET_LINK_RE.sub(style_tag, template_html, count=1)

    closing_head = template_html.lower().find("</head>")
    if closing_head == -1:
        raise ValueError("HTML template is missing a </head> element.")

    return (
        template_html[:closing_head]
        + style_tag
        + "\n"
        + template_html[closing_head:]
    )


def render_json_to_html(
    json_path: str,
    output_html_path: str,
    template_path: str | None = None,
    css_path: str | None = None,
    photo_path: str | None = None,
) -> str:
    """Render CV content JSON through the selected HTML/CSS template."""
    source_path = Path(json_path).expanduser()
    destination_path = Path(output_html_path).expanduser()
    selected_template = (
        Path(template_path).expanduser()
        if template_path
        else DEFAULT_TEMPLATE_PATH
    )
    selected_css = (
        Path(css_path).expanduser()
        if css_path
        else DEFAULT_CSS_PATH
    )
    override_photo = (
        Path(photo_path).expanduser()
        if photo_path
        else None
    )

    data = _load_json(source_path)
    template_html = _read_utf8(selected_template, "HTML template")
    css_text = _read_utf8(selected_css, "CSS template")

    _resolve_photo(data, source_path, override_photo)

    template_html = _expand_block(
        template_html,
        "EXPERIENCE_ITEM",
        data["experience"],
        _experience_item,
    )
    template_html = _expand_block(
        template_html,
        "EDUCATION_ITEM",
        data["education"],
        _simple_item("education"),
    )
    template_html = _expand_block(
        template_html,
        "SKILL_GROUP",
        data["skills"],
        _simple_item("skill"),
    )
    template_html = _expand_block(
        template_html,
        "LANGUAGE_ITEM",
        data["languages"],
        _simple_item("language"),
    )
    template_html = _expand_block(
        template_html,
        "CERTIFICATION_ITEM",
        data["certifications"],
        _simple_item("certification"),
    )
    template_html = _expand_block(
        template_html,
        "PROJECT_ITEM",
        data["projects"],
        _simple_item("project"),
    )
    template_html = _expand_block(
        template_html,
        "ADDITIONAL_ITEM",
        data["additional"],
        _simple_item("additional"),
    )

    template_html = _apply_render_options(template_html, data)
    template_html = _replace_placeholders(template_html, data)
    template_html = _inline_css(template_html, css_text)

    unresolved = sorted(set(PLACEHOLDER_RE.findall(template_html)))
    if unresolved:
        raise ValueError(
            "Generated HTML still contains unresolved placeholders: "
            + ", ".join(unresolved)
        )

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(template_html, encoding="utf-8")

    return str(destination_path.resolve())


def main() -> None:
    """Run the JSON-to-HTML action from the terminal."""
    parser = argparse.ArgumentParser(
        description=(
            "Render structured CV JSON through an external "
            "HTML and CSS template."
        )
    )
    parser.add_argument("json_path", help="Path to the CV content JSON")
    parser.add_argument(
        "output_html_path",
        help="Path for the generated HTML",
    )
    parser.add_argument(
        "--template",
        dest="template_path",
        help=(
            "HTML template path; defaults to "
            "backend/templates/template_01.html"
        ),
    )
    parser.add_argument(
        "--css",
        dest="css_path",
        help=(
            "CSS template path; defaults to "
            "backend/templates/template_01.css"
        ),
    )
    parser.add_argument(
        "--photo",
        dest="photo_path",
        help="Optional profile-photo override",
    )

    args = parser.parse_args()

    result = render_json_to_html(
        json_path=args.json_path,
        output_html_path=args.output_html_path,
        template_path=args.template_path,
        css_path=args.css_path,
        photo_path=args.photo_path,
    )
    print(result)


if __name__ == "__main__":
    main()
