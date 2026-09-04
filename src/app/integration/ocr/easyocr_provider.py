from __future__ import annotations

from pathlib import Path

from app.config.image_settings import OCRSettings
from app.models.image.ocr_document import (
    BoundingBox,
    OCRDocument,
    OCRTextBlock,
)


class OCRProviderError(RuntimeError):
    pass


class EasyOCROCRProvider:
    """EasyOCR adapter. Provider-specific details stay in integration."""

    name = "easyocr"

    def __init__(self, settings: OCRSettings) -> None:
        self.settings = settings
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            try:
                import easyocr
            except ImportError as exc:
                raise OCRProviderError(
                    "EasyOCR is required. Install with: pip install easyocr"
                ) from exc

            self._reader = easyocr.Reader(
                self.settings.languages,
                gpu=self.settings.gpu,
            )

        return self._reader

    def read(self, file_path: str | Path) -> OCRDocument:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        if not path.is_file():
            raise ValueError(f"Image path is not a file: {path}")

        try:
            results = self._get_reader().readtext(
                str(path),
                detail=1,
            )
        except Exception as exc:
            raise OCRProviderError(
                f"EasyOCR failed to process image: {path}"
            ) from exc

        blocks: list[OCRTextBlock] = []

        for polygon, text, confidence in results:
            if not text or not text.strip():
                continue

            x_values = [float(point[0]) for point in polygon]
            y_values = [float(point[1]) for point in polygon]

            blocks.append(
                OCRTextBlock(
                    text=text.strip(),
                    confidence=float(confidence),
                    bounding_box=BoundingBox(
                        x=min(x_values),
                        y=min(y_values),
                        width=max(x_values) - min(x_values),
                        height=max(y_values) - min(y_values),
                    ),
                )
            )

        return OCRDocument(
            text="\n".join(block.text for block in blocks),
            blocks=blocks,
            source_file=str(path),
            source_format=path.suffix.lower(),
            page_count=1,
            ocr_provider=self.name,
        )
