"""Environment-backed secret loading for the local AI model gate."""

from __future__ import annotations

import os

from backend.ai.model_registry import ModelConfigurationError


def load_project_dotenv() -> None:
    """Load project-root .env values without overriding the environment."""
    try:
        from dotenv import load_dotenv
    except Exception as error:
        raise ModelConfigurationError(
            "python-dotenv is required to load local .env secrets."
        ) from error

    load_dotenv(
        override=False,
    )


def load_required_secret(env_var_name: str) -> str:
    """Load a required secret from the process environment."""
    load_project_dotenv()

    value = os.environ.get(env_var_name)

    if value is None or not value.strip():
        raise ModelConfigurationError(
            f"Required environment variable is missing: {env_var_name}"
        )

    return value
