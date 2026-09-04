from typing import ClassVar

from pydantic import BaseModel, Field, field_validator

from app.config.llm import LLMSettings
from app.config.settings import BaseFeatureSettings


class OCRSettings(BaseModel):
    provider: str = "easyocr"
    languages: list[str] = Field(default_factory=lambda: ["en"])
    gpu: bool = False

    @field_validator("languages", mode="before")
    @classmethod
    def parse_languages(cls, value):
        """Parse comma-separated language codes loaded from INI."""
        if isinstance(value, str):
            return [language.strip() for language in value.split(",") if language.strip()]
        return value


class ParserSettings(BaseModel):
    preserve_source_text: bool = True


class ImageSettings(BaseFeatureSettings):
    INI_FILE_PATH: ClassVar[str] = "image_config.ini"

    ocr: OCRSettings
    llm: LLMSettings
    parser: ParserSettings
