"""Persistent retry runner for provider-independent AI jobs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
import time
from typing import Callable, TypeVar

from backend.ai.retry_policy import (
    RetryDecision,
    RetryPolicy,
    classify_ai_error,
    should_retry,
)


T = TypeVar("T")
STATE_SCHEMA_VERSION = "1.0"
ALLOWED_STATUSES = {
    "running",
    "waiting_retry",
    "succeeded",
    "failed",
    "cancelled",
}
SAFE_JOB_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class AIJobStateError(RuntimeError):
    """Raised when an AI job state file is malformed or unsafe."""


def default_managed_folder_ai_job_path(
    target_folder: Path,
    job_name: str,
) -> Path:
    """Return the default managed-folder AI job state path."""
    validate_job_name(job_name)
    return target_folder.expanduser().resolve() / "_orsi" / "ai_jobs" / f"{job_name}.json"


def validate_job_name(job_name: str) -> None:
    """Require a safe simple job name."""
    if not SAFE_JOB_NAME_PATTERN.fullmatch(job_name):
        raise AIJobStateError(
            "AI job name must contain only letters, digits, underscore, or hyphen."
        )


def utc_now(now_function: Callable[[], datetime] | None) -> datetime:
    """Return a timezone-aware UTC datetime."""
    value = now_function() if now_function is not None else datetime.now(UTC)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def isoformat_z(value: datetime) -> str:
    """Format a datetime as UTC ISO-8601 with Z."""
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    """Parse a stored UTC timestamp."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def new_state(job_name: str, now: datetime) -> dict[str, object]:
    """Create a new AI job state object."""
    now_text = isoformat_z(now)
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "job_name": job_name,
        "status": "running",
        "attempt": 0,
        "started_at": now_text,
        "updated_at": now_text,
        "last_attempt_at": None,
        "last_error_category": None,
        "last_error_message": None,
        "provider_error_details": None,
        "next_retry_at": None,
        "completed_at": None,
    }


