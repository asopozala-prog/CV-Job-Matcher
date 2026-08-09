"""Minimal task-group AI model gate."""

from __future__ import annotations

from pathlib import Path

from backend.ai.gemini_client import GeminiClient, ModelProviderError
from backend.ai.model_registry import (
    ModelConfigurationError,
    ModelGateError,
    get_model_config,
)
from backend.ai.secrets import load_required_secret


def generate_text(
    task_group: str,
    prompt: str,
) -> str:
    """Generate text for a configured task group."""
    config = get_model_config(task_group)
    api_key = load_required_secret(config.api_key_env_var)

    if config.provider == "gemini":
        client = GeminiClient(
            model_name=config.model_name,
            api_key=api_key,
        )
        return client.generate_text(prompt)

    raise ModelConfigurationError(
        f"Unsupported AI provider for task group {task_group!r}: "
        f"{config.provider!r}"
    )


def generate_document(
    task_group: str,
    prompt: str,
    file_path: Path,
) -> str:
    """Generate text from a configured task group using a PDF document."""
    config = get_model_config(task_group)
    api_key = load_required_secret(config.api_key_env_var)

    if config.provider == "gemini":
        client = GeminiClient(
            model_name=config.model_name,
            api_key=api_key,
        )
        return client.generate_document(
            prompt=prompt,
            file_path=file_path,
        )

    raise ModelConfigurationError(
        f"Unsupported AI provider for task group {task_group!r}: "
        f"{config.provider!r}"
    )
