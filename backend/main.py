# Expose Kiron's synchronous CV pipeline through a small FastAPI HTTP API.

from __future__ import annotations

import logging
import re
import shutil
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, StrictBool, field_validator

from backend.pipelines.run_cv_job import TEMP_ROOT, run_cv_job


JOB_OFFER_MAX_CHARS = 30_000
CANDIDATE_MATERIAL_MAX_CHARS = 60_000
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

logger = logging.getLogger(__name__)

app = FastAPI(title="Kiron CV Job API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://cv-job-matcher-gwls.vercel.app",
    ],
    allow_origin_regex=r"https://kiron-[a-z0-9-]+-hormus\.vercel\.app",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class JobRequest(BaseModel):
    """Validated frontend request for one complete Kiron CV job."""

    job_offer_text: str = Field(max_length=JOB_OFFER_MAX_CHARS)
    candidate_material_text: str = Field(
        max_length=CANDIDATE_MATERIAL_MAX_CHARS,
    )
    email: str
    consent_confirmed: StrictBool

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Require a practical email address without optional dependencies."""
        normalized = value.strip()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("A valid email address is required.")
        return normalized


@app.get("/health")
def health() -> dict[str, str]:
    """Return a minimal service-health response."""
    return {"status": "ok"}


@app.post("/api/jobs")
def create_job(request: JobRequest) -> dict[str, str]:
    """Run one Kiron CV job synchronously and return its public status."""
    if not request.job_offer_text.strip():
        raise HTTPException(status_code=400, detail="Job offer text is required.")
    if not request.candidate_material_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Candidate material text is required.",
        )
    if request.consent_confirmed is not True:
        raise HTTPException(
            status_code=400,
            detail="Consent must be confirmed.",
        )

    job_id = uuid.uuid4().hex
    staged_job_offer = TEMP_ROOT / f".{job_id}_input_job_offer.txt"
    staged_candidate_material = (
        TEMP_ROOT / f".{job_id}_input_candidate_material.txt"
    )
    job_dir = TEMP_ROOT / job_id

    try:
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        staged_job_offer.write_text(request.job_offer_text, encoding="utf-8")
        staged_candidate_material.write_text(
            request.candidate_material_text,
            encoding="utf-8",
        )

        run_cv_job(
            job_offer_path=str(staged_job_offer),
            candidate_material_path=str(staged_candidate_material),
            recipient_email=request.email,
            job_id=job_id,
        )
    except Exception:
        logger.exception("Kiron CV job failed for job_id=%s", job_id)
        raise HTTPException(
            status_code=500,
            detail="Kiron could not complete the application job.",
        ) from None
    finally:
        staged_job_offer.unlink(missing_ok=True)
        staged_candidate_material.unlink(missing_ok=True)
        shutil.rmtree(job_dir, ignore_errors=True)

    return {
        "status": "complete",
        "job_id": job_id,
        "message": (
            "Kiron finished your application and sent the results by email."
        ),
    }