def validate_state(state: dict[str, object], job_name: str) -> None:
    """Validate an existing AI job state object."""
    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        raise AIJobStateError("AI job state schema_version is invalid.")

    if state.get("job_name") != job_name:
        raise AIJobStateError("AI job state job_name does not match.")

    status = state.get("status")
    if status not in ALLOWED_STATUSES:
        raise AIJobStateError("AI job state status is invalid.")

    attempt = state.get("attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 0:
        raise AIJobStateError("AI job state attempt is invalid.")

    started_at = state.get("started_at")
    if not isinstance(started_at, str):
        raise AIJobStateError("AI job state started_at is invalid.")
    parse_time(started_at)


def load_state(state_path: Path, job_name: str, now: datetime) -> dict[str, object]:
    """Load or create persistent job state."""
    if not state_path.exists():
        return new_state(job_name, now)

    try:
        value = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise AIJobStateError("AI job state file is malformed.") from error

    if not isinstance(value, dict):
        raise AIJobStateError("AI job state file must contain a JSON object.")

    validate_state(value, job_name)

    if value.get("status") == "succeeded":
        raise AIJobStateError(
            "AI job state is already succeeded; reset state before rerun."
        )

    return value


def write_state_atomic(state_path: Path, state: dict[str, object]) -> None:
    """Write state JSON atomically."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=state_path.parent,
        delete=False,
    ) as output:
        temporary_path = Path(output.name)
        json.dump(state, output, ensure_ascii=False, indent=2)
        output.write("\n")

    temporary_path.replace(state_path)


def emit_progress(
    *,
    progress_callback: Callable[[dict[str, object]], None] | None,
    state: dict[str, object],
    provider_name: str,
    event: str,
    max_attempts: int,
    error_message: str | None = None,
    retry_delay_seconds: int | None = None,
    next_retry_time: str | None = None,
    attempt_number: int | None = None,
) -> None:
    """Emit one structured event containing only safe progress fields."""
    if progress_callback is None:
        return

    status = state.get("status")
    provider_message = None
    if status == "waiting_retry":
        provider_message = f"{provider_name} is currently busy..."

    progress_callback(
        {
            "event": event,
            "job_name": state.get("job_name"),
            "provider_name": provider_name,
            "status": state.get("status"),
            "attempt": attempt_number or state.get("attempt"),
            "max_attempts": max_attempts,
            "error_message": error_message,
            "retry_delay_seconds": retry_delay_seconds,
            "next_retry_time": next_retry_time,
            "last_error_category": state.get("last_error_category"),
            "provider_error_details": state.get("provider_error_details"),
            "next_retry_at": state.get("next_retry_at"),
            "provider_message": provider_message,
        }
    )


def mark_failure(
    *,
    state: dict[str, object],
    decision: RetryDecision,
    now: datetime,
    error: Exception | None = None,
) -> None:
    """Persist safe failure classification fields in state."""
    state["updated_at"] = isoformat_z(now)
    state["last_error_category"] = decision.category
    state["last_error_message"] = decision.safe_message
    details = getattr(error, "provider_details", None)
    state["provider_error_details"] = details if isinstance(details, dict) else None


def run_ai_job(
    *,
    job_name: str,
    job_callable: Callable[[], T],
    state_path: Path,
    policy: RetryPolicy | None = None,
    sleep_function: Callable[[float], None] = time.sleep,
    now_function: Callable[[], datetime] | None = None,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    provider_name: str = "AI provider",
) -> T:
    """Run an AI job with persistent retry state."""
    validate_job_name(job_name)
    active_policy = policy or RetryPolicy()
    state_file = state_path.expanduser().resolve()
    state = load_state(state_file, job_name, utc_now(now_function))

    while True:
        if int(state["attempt"]) > 0:
            emit_progress(
                progress_callback=progress_callback,
                state=state,
                provider_name=provider_name,
                event="retry_started",
                max_attempts=active_policy.max_attempts,
                error_message=(
                    str(state["last_error_message"])
                    if state.get("last_error_message")
                    else None
                ),
                next_retry_time=(
                    str(state["next_retry_at"])
                    if state.get("next_retry_at")
                    else None
                ),
                attempt_number=int(state["attempt"]) + 1,
            )
        now = utc_now(now_function)
        state["attempt"] = int(state["attempt"]) + 1
        state["provider_name"] = provider_name
        state["status"] = "running"
        state["updated_at"] = isoformat_z(now)
        state["last_attempt_at"] = isoformat_z(now)
        state["next_retry_at"] = None
        write_state_atomic(state_file, state)
        emit_progress(
            progress_callback=progress_callback,
            state=state,
            provider_name=provider_name,
            event="attempt_started",
            max_attempts=active_policy.max_attempts,
        )

        try:
            result = job_callable()
        except KeyboardInterrupt:
            cancelled_at = utc_now(now_function)
            state["status"] = "cancelled"
            state["updated_at"] = isoformat_z(cancelled_at)
            state["completed_at"] = None
            state["next_retry_at"] = None
            write_state_atomic(state_file, state)
            emit_progress(
                progress_callback=progress_callback,
                state=state,
                provider_name=provider_name,
                event="job_failed",
                max_attempts=active_policy.max_attempts,
                error_message="AI job was cancelled.",
            )
            raise
        except Exception as error:
            failed_at = utc_now(now_function)
            decision = classify_ai_error(error)
            mark_failure(
                state=state,
                decision=decision,
                now=failed_at,
                error=error,
            )
            emit_progress(
                progress_callback=progress_callback,
                state=state,
                provider_name=provider_name,
                event="attempt_failed",
                max_attempts=active_policy.max_attempts,
                error_message=decision.safe_message,
            )
            elapsed = (
                failed_at - parse_time(str(state["started_at"]))
            ).total_seconds()

            if not should_retry(
                decision=decision,
                attempt_number=int(state["attempt"]),
                elapsed_seconds=elapsed,
                policy=active_policy,
            ):
                state["status"] = "failed"
                state["next_retry_at"] = None
                write_state_atomic(state_file, state)
                emit_progress(
                    progress_callback=progress_callback,
                    state=state,
                    provider_name=provider_name,
                    event="job_failed",
                    max_attempts=active_policy.max_attempts,
                    error_message=decision.safe_message,
                )
                raise

            next_retry = failed_at + timedelta(
                seconds=active_policy.interval_seconds
            )
            state["status"] = "waiting_retry"
            state["next_retry_at"] = isoformat_z(next_retry)
            write_state_atomic(state_file, state)
            emit_progress(
                progress_callback=progress_callback,
                state=state,
                provider_name=provider_name,
                event="waiting_retry",
                max_attempts=active_policy.max_attempts,
                error_message=decision.safe_message,
                retry_delay_seconds=active_policy.interval_seconds,
                next_retry_time=isoformat_z(next_retry),
            )
            sleep_function(active_policy.interval_seconds)
            continue

        completed_at = utc_now(now_function)
        state["status"] = "succeeded"
        state["updated_at"] = isoformat_z(completed_at)
        state["completed_at"] = isoformat_z(completed_at)
        state["next_retry_at"] = None
        state["last_error_category"] = None
        state["last_error_message"] = None
        state["provider_error_details"] = None
        write_state_atomic(state_file, state)
        emit_progress(
            progress_callback=progress_callback,
            state=state,
            provider_name=provider_name,
            event="job_succeeded",
            max_attempts=active_policy.max_attempts,
        )
        return result


def reset_ai_job_state(state_path: Path) -> bool:
    """Delete only the specified AI job state file."""
    resolved = state_path.expanduser().resolve()
    if not resolved.exists():
        return False
    if not resolved.is_file():
        raise AIJobStateError("AI job state path is not a file.")
    resolved.unlink()
    return True
