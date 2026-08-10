# Orchestrate one complete Kiron CV job from source inputs to two final PDFs and optional email delivery.

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMP_ROOT = Path(tempfile.gettempdir()) / "kiron-cv-job-matcher"


def _run(command: list[str]) -> None:
    """Run one pipeline stage and stop immediately if it fails."""
    print()
    print("$ " + " ".join(command))
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def _require_file(path: Path, label: str) -> Path:
    """Validate one required input file."""
    resolved = path.expanduser().resolve()

    if not resolved.is_file():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")

    return resolved


def _require_dir(path: Path, label: str) -> Path:
    """Validate one required directory."""
    resolved = path.expanduser().resolve()

    if not resolved.is_dir():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")

    return resolved


def _new_job_id() -> str:
    """Create a short unique runtime job identifier."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    return f"{timestamp}_{suffix}"


def run_cv_job(
    job_offer_path: str,
    candidate_material_path: str,
    kiron_assets_dir: str | None = None,
    photo_path: str | None = None,
    recipient_email: str | None = None,
    job_id: str | None = None,
) -> dict[str, str]:
    """Run all three Gemini calls, render both PDFs, and optionally email them."""
    job_offer = _require_file(Path(job_offer_path), "Job offer")
    candidate_material = _require_file(
        Path(candidate_material_path),
        "Candidate material",
    )
    assets_dir = _require_dir(
        (
            Path(kiron_assets_dir)
            if kiron_assets_dir is not None
            else PROJECT_ROOT / "backend" / "assets" / "kiron" / "transparent"
        ),
        "Kiron assets directory",
    )

    photo: Path | None = None
    if photo_path:
        photo = _require_file(Path(photo_path), "Profile photo")

    runtime_job_id = job_id or _new_job_id()
    job_dir = TEMP_ROOT / runtime_job_id

    if job_dir.exists():
        raise FileExistsError(
            f"Runtime job directory already exists: {job_dir}"
        )

    job_dir.mkdir(parents=True, exist_ok=False)

    hiring_criteria = job_dir / "hiring_criteria.json"
    matching_evaluation = job_dir / "matching_evaluation.json"
    cv_data = job_dir / "cv_data.json"

    evaluation_html = job_dir / "evaluation.html"
    evaluation_pdf = job_dir / "evaluation.pdf"

    cv_html = job_dir / "cv.html"
    cv_pdf = job_dir / "cv.pdf"

    hiring_state = job_dir / "hiring_criteria_retry_state.json"
    matching_state = job_dir / "matching_evaluation_retry_state.json"
    cv_state = job_dir / "targeted_cv_retry_state.json"

    manifest_path = job_dir / "job_manifest.json"

    manifest = {
        "job_id": runtime_job_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "inputs": {
            "job_offer": str(job_offer),
            "candidate_material": str(candidate_material),
            "photo_supplied": photo is not None,
        },
        "outputs": {},
    }

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    try:
        print(f"=== Kiron CV Job: {runtime_job_id} ===")

        print("\n1/8 Generate hiring criteria")
        _run(
            [
                sys.executable,
                "-m",
                "backend.actions.generate_hiring_criteria",
                str(job_offer),
                "--output",
                str(hiring_criteria),
                "--state-path",
                str(hiring_state),
            ]
        )

        print("\n2/8 Generate matching evaluation")
        _run(
            [
                sys.executable,
                "-m",
                "backend.actions.generate_matching_evaluation",
                str(hiring_criteria),
                str(candidate_material),
                "--output",
                str(matching_evaluation),
                "--state-path",
                str(matching_state),
            ]
        )

        print("\n3/8 Generate targeted CV data")
        _run(
            [
                sys.executable,
                "-m",
                "backend.actions.generate_targeted_cv",
                str(hiring_criteria),
                str(candidate_material),
                "--output",
                str(cv_data),
                "--state-path",
                str(cv_state),
            ]
        )

        print("\n4/8 Render evaluation HTML")
        _run(
            [
                sys.executable,
                "-m",
                "backend.actions.render_evaluation_to_html",
                str(matching_evaluation),
                str(evaluation_html),
                "--assets-dir",
                str(assets_dir),
            ]
        )

        print("\n5/8 Render evaluation PDF")
        _run(
            [
                sys.executable,
                str(PROJECT_ROOT / "backend" / "actions" / "render_html_to_pdf.py"),
                str(evaluation_html),
                str(evaluation_pdf),
            ]
        )

        print("\n6/8 Render CV HTML")
        cv_render_command = [
            sys.executable,
            "-m",
            "backend.actions.render_json_to_html",
            str(cv_data),
            str(cv_html),
        ]

        if photo is not None:
            cv_render_command.extend(["--photo", str(photo)])

        _run(cv_render_command)

        print("\n7/8 Render CV PDF")
        _run(
            [
                sys.executable,
                str(PROJECT_ROOT / "backend" / "actions" / "render_html_to_pdf.py"),
                str(cv_html),
                str(cv_pdf),
            ]
        )

        if recipient_email:
            print("\n8/8 Email final PDFs")
            _run(
                [
                    sys.executable,
                    "-m",
                    "backend.actions.send_result_email",
                    recipient_email,
                    str(evaluation_pdf),
                    str(cv_pdf),
                ]
            )
        else:
            print("\n8/8 Email skipped — no recipient supplied")

        result = {
            "job_id": runtime_job_id,
            "job_dir": str(job_dir.resolve()),
            "hiring_criteria_json": str(hiring_criteria.resolve()),
            "matching_evaluation_json": str(matching_evaluation.resolve()),
            "cv_data_json": str(cv_data.resolve()),
            "evaluation_pdf": str(evaluation_pdf.resolve()),
            "cv_pdf": str(cv_pdf.resolve()),
        }

        manifest["status"] = "complete"
        manifest["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["outputs"] = result

        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        print()
        print("✓ Kiron job complete")
        print(f"Evaluation PDF: {evaluation_pdf.resolve()}")
        print(f"CV PDF:         {cv_pdf.resolve()}")

        return result

    except Exception:
        manifest["status"] = "failed"
        manifest["failed_at_utc"] = datetime.now(timezone.utc).isoformat()

        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        raise


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Run one complete Kiron CV job: "
            "job offer + candidate material -> evaluation PDF + targeted CV PDF."
        )
    )

    parser.add_argument(
        "job_offer_path",
        help="UTF-8 job-offer text file",
    )
    parser.add_argument(
        "candidate_material_path",
        help="UTF-8 candidate CV/career-material file",
    )
    parser.add_argument(
        "--kiron-assets-dir",
        help=(
            "Directory containing Kiron's final transparent PNG assets; "
            "defaults to backend/assets/kiron/transparent"
        ),
    )
    parser.add_argument(
        "--photo",
        dest="photo_path",
        help="Optional profile-photo file",
    )
    parser.add_argument(
        "--email",
        dest="recipient_email",
        help="Optional recipient email for the two final PDFs",
    )
    parser.add_argument(
        "--job-id",
        help="Optional explicit job id; otherwise one is generated automatically",
    )

    args = parser.parse_args()

    result = run_cv_job(
        job_offer_path=args.job_offer_path,
        candidate_material_path=args.candidate_material_path,
        kiron_assets_dir=args.kiron_assets_dir,
        photo_path=args.photo_path,
        recipient_email=args.recipient_email,
        job_id=args.job_id,
    )

    print()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(
            f"\nERROR: pipeline stage failed with exit code {exc.returncode}",
            file=sys.stderr,
        )
        raise SystemExit(exc.returncode)
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
