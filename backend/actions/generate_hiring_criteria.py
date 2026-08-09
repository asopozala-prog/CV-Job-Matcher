# Generate structured hiring criteria from one complete job-posting document.

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

from backend.ai.ai_job_runner import run_ai_job
from backend.ai.model_gate import generate_text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = PROJECT_ROOT / "schemas" / "01_Hiring_Criteria.md"
TASK_GROUP = "hiring_criteria"
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


def _parse_json_object(response: str) -> dict[str, Any]:
    """Parse a Gemini response as one JSON object."""
    match = FENCED_JSON_PATTERN.fullmatch(response)
    json_text = match.group(1) if match else response.strip()
    try:
        result = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Gemini returned invalid JSON for hiring criteria: "
            f"line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error
    if not isinstance(result, dict):
        raise ValueError(
            "Gemini returned invalid JSON for hiring criteria: "
            "the top-level value must be an object."
        )
    return result


def _build_prompt(job_offer_text: str) -> str:
    """Append the complete job posting once to the hiring-criteria contract."""
    contract = _read_utf8(PROMPT_PATH, "Hiring criteria prompt")
    return (
        f"{contract.rstrip()}\n\n"
        "INPUT\n\n"
        "COMPLETE JOB POSTING\n"
        f"{job_offer_text}\n"
    )


def _state_path(output_json_path: str | Path | None, state_path: str | Path | None) -> Path:
    """Resolve the persistent retry-state path for this action."""
    if state_path is not None:
        return Path(state_path).expanduser()
    if output_json_path is not None:
        output_path = Path(output_json_path).expanduser()
        return output_path.with_name(f"{output_path.name}.ai_job_state.json")
    return PROJECT_ROOT / ".ai_jobs" / f"{TASK_GROUP}.json"


def generate_hiring_criteria(
    job_offer_path: str | Path,
    output_json_path: str | Path | None = None,
    *,
    state_path: str | Path | None = None,
) -> dict[str, Any]:
    """Generate hiring criteria, optionally write them, and return the object."""
    source_path = Path(job_offer_path).expanduser()
    prompt = _build_prompt(_read_utf8(source_path, "Job offer"))
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
    """Run the hiring-criteria action from one UTF-8 job-posting file."""
    parser = argparse.ArgumentParser(description="Generate Kiron hiring criteria.")
    parser.add_argument("job_offer_path", help="Complete UTF-8 job-posting file")
    parser.add_argument("--output", help="Optional output JSON path")
    parser.add_argument("--state-path", help="Optional AI retry-state JSON path")
    args = parser.parse_args()

    result = generate_hiring_criteria(
        args.job_offer_path,
        args.output,
        state_path=args.state_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
