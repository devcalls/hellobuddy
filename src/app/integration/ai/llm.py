from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class LLMService(ABC):
    """
    Provider-neutral LLM interface.

    Nothing outside the provider adapters should know whether
    the underlying model is Gemini, OpenAI, Anthropic, etc.
    """

    @abstractmethod
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        """
        Generate a structured response validated against response_model.
        """
        raise NotImplementedError