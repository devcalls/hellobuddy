from __future__ import annotations

from app.config.llm import LLMSettings
from app.integration.ai.llm import LLMService
from app.integration.ai.providers.gemini import (
    GeminiLLMService,
)
from app.integration.ai.providers.openai import (
    OpenAILLMService,
)
import os

class LLMServiceFactory:

    @staticmethod
    def create(
        settings: LLMSettings,
    ) -> LLMService:

        provider = settings.provider.lower()

        if provider == "gemini":
            api_key = os.environ["GOOGLE_API_KEY"]
            if not api_key:
                raise RuntimeError(
                    "LLM API key is required for Gemini."
                )

            return GeminiLLMService(
                api_key=api_key,
                model=settings.model,
            )

        if provider == "openai":
            api_key = os.environ["OPENAI_API_KEY"]
            if not api_key:
                raise RuntimeError(
                    "LLM API key is required for OpenAI."
                )

            return OpenAILLMService(
                api_key=api_key,
                model=settings.model,
            )

        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )