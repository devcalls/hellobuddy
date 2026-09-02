
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """
    Supported LLM providers.
    """

    GEMINI = "gemini"
    OPENAI = "openai"


class LLMSettings(BaseModel):
    """
    Generic LLM configuration.

    Provider determines which implementation is used.
    Model identifies the model to invoke.
    """

    provider: LLMProvider = Field(
        default=LLMProvider.GEMINI
    )

    model: str = Field(
        default="gemini-2.5-flash"
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
    )

    max_output_tokens: int = Field(
        default=8192,
        gt=0,
    )


class LLMClientFactory:
    """
    Creates an LLM client based on provider configuration.

    Application services should use this factory instead of
    directly importing provider-specific SDKs.
    """

    @staticmethod
    def create(
        settings: LLMSettings,
        api_key: str,
    ) -> Any:

        if not api_key:
            raise ValueError(
                f"API key is required for provider "
                f"'{settings.provider.value}'."
            )

        if settings.provider == LLMProvider.GEMINI:

            return LLMClientFactory._create_gemini_client(
                api_key
            )

        if settings.provider == LLMProvider.OPENAI:

            return LLMClientFactory._create_openai_client(
                api_key
            )

        raise ValueError(
            f"Unsupported LLM provider: "
            f"{settings.provider}"
        )

    @staticmethod
    def _create_gemini_client(
        api_key: str,
    ):

        from google import genai

        return genai.Client(
            api_key=api_key
        )

    @staticmethod
    def _create_openai_client(
        api_key: str,
    ):

        from openai import OpenAI

        return OpenAI(
            api_key=api_key
        )

