from __future__ import annotations

from typing import TypeVar


from pydantic import BaseModel

from app.integration.ai.llm import LLMService


T = TypeVar("T", bound=BaseModel)


class OpenAILLMService(LLMService):

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ) -> None:
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key
        )

        self.model = model

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:

        response = self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            text_format=response_model,
        )

        if response.output_parsed is None:
            raise RuntimeError(
                "OpenAI returned no structured response."
            )

        return response.output_parsed