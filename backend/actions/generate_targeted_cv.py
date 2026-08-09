# Generate a truthful job-targeted CV as structured JSON.

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Mapping

from backend.ai.ai_job_runner import run_ai_job
from backend.ai.model_gate import generate_text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = PROJECT_ROOT / "schemas" / "03_Job-Targeted_CV.md"
TASK_GROUP = "targeted_cv_generation"
FENCED_JSON_PATTERN = re.compile(
    r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
    flags=re.IGNORECASE | re.DOTALL,
)


def _read_utf8(path: Path, label: str) -> str:
    """Read a required UTF-8 text file."""
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} is not valid UTF-8: {path}") from error


def _json_object_text(value: Mapping[str, Any] | str) -> str:
    """Normalize hiring criteria supplied as a dictionary or JSON string."""
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError("Hiring criteria input is not valid JSON.") from error
        if not isinstance(parsed, dict):
            raise ValueError("Hiring criteria JSON must contain one object.")
        value = parsed
    return json.dumps(dict(value), ensure_ascii=False, indent=2)


def _parse_json_object(response: str) -> dict[str, Any]:
    """Parse a Gemini response as one JSON object."""
    match = FENCED_JSON_PATTERN.fullmatch(response)
    json_text = match.group(1) if match else response.strip()
    try:
        result = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Gemini returned invalid JSON for targeted CV generation: "
            f"line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error
    if not isinstance(result, dict):
        raise ValueError(
            "Gemini returned invalid JSON for targeted CV generation: "
            "the top-level value must be an object."
        )
    return result


def _build_prompt(
    hiring_criteria: Mapping[str, Any] | str,
    candidate_career_material_text: str,
) -> str:
    """Append job analysis and raw CV materials to the contract."""
    contract = _read_utf8(PROMPT_PATH, "Targeted CV prompt")
    return (
        f"{contract.rstrip()}\n\n"
        "INPUT\n\n"
        "JOB ANALYSIS\n"
        f"{_json_object_text(hiring_criteria)}\n\n"
        "RAW CV MATERIALS\n"
        f"{candidate_career_material_text}\n"
    )


def _state_path(output_json_path: str | Path | None, state_path: str | Path | None) -> Path:
    """Resolve the persistent retry-state path for this action."""
    if state_path is not None:
        return Path(state_path).expanduser()
    if output_json_path is not None:
        output_path = Path(output_json_path).expanduser()
        return output_path.with_name(f"{output_path.name}.ai_job_state.json")
    return PROJECT_ROOT / ".ai_jobs" / f"{TASK_GROUP}.json"


def generate_targeted_cv(
    hiring_criteria: Mapping[str, Any] | str,
    candidate_career_material_text: str,
    output_json_path: str | Path | None = None,
    *,
    state_path: str | Path | None = None,
) -> dict[str, Any]:
    """Generate a targeted CV, optionally write it, and return the object."""
    prompt = _build_prompt(hiring_criteria, candidate_career_material_text)
    result = run_ai_job(
        job_name=TASK_GROUP,
        job_callable=lambda: _parse_json_object(generate_text(TASK_GROUP, prompt)),
        state_path=_state_path(output_json_path, state_path),
        provider_name="Gemini",
    )

    if output_json_path is not None:
        destination = Path(output_json_path).expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return result


def main() -> None:
    """Run the targeted-CV action from local UTF-8 input files."""
    parser = argparse.ArgumentParser(description="Generate a Kiron job-targeted CV.")
    parser.add_argument("hiring_criteria_path", help="Hiring criteria JSON file")
    parser.add_argument("candidate_material_path", help="UTF-8 candidate material file")
    parser.add_argument("--output", help="Optional output JSON path")
    parser.add_argument("--state-path", help="Optional AI retry-state JSON path")
    args = parser.parse_args()

    result = generate_targeted_cv(
        _read_utf8(Path(args.hiring_criteria_path).expanduser(), "Hiring criteria"),
        _read_utf8(Path(args.candidate_material_path).expanduser(), "Candidate material"),
        args.output,
        state_path=args.state_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
