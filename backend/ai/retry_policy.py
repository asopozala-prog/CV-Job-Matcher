"""Provider-independent retry classification for local AI jobs."""

from __future__ import annotations

from builtins import TimeoutError as BuiltinTimeoutError
from dataclasses import dataclass
import json
import socket

from backend.ai.model_registry import ModelConfigurationError, ModelGateError


@dataclass(frozen=True)
class RetryDecision:
    """Safe retry classification for one AI error."""

    retryable: bool
    category: str
    safe_message: str


@dataclass(frozen=True)
class RetryPolicy:
    """Persistent retry policy for temporary AI failures."""

    interval_seconds: int = 300
    max_attempts: int = 0
    max_duration_seconds: int = 0


def _error_details(error: Exception) -> str:
    parts = [
        str(error),
        str(getattr(error, "code", "")),
        str(getattr(error, "status_code", "")),
        str(getattr(error, "status", "")),
        str(getattr(error, "message", "")),
        json.dumps(
            getattr(error, "provider_details", {}),
            ensure_ascii=False,
            default=str,
        ),
    ]
    return " ".join(parts).casefold()


def _terminal(category: str, message: str) -> RetryDecision:
    return RetryDecision(
        retryable=False,
        category=category,
        safe_message=message,
    )


def _retryable(category: str, message: str) -> RetryDecision:
    return RetryDecision(
        retryable=True,
        category=category,
        safe_message=message,
    )


def classify_ai_error(error: Exception) -> RetryDecision:
    """Classify one AI exception as retryable or terminal."""
    details = _error_details(error)

    if isinstance(error, ModelConfigurationError):
        return _terminal(
            "configuration_error",
            "AI model configuration is invalid or incomplete.",
        )

    if isinstance(error, (FileNotFoundError, PermissionError, ValueError)):
        return _terminal(
            "input_error",
            "AI job input is invalid or unavailable.",
        )

    if isinstance(error, (TimeoutError, BuiltinTimeoutError, socket.timeout)):
        return _retryable(
            "temporary_timeout",
            "Temporary AI request timeout.",
        )

    terminal_markers = {
        "missing api key": "configuration_error",
        "required environment variable is missing": "configuration_error",
        "unknown ai task group": "configuration_error",
        "unsupported ai provider": "configuration_error",
        "authentication": "authentication_error",
        "unauthorized": "authentication_error",
        "invalid api key": "authentication_error",
        "unsupported model": "configuration_error",
        "not a pdf": "input_error",
        "pdf does not exist": "input_error",
        "input too large": "input_error",
        "input token limit": "input_error",
        "context length exceeded": "input_error",
        "request payload size": "input_error",
        "schema validation": "validation_error",
        "invalid json": "validation_error",
        "not valid json": "validation_error",
        "business-rule": "validation_error",
        "business rule": "validation_error",
        "permanent quota": "quota_exhausted",
    }
    for marker, category in terminal_markers.items():
        if marker in details:
            return _terminal(
                category,
                "AI job failed with a terminal error.",
            )

    retryable_markers = {
        "429": "rate_limit",
        "rate limit": "rate_limit",
        "rate-limit": "rate_limit",
        "ratelimit": "rate_limit",
        "503": "provider_unavailable",
        "unavailable": "provider_unavailable",
        "high demand": "provider_unavailable",
        "temporarily unavailable": "provider_unavailable",
        "provider unavailable": "provider_unavailable",
        "connection reset": "temporary_transport_error",
        "connection aborted": "temporary_transport_error",
        "temporarily failure in name resolution": "temporary_dns_error",
        "temporary failure in name resolution": "temporary_dns_error",
        "dns": "temporary_dns_error",
        "transport": "temporary_transport_error",
        "timeout": "temporary_timeout",
        "timed out": "temporary_timeout",
    }
    for marker, category in retryable_markers.items():
        if marker in details:
            if category == "rate_limit":
                return _retryable(
                    category,
                    "AI provider rate limit reached (HTTP 429).",
                )
            if category == "provider_unavailable":
                return _retryable(
                    category,
                    "AI provider temporarily unavailable (HTTP 503).",
                )
            if category == "temporary_dns_error":
                return _retryable(
                    category,
                    "Temporary network name-resolution failure.",
                )
            if category == "temporary_timeout":
                return _retryable(
                    category,
                    "Temporary AI request timeout.",
                )
            return _retryable(
                category,
                "Temporary AI transport failure.",
            )

    if isinstance(error, ModelGateError):
        return _terminal(
            "provider_error",
            "AI provider request failed.",
        )

    return _terminal(
        "unknown_error",
        "AI job failed with an unknown terminal error.",
    )


def should_retry(
    *,
    decision: RetryDecision,
    attempt_number: int,
    elapsed_seconds: float,
    policy: RetryPolicy,
) -> bool:
    """Return whether another attempt is allowed under the policy."""
    if not decision.retryable:
        return False

    if policy.max_attempts != 0 and attempt_number >= policy.max_attempts:
        return False

    if (
        policy.max_duration_seconds != 0
        and elapsed_seconds + policy.interval_seconds
        > policy.max_duration_seconds
    ):
        return False

    return True
