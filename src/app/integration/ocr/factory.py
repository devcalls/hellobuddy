from __future__ import annotations

from app.config.image_settings import OCRSettings
from app.integration.ocr.easyocr_provider import EasyOCROCRProvider


class OCRProviderFactory:
    @staticmethod
    def create(settings: OCRSettings):
        provider = settings.provider.lower()

        if provider == "easyocr":
            return EasyOCROCRProvider(settings)

        raise ValueError(f"Unsupported OCR provider: {provider}")
