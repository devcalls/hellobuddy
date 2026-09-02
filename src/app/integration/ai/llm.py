"""
Provider-neutral LLM service.

Application code should depend on this interface rather
than Gemini/OpenAI SDKs.
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Any

from pydantic import BaseModel

from app.config.llm import (
    LLMProvider,
    LLMSettings,
)
import os

T = TypeVar(
    "T",
    bound=BaseModel,
)


class LLMService(ABC):
    """
    Provider-neutral LLM interface.
    """

    @abstractmethod
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:

        raise NotImplementedError


class GeminiLLMService(LLMService):
    """
    Gemini implementation.

    Important:
    We do NOT pass the Pydantic model directly to Gemini.

    Pydantic v2 generates schemas containing $defs/$ref.
    We resolve those references first because the Gemini
    response_schema transformer can otherwise fail on
    nested models.
    """

    def __init__(
        self,
        client,
        settings: LLMSettings,
    ) -> None:

        self.client = client
        self.settings = settings

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:

        from google.genai import types

        # ---------------------------------------------
        # 1. Generate Pydantic JSON schema
        # ---------------------------------------------

        schema = response_model.model_json_schema()

        # ---------------------------------------------
        # 2. Resolve all $defs / $ref references
        # ---------------------------------------------

        schema = self._dereference_schema(
            schema
        )

        # ---------------------------------------------
        # 3. Remove JSON-schema constructs that are
        #    not needed by Gemini's response_schema.
        # ---------------------------------------------

        schema = self._clean_schema(
            schema
        )

        # ---------------------------------------------
        # 4. Call Gemini
        # ---------------------------------------------

        response = self.client.models.generate_content(
            model=self.settings.model,

            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"{system_prompt}\n\n"
                                f"{user_prompt}"
                            )
                        }
                    ],
                }
            ],

            config=types.GenerateContentConfig(

                temperature=(
                    self.settings.temperature
                ),

                max_output_tokens=(
                    self.settings.max_output_tokens
                ),

                response_mime_type=(
                    "application/json"
                ),

                response_schema=schema,
            ),
        )

        # ---------------------------------------------
        # 5. Validate Gemini's response using the
        #    original Pydantic model.
        # ---------------------------------------------

        if not response.text:

            raise ValueError(
                "Gemini returned an empty response."
            )

        return response_model.model_validate_json(
            response.text
        )

    @classmethod
    def _dereference_schema(
        cls,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Fully expand Pydantic $defs/$ref references.

        Example:

            {
                "$ref": "#/$defs/ExtractedExperience"
            }

        becomes:

            {
                "type": "object",
                "properties": {...}
            }

        This removes Gemini's dependency on resolving
        Pydantic's nested references.
        """

        defs = schema.get(
            "$defs",
            {}
        )

        def resolve(
            node: Any,
        ) -> Any:

            # -----------------------------------------
            # Dictionary
            # -----------------------------------------

            if isinstance(node, dict):

                ref = node.get("$ref")

                if ref:

                    ref_name = (
                        ref.split("/")[-1]
                    )

                    if ref_name not in defs:

                        raise ValueError(
                            "Unable to resolve JSON schema "
                            f"reference '{ref_name}'. "
                            f"Available definitions: "
                            f"{list(defs.keys())}"
                        )

                    # Resolve the referenced model
                    resolved = resolve(
                        defs[ref_name]
                    )

                    # Preserve description if the
                    # reference had one.
                    extra = {
                        key: value
                        for key, value
                        in node.items()
                        if key != "$ref"
                    }

                    if extra:

                        if isinstance(
                            resolved,
                            dict,
                        ):

                            resolved = {
                                **resolved,
                                **extra,
                            }

                    return resolved

                return {
                    key: resolve(value)
                    for key, value in node.items()
                    if key != "$defs"
                }

            # -----------------------------------------
            # Lists
            # -----------------------------------------

            if isinstance(node, list):

                return [
                    resolve(item)
                    for item in node
                ]

            return node

        return resolve(schema)

    @classmethod
    def _clean_schema(
        cls,
        schema: Any,
    ) -> Any:
        """
        Clean the dereferenced schema for Gemini.

        ResumeExtraction deliberately uses a small subset
        of JSON Schema, so this mainly removes metadata
        generated by Pydantic.
        """

        if isinstance(schema, list):

            return [
                cls._clean_schema(item)
                for item in schema
            ]

        if not isinstance(schema, dict):

            return schema

        cleaned = {}

        for key, value in schema.items():

            # Pydantic/internal JSON schema fields
            if key in {
                "$defs",
                "$schema",
                "$ref",
            }:
                continue

            # Gemini does not need these generated
            # schema annotations.
            if key == "title":

                continue

            cleaned[key] = (
                cls._clean_schema(value)
            )

        return cleaned


class OpenAILLMService(LLMService):
    """
    OpenAI implementation.
    """

    def __init__(
        self,
        client,
        settings: LLMSettings,
    ) -> None:

        self.client = client
        self.settings = settings

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:

        response = self.client.responses.parse(
            model=self.settings.model,

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

        result = response.output_parsed

        if result is None:

            raise ValueError(
                "OpenAI returned no structured output."
            )

        return result


class LLMServiceFactory:
    """
    Creates the provider-specific LLM service.
    """

    @staticmethod
    def create(
        settings: LLMSettings,
    ) -> LLMService:

        if settings.provider == LLMProvider.GEMINI:

            from google import genai
            
            if "GOOGLE_API_KEY" not in os.environ:
                raise ValueError(
                                f"API key is required for "
                                f"{settings.provider.value}."
                            )
            else:
                api_key = os.environ["GOOGLE_API_KEY"]

            client = genai.Client(
                api_key=api_key
            )

            return GeminiLLMService(
                client=client,
                settings=settings,
            )

        if settings.provider == LLMProvider.OPENAI:

            from openai import OpenAI
            
            if "OPENAI_API_KEY" not in os.environ:
                raise ValueError(
                                f"API key is required for "
                                f"{settings.provider.value}."
                            )
            else:
                api_key = os.environ["GEMINI_API_KEY"]

            client = OpenAI(
                api_key=api_key
            )

            return OpenAILLMService(
                client=client,
                settings=settings,
            )

        raise ValueError(
            f"Unsupported LLM provider: "
            f"{settings.provider}"
        )
