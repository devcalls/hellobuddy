from __future__ import annotations

import json
from typing import TypeVar

from google import genai
from pydantic import BaseModel

from app.integration.ai.llm import LLMService


T = TypeVar("T", bound=BaseModel)


class GeminiLLMService(LLMService):

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ) -> None:
        self.model = model

        self.client = genai.Client(
            api_key=api_key
        )

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:

        schema = response_model.model_json_schema()

        # Gemini does not accept every Pydantic JSON-schema keyword.
        schema = self._sanitize_schema(schema)

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config={
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
                "response_schema": schema,
            },
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        try:
            payload = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc

        return response_model.model_validate(payload)

    def _sanitize_schema(
        self,
        schema: dict,
    ) -> dict:

        """
        Remove JSON Schema constructs that Gemini does not support
        reliably.

        This sanitization belongs ONLY to the Gemini adapter.
        """

        if isinstance(schema, dict):

            schema.pop("additionalProperties", None)

            for key in list(schema.keys()):
                value = schema[key]

                if isinstance(value, dict):
                    self._sanitize_schema(value)

                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._sanitize_schema(item)

        return schema