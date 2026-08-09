"""Public local AI model-gate interface."""

from backend.ai.model_gate import (
    ModelConfigurationError,
    ModelGateError,
    ModelProviderError,
    generate_document,
    generate_text,
)
from backend.ai.ai_job_runner import (
    default_managed_folder_ai_job_path,
    reset_ai_job_state,
    run_ai_job,
)
from backend.ai.retry_policy import (
    RetryDecision,
    RetryPolicy,
    classify_ai_error,
    should_retry,
)

__all__ = [
    "RetryDecision",
    "RetryPolicy",
    "ModelConfigurationError",
    "ModelGateError",
    "ModelProviderError",
    "classify_ai_error",
    "default_managed_folder_ai_job_path",
    "generate_document",
    "generate_text",
    "reset_ai_job_state",
    "run_ai_job",
    "should_retry",
]
