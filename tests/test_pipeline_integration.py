# Integration-test Kiron's real orchestration and renderers without Gemini calls or sending email.

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from backend.pipelines import run_cv_job as pipeline


EVALUATION_FIXTURE = {
    "overall_recommendation": "Yes",
    "hr_screening_probability": 72,
    "reasoning": "The candidate shows relevant evidence for the role.",
    "good_match": "The strongest match is practical project experience.",
    "gaps": "Some role-specific evidence could be clearer.",
    "final_verdict": (
        "The candidate would reasonably progress to the next stage. "
        "The profile shows enough relevant evidence for an interview."
    ),
    "kiron_support": "Kiron can help strengthen the remaining evidence.",
}

CV_FIXTURE = {
    "candidate": {
        "full_name": "Integration Test Candidate",
        "professional_title": "ML Engineer",
        "summary": (
            "ML engineer focused on practical AI systems. "
            "Builds small, testable automation and data workflows."
        ),
    },
    "contact": {
        "email": "candidate@example.com",
        "phone": None,
        "location": "Test City",
        "linkedin_url": None,
        "portfolio_url": None,
    },
    "experience": [
        {
            "title": "ML Engineering Project",
            "company": "Test Studio",
            "location": "Test City",
            "start_date": "2025",
            "end_date": None,
            "date_range": "2025–Present",
            "bullets": [
                "Built a testable AI-assisted document workflow.",
                "Automated repeatable validation and rendering steps.",
            ],
        }
    ],
    "education": [
        {
            "qualification": "Practical ML Engineering",
            "institution": "Test Lab",
            "date": "2025",
        }
    ],
    "skills": [
        {
            "category": "Core",
            "items": ["Python", "ML", "APIs", "Testing", "Automation"],
            "items_text": "Python, ML, APIs, Testing, Automation",
            "icon_id": "skills",
        }
    ],
    "languages": [{"name": "English", "proficiency": "Professional"}],
    "certifications": [],
    "projects": [
        {
            "title": "Kiron Integration Test",
            "description": "Validates the complete local rendering pipeline.",
            "icon_id": "projects",
        }
    ],
    "additional": [
        {
            "type": "highlight",
            "text": "End-to-end pipeline validation",
        }
    ],
}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class KironPipelineIntegrationTest(unittest.TestCase):
    """Exercise orchestration plus real HTML/PDF rendering with deterministic AI fixtures."""

    def test_pipeline_renders_both_pdfs_and_reaches_email_stage(self) -> None:
        real_run = pipeline._run
        email_calls: list[tuple[str, Path, Path]] = []

        with tempfile.TemporaryDirectory(prefix="kiron-integration-test-") as temp:
            temp_root = Path(temp)
            inputs = temp_root / "inputs"
            jobs = temp_root / "jobs"
            inputs.mkdir()

            job_offer = inputs / "job_offer.txt"
            candidate_material = inputs / "candidate_material.txt"
            job_offer.write_text(
                "Seeking an ML engineer to build reliable AI workflows.\n",
                encoding="utf-8",
            )
            candidate_material.write_text(
                "Candidate has Python, ML, API, testing, and automation experience.\n",
                encoding="utf-8",
            )

            def controlled_run(command: list[str]) -> None:
                """Replace only external AI/email effects; keep render stages real."""
                joined = " ".join(command)

                if "backend.actions.generate_hiring_criteria" in joined:
                    output = Path(command[command.index("--output") + 1])
                    _write_json(output, {"test": "hiring criteria"})
                    return

                if "backend.actions.generate_matching_evaluation" in joined:
                    output = Path(command[command.index("--output") + 1])
                    _write_json(output, EVALUATION_FIXTURE)
                    return

                if "backend.actions.generate_targeted_cv" in joined:
                    output = Path(command[command.index("--output") + 1])
                    _write_json(output, CV_FIXTURE)
                    return

                if "backend.actions.send_result_email" in joined:
                    module_index = command.index("backend.actions.send_result_email")
                    recipient = command[module_index + 1]
                    evaluation_pdf = Path(command[module_index + 2])
                    cv_pdf = Path(command[module_index + 3])
                    email_calls.append((recipient, evaluation_pdf, cv_pdf))
                    return

                # HTML and Playwright PDF rendering remain real subprocesses.
                real_run(command)

            with (
                patch.object(pipeline, "TEMP_ROOT", jobs),
                patch.object(pipeline, "_run", side_effect=controlled_run),
            ):
                result = pipeline.run_cv_job(
                    job_offer_path=str(job_offer),
                    candidate_material_path=str(candidate_material),
                    recipient_email="integration@example.com",
                    job_id="integration_test",
                )

            job_dir = Path(result["job_dir"])
            evaluation_pdf = Path(result["evaluation_pdf"])
            cv_pdf = Path(result["cv_pdf"])

            self.assertTrue(job_dir.is_dir())
            self.assertGreater(evaluation_pdf.stat().st_size, 0)
            self.assertGreater(cv_pdf.stat().st_size, 0)

            for expected in (
                "hiring_criteria.json",
                "matching_evaluation.json",
                "cv_data.json",
                "evaluation.html",
                "evaluation.pdf",
                "cv.html",
                "cv.pdf",
                "job_manifest.json",
            ):
                self.assertTrue(
                    (job_dir / expected).is_file(),
                    f"Missing expected pipeline artifact: {expected}",
                )

            manifest = json.loads(
                (job_dir / "job_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["status"], "complete")

            self.assertEqual(len(email_calls), 1)
            recipient, emailed_evaluation, emailed_cv = email_calls[0]
            self.assertEqual(recipient, "integration@example.com")
            self.assertEqual(emailed_evaluation.resolve(), evaluation_pdf.resolve())
            self.assertEqual(emailed_cv.resolve(), cv_pdf.resolve())

            # A PDF should begin with the standard PDF file signature.
            self.assertEqual(evaluation_pdf.read_bytes()[:4], b"%PDF")
            self.assertEqual(cv_pdf.read_bytes()[:4], b"%PDF")


if __name__ == "__main__":
    unittest.main()
