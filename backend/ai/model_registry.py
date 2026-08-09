"""Task-group model registry for local AI provider routing."""

from __future__ import annotations

from dataclasses import dataclass


class ModelGateError(RuntimeError):
    """Base exception for model-gate failures."""


class ModelConfigurationError(ModelGateError):
    """Raised when model-gate configuration is missing or invalid."""


@dataclass(frozen=True)
class ModelConfig:
    """Immutable model configuration for one task group."""

    provider: str
    model_name: str
    api_key_env_var: str


HIRING_CRITERIA_GEMINI_MODEL = "gemini-3.6-flash"
MATCHING_EVALUATION_GEMINI_MODEL = "gemini-3.6-flash"
TARGETED_CV_GENERATION_GEMINI_MODEL = "gemini-3.6-flash"

MODEL_REGISTRY: dict[str, ModelConfig] = {
    "hiring_criteria": ModelConfig(
        provider="gemini",
        model_name=HIRING_CRITERIA_GEMINI_MODEL,
        api_key_env_var="GEMINI_API_KEY",
    ),
    "matching_evaluation": ModelConfig(
        provider="gemini",
        model_name=MATCHING_EVALUATION_GEMINI_MODEL,
        api_key_env_var="GEMINI_API_KEY",
    ),
    "targeted_cv_generation": ModelConfig(
        provider="gemini",
        model_name=TARGETED_CV_GENERATION_GEMINI_MODEL,
        api_key_env_var="GEMINI_API_KEY",
    ),
}


def get_model_config(task_group: str) -> ModelConfig:
    """Return model configuration for a known task group."""
    try:
        return MODEL_REGISTRY[task_group]
    except KeyError as error:
        known_groups = ", ".join(sorted(MODEL_REGISTRY))
        raise ModelConfigurationError(
            f"Unknown AI task group: {task_group!r}. "
            f"Known task groups: {known_groups}"
        ) from error
