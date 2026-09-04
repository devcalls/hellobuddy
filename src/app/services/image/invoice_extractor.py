from __future__ import annotations

from app.integration.ai.factory import LLMServiceFactory
from app.integration.ai.llm import LLMService
from app.models.image.invoice import Invoice
from app.models.image.ocr_document import OCRDocument
from app.prompts.image.invoice_extraction import (
    INVOICE_EXTRACTION_SYSTEM_PROMPT,
)


class InvoiceExtractor:
    def __init__(
        self,
        settings,
        llm_service: LLMService | None = None,
    ) -> None:
        self.settings = settings
        self.llm_service = (
            llm_service
            or LLMServiceFactory.create(settings=settings.llm)
        )

    def extract(self, document: OCRDocument) -> Invoice:
        if not document.text.strip():
            raise ValueError("Cannot extract an invoice from empty OCR text.")

        prompt = self._build_user_prompt(document)

        return self.llm_service.generate_structured(
            system_prompt=INVOICE_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=Invoice,
        )

    @staticmethod
    def _build_user_prompt(document: OCRDocument) -> str:
        return f"""
Extract the invoice represented by the OCR document below.

OCR TEXT
========
{document.text}

OCR BLOCKS / LOCATION INFORMATION
=================================
{document.model_dump_json(indent=2)}

Return only data supported by the OCR document.
""".strip()
