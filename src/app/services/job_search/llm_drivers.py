import os
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic
from pydantic import BaseModel

# Create a Generic Type Variable constrained to Pydantic BaseModels
T = TypeVar("T", bound=BaseModel)

class BaseLLMDriver(ABC):
    """Abstract interface that all provider drivers must implement using Generics."""
    
    @abstractmethod
    def generate_structured_output(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        response_schema: Type[T]
    ) -> T:
        """
        Executes a structured call to the LLM provider.
        :param system_prompt: Defines the behavior/identity of the model.
        :param user_prompt: The dynamic data context or instructions.
        :param response_schema: The Pydantic class definition to force the layout.
        :return: An initialized instance of the passed response_schema Pydantic model.
        """
        pass


# ==========================================
# 1. Groq Driver Implementation
# ==========================================
class GroqDriver(BaseLLMDriver):
    """Driver for Groq using dynamic JSON Schema enforcement."""
    def __init__(self, model_name: str):
        from groq import Groq
        self.client = Groq()
        self.model_name = model_name

    def generate_structured_output(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        response_schema: Type[T]
    ) -> T:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": f"{response_schema.__name__}Schema",
                    "strict": True,
                    "schema": response_schema.model_json_schema()
                }
            },
            temperature=0.8
        )
        return response_schema.model_validate_json(response.choices[0].message.content)


# ==========================================
# 2. Gemini Driver Implementation
# ==========================================
class GeminiDriver(BaseLLMDriver):
    """Driver for Google Gemini using the modern 2026 unified GenAI SDK."""
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        from google import genai
        self.client = genai.Client()
        self.model_name = model_name

    def generate_structured_output(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        response_schema: Type[T]
    ) -> T:
        from google.genai import types
        
        # Combine instructions cleanly or use system_instruction parameter if supported
        full_content = f"Instructions: {system_prompt}\n\nContext Data:\n{user_prompt}"
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_content,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1
            )
        )
        return response_schema.model_validate_json(response.text)