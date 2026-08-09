"""Gemini provider adapter for plain text generation."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

from backend.ai.model_registry import ModelGateError


PDF_MIME_TYPE = "application/pdf"
GEMINI_REQUEST_TIMEOUT_MS = 600_000
FILE_PROCESSING_POLL_SECONDS = 2.0
FILE_PROCESSING_TIMEOUT_SECONDS = 120.0


class ModelProviderError(ModelGateError):
    """Raised when an AI provider request fails."""

    def __init__(
        self,
        message: str,
        *,
        provider_details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.provider_details = dict(provider_details or {})


def _json_safe(value: Any) -> Any:
    """Return provider data in a form safe for state and progress JSON."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


def extract_gemini_error_details(error: Exception) -> dict[str, Any]:
    """Extract full and normalized structured details from a Gemini exception."""
    raw_details = _json_safe(getattr(error, "details", None))
    response = getattr(error, "response", None)
    http_status = (
        getattr(error, "code", None)
        or getattr(error, "status_code", None)
        or getattr(response, "status_code", None)
    )
    original_message = getattr(error, "message", None) or str(error)
    provider_status = getattr(error, "status", None)
    quota_violations: list[dict[str, Any]] = []
    retry_delay: Any = None

    def visit(value: Any) -> None:
        nonlocal retry_delay
        if isinstance(value, dict):
            type_name = str(value.get("@type", ""))
            violations = value.get("violations")
            if "QuotaFailure" in type_name and isinstance(violations, list):
                for violation in violations:
                    if isinstance(violation, dict):
                        quota_violations.append(
                            {
                                "quota_metric": violation.get(
                                    "quotaMetric", violation.get("quota_metric")
                                ),
                                "quota_id": violation.get(
                                    "quotaId", violation.get("quota_id")
                                ),
                                "quota_dimensions": _json_safe(
                                    violation.get(
                                        "quotaDimensions",
                                        violation.get("quota_dimensions"),
                                    )
                                ),
                            }
                        )
            if "RetryInfo" in type_name:
                retry_delay = value.get("retryDelay", value.get("retry_delay"))
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(raw_details)
    first_quota = quota_violations[0] if quota_violations else {}
    return {
        "http_status": http_status,
        "http_code": http_status,
        "status_code": http_status,
        "provider_status": provider_status,
        "original_provider_message": str(original_message),
        "quota_metric": first_quota.get("quota_metric"),
        "quota_id": first_quota.get("quota_id"),
        "quota_dimensions": first_quota.get("quota_dimensions"),
        "quota_violations": quota_violations,
        "retry_delay": _json_safe(retry_delay),
        "raw_exception_type": f"{type(error).__module__}.{type(error).__name__}",
        "raw_exception_class": type(error).__name__,
        "provider_payload": raw_details,
    }


def provider_error(
    error: Exception,
    default_message: str = "Gemini text generation failed.",
) -> ModelProviderError:
    """Create a safe provider error without discarding SDK error details."""
    return ModelProviderError(
        classify_gemini_error(error, default_message),
        provider_details=extract_gemini_error_details(error),
    )


def classify_gemini_error(
    error: Exception,
    default_message: str = "Gemini text generation failed.",
) -> str:
    """Return a safe project-level message for a provider exception."""
    parts: list[str] = []
    current: BaseException | None = error
    while current is not None:
        parts.extend(
            [
                str(current),
                type(current).__name__,
                str(getattr(current, "code", "")),
                str(getattr(current, "status_code", "")),
                str(getattr(current, "status", "")),
                str(getattr(current, "message", "")),
            ]
        )
        current = current.__cause__ or current.__context__
    details = " ".join(parts).lower()

    if "timeout" in details or "timed out" in details:
        return "Gemini request timeout (600 seconds)."

    if (
        "503" in details
        or "unavailable" in details
        or "high demand" in details
    ):
        return (
            "Gemini temporarily unavailable: model under high demand "
            "(HTTP 503)."
        )

    if (
        "429" in details
        or "quota" in details
        or "rate limit" in details
        or "rate-limit" in details
        or "ratelimit" in details
    ):
        return "Gemini rate limit or quota reached (HTTP 429)."

    return default_message


def file_state_name(file_object: Any) -> str:
    """Return a normalized provider file state name."""
    state = getattr(file_object, "state", None)

    if state is None:
        return ""

    return str(getattr(state, "value", state)).upper()


class GeminiClient:
    """Small adapter around the google-genai Gemini client."""

    def __init__(self, *, model_name: str, api_key: str) -> None:
        self.model_name = model_name

        try:
            from google import genai
            from google.genai import types
        except Exception as error:
            raise ModelProviderError(
                "The google-genai package is required for Gemini requests."
            ) from error

        try:
            self._client: Any = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    timeout=GEMINI_REQUEST_TIMEOUT_MS,
                ),
            )
        except Exception as error:
            raise ModelProviderError(
                "Failed to create Gemini client."
            ) from error

    def generate_text(self, prompt: str) -> str:
        """Send a text prompt to Gemini and return response text."""
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
        except Exception as error:
            raise provider_error(error) from error

        text = getattr(response, "text", None)

        if text is None:
            raise ModelProviderError(
                "Gemini response did not contain plain text."
            )

        return str(text)

    def wait_for_file_processing(self, uploaded_file: Any) -> Any:
        """Poll provider file state until it can be used or fails."""
        file_name = getattr(uploaded_file, "name", None)

        if not file_name:
            raise ModelProviderError(
                "Gemini PDF upload did not return a usable file handle."
            )

        deadline = time.monotonic() + FILE_PROCESSING_TIMEOUT_SECONDS
        current_file = uploaded_file

        while file_state_name(current_file) in {
            "PROCESSING",
            "STATE_UNSPECIFIED",
        }:
            if time.monotonic() >= deadline:
                raise ModelProviderError(
                    "Gemini PDF processing timed out."
                )

            time.sleep(FILE_PROCESSING_POLL_SECONDS)

            try:
                current_file = self._client.files.get(name=file_name)
            except Exception as error:
                raise provider_error(
                    error,
                    "Gemini PDF processing status check failed.",
                ) from error

        if file_state_name(current_file) == "FAILED":
            raise ModelProviderError(
                "Gemini PDF processing failed."
            )

        return current_file

    def delete_uploaded_file(self, uploaded_file: Any) -> None:
        """Best-effort deletion of a temporary provider file."""
        file_name = getattr(uploaded_file, "name", None)

        if file_name:
            self._client.files.delete(name=file_name)

    def generate_document(
        self,
        *,
        prompt: str,
        file_path: Path,
    ) -> str:
        """Send a PDF and prompt to Gemini and return response text."""
        pdf_path = file_path.expanduser().resolve()

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF does not exist: {pdf_path}"
            )

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Not a PDF: {pdf_path}"
            )

        uploaded_file: Any | None = None

        try:
            uploaded_file = self._client.files.upload(
                file=pdf_path,
                config={
                    "mime_type": PDF_MIME_TYPE,
                    "display_name": pdf_path.name,
                },
            )
        except Exception as error:
            raise provider_error(error, "Gemini PDF upload failed.") from error

        try:
            processed_file = self.wait_for_file_processing(uploaded_file)

            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        processed_file,
                        prompt,
                    ],
                )
            except Exception as error:
                raise provider_error(error) from error

            text = getattr(response, "text", None)

            if text is None:
                raise ModelProviderError(
                    "Gemini response did not contain plain text."
                )

            return str(text)

        finally:
            if uploaded_file is not None:
                try:
                    self.delete_uploaded_file(uploaded_file)
                except Exception:
                    pass
