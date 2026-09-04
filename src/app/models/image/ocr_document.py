"""
Canonical OCR document representation.

This model represents what the OCR engine observed. It does not assign
business meaning to the extracted text.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(ge=0)
    height: float = Field(ge=0)


class OCRTextBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: BoundingBox
    page: int = Field(default=1, ge=1)


class OCRDocument(BaseModel):
    """
    OCR output consumed by semantic extractors.

    `text` is the normalized full OCR text. `blocks` preserve the
    location and OCR confidence for provenance.
    """

    model_config = ConfigDict(extra="forbid")

    text: str
    blocks: list[OCRTextBlock] = Field(default_factory=list)
    source_file: str | None = None
    source_format: str | None = None
    page_count: int = Field(default=1, ge=1)
    ocr_provider: str = "easyocr"
