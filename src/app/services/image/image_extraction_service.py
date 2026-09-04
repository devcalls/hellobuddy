from __future__ import annotations

from pathlib import Path

from app.config.image_settings import ImageSettings
from app.integration.ocr.factory import OCRProviderFactory
from app.models.image.invoice import Invoice
from app.models.image.ocr_document import OCRDocument
from app.services.image.invoice_extractor import InvoiceExtractor
from app.services.image.invoice_validation_service import InvoiceValidationService


SUPPORTED_IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}


class ImageExtractionService:
    """Orchestrates OCR, invoice extraction and deterministic validation."""

    def __init__(
        self,
        settings: ImageSettings,
        ocr_provider=None,
        invoice_extractor=None,
        validation_service=None,
    ) -> None:
        self.settings = settings
        self.ocr_provider = ocr_provider or OCRProviderFactory.create(settings.ocr)
        self.invoice_extractor = invoice_extractor or InvoiceExtractor(settings)
        self.validation_service = validation_service or InvoiceValidationService(
            low_ocr_confidence_threshold=settings.parser.low_ocr_confidence_threshold
        )

    def read_ocr(self, file_path: str | Path) -> OCRDocument:
        return self.ocr_provider.read(file_path)

    def extract_invoice(self, file_path: str | Path) -> Invoice:
        document = self.read_ocr(file_path)
        invoice = self.invoice_extractor.extract(document)
        return self.validation_service.validate(invoice, ocr_document=document)

    def extract_invoices(self, input_path: str | Path) -> list[Invoice]:
        """Extract all supported images from a file or directory."""
        paths = self._resolve_input_paths(input_path)
        invoices: list[Invoice] = []

        for path in paths:
            invoices.append(self.extract_invoice(path))

        return invoices

    @staticmethod
    def _resolve_input_paths(input_path: str | Path) -> list[Path]:
        path = Path(input_path)

        if not path.exists():
            raise FileNotFoundError(f"Image path not found: {path}")

        if path.is_file():
            if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
                raise ValueError(
                    f"Unsupported image format: {path.suffix or '<none>'}"
                )
            return [path]

        if path.is_dir():
            paths = sorted(
                item
                for item in path.iterdir()
                if item.is_file()
                and item.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
            )
            if not paths:
                raise ValueError(
                    f"No supported image files found in directory: {path}"
                )
            return paths

        raise ValueError(f"Unsupported input path: {path}")
