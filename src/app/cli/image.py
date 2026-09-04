from __future__ import annotations

from pathlib import Path

from app.config.image_settings import ImageSettings
from app.services.image.image_extraction_service import ImageExtractionService
from app.services.image.image_output_service import ImageOutputService
from app.integration.ocr.factory import OCRProviderFactory


def _get_image_settings() -> ImageSettings:
    """Load image settings only when an image command is executed."""
    return ImageSettings()


def extract_image(
    input_path: str,
    output_format: str | None = None,
    output_path: str | None = None,
    document_type: str = "invoice",
    spreadsheet: str | None = None,
    worksheet: str = "Invoices",
    credentials_file: str | None = None,
) -> int:
    """Extract one or many invoices and write a consolidated output."""
    try:
        settings = _get_image_settings()
        path = Path(input_path)

        if document_type != "invoice":
            print(
                f"✗ Unsupported document type: {document_type}. "
                "Currently supported: invoice"
            )
            return 1

        output_format = output_format or settings.output.default_format
        worksheet = worksheet or settings.output.default_worksheet

        extraction_service = ImageExtractionService(settings)
        paths = extraction_service._resolve_input_paths(path)

        print(f"Found {len(paths)} image(s) to process")

        invoices = []
        failures = []

        for index, image_path in enumerate(paths, start=1):
            print(f"[{index}/{len(paths)}] Analyzing: {image_path}")
            try:
                invoice = extraction_service.extract_invoice(image_path)
                invoices.append(invoice)

                suspicious_items = [
                    (item_index, item)
                    for item_index, item in enumerate(invoice.line_items, start=1)
                    if item.suspicious
                ]

                print("  ✓ Invoice extracted and validated")
                attention_items = [
                    (item_index, item)
                    for item_index, item in enumerate(invoice.line_items, start=1)
                    if item.category != "OK"
                ]

                if attention_items:
                    for item_index, item in attention_items:
                        icon = "🚨" if item.category == "URGENT" else "⚠"
                        print(
                            f"  {icon} Line item {item_index} [{item.category}]: "
                            + "; ".join(item.suspicion_reasons)
                        )
            except Exception as exc:
                failures.append((image_path, exc))
                print(f"  ✗ Failed: {exc}")

        if not invoices:
            print("✗ No invoices were successfully extracted.")
            return 1

        if output_format == "csv" and output_path is None:
            output_path = "invoices.csv"

        if output_format == "json" and output_path is None and len(invoices) == 1:
            # Keep the existing single-invoice behavior: JSON to stdout.
            pass

        if output_format in {"google-sheets", "google_sheets", "sheets"}:
            if not spreadsheet:
                print(
                    "✗ Google Sheets output requires --spreadsheet "
                    "with a spreadsheet ID or name."
                )
                return 1

        ImageOutputService().write(
            invoices,
            output_format=output_format,
            output_path=output_path,
            spreadsheet=spreadsheet,
            worksheet=worksheet,
            credentials_file=credentials_file,
        )

        if output_path:
            print(f"✓ Output written to {output_path}")
        elif output_format in {"google-sheets", "google_sheets", "sheets"}:
            print(f"✓ Output written to Google Sheet: {spreadsheet}/{worksheet}")

        print(
            f"✓ Completed: {len(invoices)} invoice(s) extracted successfully"
        )

        if failures:
            print(f"⚠ {len(failures)} image(s) failed:")
            for failed_path, error in failures:
                print(f"  - {failed_path}: {error}")

        return 0

    except Exception as exc:
        print(f"✗ Image extraction failed: {exc}")
        return 1


def extract_ocr(
    file_path: str,
    output: str | None = None,
) -> int:
    """Extract raw OCRDocument JSON without semantic extraction."""
    try:
        settings = _get_image_settings()
        path = Path(file_path)

        if not path.exists():
            print(f"✗ Image file not found: {path}")
            return 1

        provider = OCRProviderFactory.create(settings.ocr)
        document = provider.read(path)

        serialized = document.model_dump_json(indent=2)
        if output is None:
            print(serialized)
        else:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(serialized, encoding="utf-8")
            print(f"✓ Output written to {output_path}")

        print("✓ OCR extraction completed")
        return 0

    except Exception as exc:
        print(f"✗ OCR extraction failed: {exc}")
        return 1
