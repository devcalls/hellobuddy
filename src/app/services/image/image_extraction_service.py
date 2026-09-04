from __future__ import annotations

from pathlib import Path

from app.config.image_settings import ImageSettings
from app.integration.ocr.factory import OCRProviderFactory
from app.models.image.invoice import Invoice
from app.models.image.ocr_document import OCRDocument
from app.services.image.invoice_extractor import InvoiceExtractor
from app.services.image.invoice_validation_service import (
    InvoiceValidationService,
)


class ImageExtractionService:
    """
    Orchestrates the image pipeline:

        image -> OCRDocument -> domain extraction -> validation
    """

    def __init__(
        self,
        settings: ImageSettings,
        ocr_provider=None,
        invoice_extractor=None,
        validation_service=None,
    ) -> None:
        self.settings = settings
        self.ocr_provider = (
            ocr_provider
            or OCRProviderFactory.create(settings.ocr)
        )
        self.invoice_extractor = (
            invoice_extractor
            or InvoiceExtractor(settings)
        )
        self.validation_service = (
            validation_service
            or InvoiceValidationService()
        )

    def read_ocr(self, file_path: str | Path) -> OCRDocument:
        return self.ocr_provider.read(file_path)

    def extract_invoice(self, file_path: str | Path) -> Invoice:
        document = self.read_ocr(file_path)
        invoice = self.invoice_extractor.extract(document)
        self.validation_service.validate(invoice)
        return invoice
