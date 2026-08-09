# Build deterministic Kiron SVG icons from the canonical JSON geometry library.

from __future__ import annotations

import argparse
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import sys
from typing import Any
import xml.etree.ElementTree as ET


SUPPORTED_TYPES = {"path", "circle", "ellipse", "rect"}

FACE_IDS = {"eye", "eye_highlight", "cheek", "mouth", "nostril"}
HEAD_GROUP_IDS = {"head", "muzzle_highlight", *FACE_IDS}
BODY_GROUP_IDS = {
    "body",
    "body_spot_1",
    "body_spot_2",
    "body_spot_3",
}
NECK_GROUP_IDS = {
    "neck",
    "neck_spot_1",
    "neck_spot_2",
    "neck_spot_3",
}
FRONT_LEG_IDS = {"front_leg_near", "front_leg_far"}
REAR_LEG_IDS = {"rear_leg_near", "rear_leg_far"}


def _warn(message: str) -> None:
    """Print one non-fatal renderer warning."""
    print(f"[kiron] warning: {message}", file=sys.stderr)


def _load_library(path: Path) -> dict[str, Any]:
    """Load and minimally validate the Kiron icon library."""
    if not path.is_file():
        raise FileNotFoundError(f"Kiron icon library does not exist: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError(f"Kiron library is not valid UTF-8: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid Kiron JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc

    required = (
        "library",
        "default_style",
        "base_character",
        "expression_variants",
        "pose_variants",
        "ui_icon_roles",
        "prop_library",
        "export_rules",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(
            "Kiron library is missing required keys: " + ", ".join(missing)
        )

    elements = data["base_character"].get("elements")
    if not isinstance(elements, list):
        raise ValueError("base_character.elements must be a list.")

    return data


def _merge_transform(existing: str | None, new: str | None) -> str | None:
    """Combine SVG transforms without discarding existing geometry transforms."""
    parts = [part for part in (existing, new) if part]
    return " ".join(parts) if parts else None


def _apply_element_override(
    element: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    """Apply one expression override to one copied geometry element."""
    result = deepcopy(element)

    if override.get("visible") is False:
        result["visible"] = False
        return result

    for key, value in override.items():
        if key == "visible":
            result["visible"] = bool(value)
        else:
            result[key] = deepcopy(value)

    return result


def _apply_expression(
    elements: list[dict[str, Any]],
    expressions: dict[str, Any],
    expression_name: str,
) -> list[dict[str, Any]]:
    """Apply one named facial-expression variant."""
    variant = expressions.get(expression_name)
    if not isinstance(variant, dict):
        _warn(
            f"Unknown expression '{expression_name}', "
            "falling back to 'friendly'."
        )
        variant = expressions.get("friendly", {})

    overrides = variant.get("overrides", {})
    if not isinstance(overrides, dict):
        return elements

    copied = deepcopy(elements)

    for index, element in enumerate(copied):
        element_id = element.get("id")
        override = overrides.get(element_id)

        if isinstance(override, dict):
            copied[index] = _apply_element_override(element, override)

    head_transform = overrides.get("head_transform")
    if isinstance(head_transform, str):
        for element in copied:
            if element.get("id") in HEAD_GROUP_IDS:
                element["transform"] = _merge_transform(
                    element.get("transform"),
                    head_transform,
                )

    return copied


def _apply_transform_to_ids(
    elements: list[dict[str, Any]],
    ids: set[str],
    transform: str,
) -> None:
    """Apply one transform string to selected element ids."""
    for element in elements:
        if element.get("id") in ids:
            element["transform"] = _merge_transform(
                element.get("transform"),
                transform,
            )


def _apply_pose(
    elements: list[dict[str, Any]],
    poses: dict[str, Any],
    pose_name: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """Apply supported pose instructions and return optional expression override."""
    variant = poses.get(pose_name)
    if not isinstance(variant, dict):
        _warn(
            f"Unknown pose '{pose_name}', "
            "falling back to 'standing'."
        )
        return deepcopy(elements), None

    instructions = variant.get("instructions")
    if not isinstance(instructions, dict):
        return deepcopy(elements), None

    copied = deepcopy(elements)

    direct_transform_map: dict[str, set[str]] = {
        "body_transform": BODY_GROUP_IDS,
        "neck_transform": NECK_GROUP_IDS,
        "head_transform": HEAD_GROUP_IDS,
        "front_leg_near_transform": {"front_leg_near"},
        "front_leg_far_transform": {"front_leg_far"},
        "rear_leg_near_transform": {"rear_leg_near"},
        "rear_leg_far_transform": {"rear_leg_far"},
    }

    for instruction, ids in direct_transform_map.items():
        value = instructions.get(instruction)
        if isinstance(value, str):
            _apply_transform_to_ids(copied, ids, value)

    # The designer included semantic pose modes that need geometry before they
    # can be rendered faithfully. Preserve the canonical geometry rather than
    # inventing shapes.
    unsupported_modes = (
        "rear_legs_mode",
        "front_legs_mode",
    )
    for key in unsupported_modes:
        if key in instructions:
            _warn(
                f"Pose '{pose_name}' instruction '{key}="
                f"{instructions[key]}' has no explicit geometry; "
                "canonical leg geometry is preserved."
            )

    expression_override = instructions.get("expression")
    if not isinstance(expression_override, str):
        expression_override = None

    return copied, expression_override


def _svg_attributes(element: dict[str, Any]) -> dict[str, str]:
    """Convert one geometry element into SVG-safe string attributes."""
    ignored = {"id", "type", "visible"}
    attrs: dict[str, str] = {}

    for key, value in element.items():
        if key in ignored or value is None:
            continue

        svg_key = {
            "stroke_width": "stroke-width",
            "stroke_linecap": "stroke-linecap",
            "stroke_linejoin": "stroke-linejoin",
        }.get(key, key)

        attrs[svg_key] = str(value)

    return attrs


def _element_to_svg(element: dict[str, Any]) -> ET.Element | None:
    """Convert one supported structured geometry element into XML."""
    if element.get("visible") is False:
        return None

    element_type = element.get("type")
    if element_type not in SUPPORTED_TYPES:
        _warn(
            f"Skipping unsupported SVG element type "
            f"{element_type!r} for id {element.get('id')!r}."
        )
        return None

    node = ET.Element(str(element_type))
    for key, value in _svg_attributes(element).items():
        node.set(key, value)

    if element.get("id"):
        node.set("data-kiron-id", str(element["id"]))

    return node


def _build_geometry_for_role(
    library: dict[str, Any],
    role_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Resolve base character, pose, expression, and prop for one UI role."""
    roles = library["ui_icon_roles"]
    role = roles.get(role_id)

    if not isinstance(role, dict):
        fallback_id = "kiron_analysis"
        _warn(
            f"Unknown icon role '{role_id}', "
            f"falling back to '{fallback_id}'."
        )
        role_id = fallback_id
        role = roles.get(role_id)

    if not isinstance(role, dict):
        raise ValueError("No valid fallback Kiron UI role is available.")

    elements = deepcopy(library["base_character"]["elements"])

    pose_name = str(role.get("pose", "standing"))
    elements, pose_expression = _apply_pose(
        elements,
        library["pose_variants"],
        pose_name,
    )

    expression_name = (
        pose_expression
        if pose_expression
        else str(role.get("expression", "friendly"))
    )
    elements = _apply_expression(
        elements,
        library["expression_variants"],
        expression_name,
    )

    prop_name = role.get("prop")
    if prop_name:
        prop = library["prop_library"].get(str(prop_name))
        if not isinstance(prop, dict):
            _warn(
                f"Role '{role_id}' references unknown prop "
                f"{prop_name!r}; rendering without prop."
            )
        else:
            prop_elements = prop.get("elements", [])
            if isinstance(prop_elements, list):
                for index, prop_element in enumerate(prop_elements):
                    if not isinstance(prop_element, dict):
                        continue
                    copied = deepcopy(prop_element)
                    copied.setdefault(
                        "id",
                        f"prop_{prop_name}_{index + 1}",
                    )
                    elements.append(copied)

    return elements, role


def build_kiron_svg(
    library_path: str,
    role_id: str,
    output_path: str | None = None,
) -> str:
    """Build one Kiron role icon as self-contained SVG."""
    library_file = Path(library_path).expanduser()
    library = _load_library(library_file)

    elements, role = _build_geometry_for_role(library, role_id)

    svg_rules = library["export_rules"].get("inline_svg", {})
    svg_attrs = svg_rules.get("svg_attributes", {})
    if not isinstance(svg_attrs, dict):
        svg_attrs = {}

    root = ET.Element("svg")
    defaults = {
        "xmlns": "http://www.w3.org/2000/svg",
        "viewBox": library["base_character"].get(
            "viewBox",
            library["library"]["coordinate_system"]["viewBox"],
        ),
        "aria-hidden": "true",
        "focusable": "false",
        "preserveAspectRatio": "xMidYMid meet",
    }
    defaults.update(
        {str(key): str(value) for key, value in svg_attrs.items()}
    )

    for key, value in defaults.items():
        root.set(key, value)

    root.set("data-kiron-role", role_id)
    root.set("data-ui-role", str(role.get("ui_role", "")))
    root.set("data-label", str(role.get("label", role_id)))

    for element in elements:
        if not isinstance(element, dict):
            _warn("Skipping non-object element in geometry list.")
            continue

        node = _element_to_svg(element)
        if node is not None:
            root.append(node)

    ET.indent(root, space="  ")
    svg_text = ET.tostring(
        root,
        encoding="unicode",
        short_empty_elements=True,
    )
    svg_text = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg_text + "\n"

    if output_path:
        destination = Path(output_path).expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(svg_text, encoding="utf-8")

    return svg_text


def build_all_icons(
    library_path: str,
    output_dir: str,
) -> list[Path]:
    """Build every UI icon role into one SVG file per role."""
    library_file = Path(library_path).expanduser()
    library = _load_library(library_file)
    destination = Path(output_dir).expanduser()
    destination.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    for role_id in library["ui_icon_roles"]:
        path = destination / f"{role_id}.svg"
        build_kiron_svg(
            str(library_file),
            role_id,
            str(path),
        )
        outputs.append(path.resolve())

    return outputs


def main() -> None:
    """Run the Kiron SVG builder from the terminal."""
    parser = argparse.ArgumentParser(
        description=(
            "Build deterministic Kiron SVG icons from "
            "kiron_icon_library.json."
        )
    )
    parser.add_argument(
        "--library",
        default=str(
            Path(__file__).with_name("kiron_icon_library.json")
        ),
        help="Path to kiron_icon_library.json",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--icon",
        dest="role_id",
        help="Build one UI role, for example kiron_analysis",
    )
    mode.add_argument(
        "--all",
        action="store_true",
        help="Build every UI role",
    )

    parser.add_argument(
        "--output",
        help="Output SVG path when using --icon",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).with_name("generated")),
        help="Output directory when using --all",
    )

    args = parser.parse_args()

    if args.all:
        outputs = build_all_icons(
            args.library,
            args.output_dir,
        )
        for output in outputs:
            print(output)
        return

    svg = build_kiron_svg(
        args.library,
        args.role_id,
        args.output,
    )

    if args.output:
        print(Path(args.output).expanduser().resolve())
    else:
        print(svg)


if __name__ == "__main__":
    main()
