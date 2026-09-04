from __future__ import annotations

import json
from pathlib import Path

from app.config.image_settings import ImageSettings
from app.integration.ai.factory import LLMServiceFactory
from app.integration.ai.llm import LLMService
from app.integration.ocr.factory import OCRProviderFactory
from app.services.image.invoice_extractor import InvoiceExtractor
from app.services.image.invoice_validation_service import (
    InvoiceValidationService,
)


def _get_image_settings() -> ImageSettings:
    """Load image settings only when an image command is executed."""
    return ImageSettings()


def _build_llm_service(settings: ImageSettings) -> LLMService:
    return LLMServiceFactory.create(settings=settings.llm)


def _write_json(data, output: str | None) -> None:
    serialized = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    if output is None:
        print(serialized)
        return

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialized, encoding="utf-8")
    print(f"✓ Output written to {output_path}")


def extract_image(
    file_path: str,
    output: str | None = None,
    document_type: str = "invoice",
) -> int:
    """
    Extract structured data from an image.

    Example:
        hellobuddy image extract invoice.jpg --type invoice -o invoice.json
    """
    try:
        image_settings = _get_image_settings()
        path = Path(file_path)

        if not path.exists():
            print(f"✗ Image file not found: {path}")
            return 1

        if not path.is_file():
            print(f"✗ Image path is not a file: {path}")
            return 1

        if document_type != "invoice":
            print(
                f"✗ Unsupported document type: {document_type}. "
                "Currently supported: invoice"
            )
            return 1

        print(f"Analyzing image: {path}")

        ocr_provider = OCRProviderFactory.create(image_settings.ocr)
        ocr_document = ocr_provider.read(path)

        print(
            f"✓ OCR completed: {len(ocr_document.blocks)} text blocks"
        )

        extractor = InvoiceExtractor(
            settings=image_settings,
            llm_service=_build_llm_service(image_settings),
        )

        invoice = extractor.extract(ocr_document)

        InvoiceValidationService().validate(invoice)

        _write_json(
            invoice.model_dump(mode="json"),
            output,
        )

        print("✓ Invoice extraction completed")
        return 0

    except ValueError as exc:
        print(f"✗ Image extraction failed: {exc}")
        return 1

    except Exception as exc:
        print(f"✗ Image extraction failed: {exc}")
        return 1


def extract_ocr(
    file_path: str,
    output: str | None = None,
) -> int:
    """Extract raw OCRDocument JSON without semantic extraction."""
    try:
        image_settings = _get_image_settings()
        path = Path(file_path)

        if not path.exists():
            print(f"✗ Image file not found: {path}")
            return 1

        provider = OCRProviderFactory.create(image_settings.ocr)
        document = provider.read(path)

        _write_json(
            document.model_dump(mode="json"),
            output,
        )

        print("✓ OCR extraction completed")
        return 0

    except Exception as exc:
        print(f"✗ OCR extraction failed: {exc}")
        return 1
