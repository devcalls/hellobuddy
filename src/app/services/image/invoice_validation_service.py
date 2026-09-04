from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from app.models.image.invoice import ExtractionEvidence, Invoice
from app.models.image.ocr_document import OCRDocument, OCRTextBlock


class InvoiceValidationService:
    """Deterministic invoice checks and post-extraction quality annotations."""

    def __init__(self, low_ocr_confidence_threshold: float = 0.50) -> None:
        if not 0.0 <= low_ocr_confidence_threshold <= 1.0:
            raise ValueError("low_ocr_confidence_threshold must be between 0 and 1")
        self.low_ocr_confidence_threshold = low_ocr_confidence_threshold

    def validate(
        self,
        invoice: Invoice,
        ocr_document: OCRDocument | None = None,
    ) -> Invoice:
        """
        Annotate suspicious line items and reject only unreconciled errors.

        Low OCR confidence is a warning, not a fatal validation error. This is
        important because OCR can misread a single field while the invoice's
        other values still provide useful information.
        """
        if ocr_document is not None:
            self._enrich_line_item_ocr_confidence(invoice, ocr_document)

        errors = self.collect_errors(invoice)
        self._annotate_suspicious_line_items(invoice, errors)

        fatal_errors = [
            error for error in errors if not error.startswith("line item ")
        ]

        # A line-item arithmetic mismatch is non-fatal when that line has a
        # low-confidence field. The mismatch itself becomes part of the
        # suspicious-line-item message. If all involved fields are high
        # confidence, retain the old fail-fast behavior.
        for error in errors:
            if not error.startswith("line item "):
                continue
            index = self._line_item_index_from_error(error)
            if index is None:
                fatal_errors.append(error)
                continue

            item = invoice.line_items[index - 1]
            if not self._has_low_confidence_evidence(item):
                fatal_errors.append(error)

        if fatal_errors:
            raise ValueError(
                "Invoice validation failed:\n"
                + "\n".join(f"- {error}" for error in fatal_errors)
            )

        return invoice

    def collect_errors(self, invoice: Invoice) -> list[str]:
        errors: list[str] = []

        if invoice.total is not None and invoice.subtotal is not None:
            if invoice.tax is not None:
                # Discount is part of the invoice arithmetic. A discount may
                # already be negative (e.g. -83.50), so simply add it.
                expected = invoice.subtotal + invoice.tax
                if invoice.discount is not None:
                    expected += invoice.discount

                if not self._approximately_equal(expected, invoice.total):
                    errors.append(
                        "subtotal + tax + discount does not match total."
                    )

        for index, item in enumerate(invoice.line_items, start=1):
            if (
                item.quantity is not None
                and item.unit_price is not None
                and item.amount is not None
            ):
                expected = item.quantity * item.unit_price
                if not self._approximately_equal(expected, item.amount):
                    errors.append(
                        f"line item {index}: quantity × unit_price "
                        "does not match amount."
                    )

        return errors

    def _annotate_suspicious_line_items(
        self,
        invoice: Invoice,
        errors: list[str],
    ) -> None:
        mismatch_indexes = {
            self._line_item_index_from_error(error)
            for error in errors
            if error.startswith("line item ")
        }

        for index, item in enumerate(invoice.line_items, start=1):
            reasons: list[str] = []

            # Report every low-confidence field, not just the first one.
            for field_name in ("description", "quantity", "unit_price", "amount"):
                confidence = self._field_ocr_confidence(item, field_name)
                if confidence is not None and confidence < self.low_ocr_confidence_threshold:
                    reasons.append(
                        f"{field_name} has low OCR confidence "
                        f"({confidence:.2f}; threshold {self.low_ocr_confidence_threshold:.2f})"
                    )

            if index in mismatch_indexes:
                reasons.append(
                    "quantity × unit_price does not match amount"
                )

            item.suspicion_reasons = self._deduplicate(reasons)

            has_low_confidence = any(
                evidence.ocr_confidence is not None
                and evidence.ocr_confidence < self.low_ocr_confidence_threshold
                for evidence in item.evidence
            )
            has_mismatch = index in mismatch_indexes

            # Categories are intended to tell the operator what needs
            # attention, not merely whether OCR confidence is low.
            #
            # REVIEW: one or more OCR fields are low confidence, but the
            # extracted line item still reconciles mathematically.
            # URGENT: the line has both a low-confidence field and an
            # arithmetic inconsistency, making the extracted value suspect.
            if has_mismatch and has_low_confidence:
                item.category = "URGENT"
            elif has_low_confidence:
                item.category = "REVIEW"
            else:
                item.category = "OK"

            item.suspicious = item.category == "URGENT"

    def _enrich_line_item_ocr_confidence(
        self,
        invoice: Invoice,
        ocr_document: OCRDocument,
    ) -> None:
        """
        Fill missing OCR confidence in line-item evidence from OCR blocks.

        The LLM remains responsible for semantic extraction. This step only
        attaches provenance from the OCR observations to the already extracted
        fields so validation can explain why a value is suspicious.
        """
        for item in invoice.line_items:
            for field_name in ("description", "quantity", "unit_price", "amount"):
                value = getattr(item, field_name)
                if value is None:
                    continue

                existing = self._field_evidence(item, field_name)
                if existing and any(
                    evidence.ocr_confidence is not None for evidence in existing
                ):
                    continue

                block = self._find_matching_block(value, ocr_document.blocks)
                if block is None:
                    continue

                if existing:
                    evidence = existing[0]
                    evidence.field = field_name
                    evidence.ocr_confidence = block.confidence
                    evidence.bounding_box = block.bounding_box
                else:
                    item.evidence.append(
                        ExtractionEvidence(
                            field=field_name,
                            source_text=block.text,
                            bounding_box=block.bounding_box,
                            ocr_confidence=block.confidence,
                            extraction_confidence=block.confidence,
                            reason="Matched extracted field to OCR block for validation.",
                        )
                    )

    @staticmethod
    def _field_evidence(item, field_name: str) -> list[ExtractionEvidence]:
        return [
            evidence
            for evidence in item.evidence
            if evidence.field == field_name
        ]

    def _field_ocr_confidence(
        self,
        item,
        field_name: str,
    ) -> float | None:
        confidences = [
            evidence.ocr_confidence
            for evidence in self._field_evidence(item, field_name)
            if evidence.ocr_confidence is not None
        ]
        if not confidences:
            return None
        return min(confidences)

    def _has_low_confidence_evidence(self, item) -> bool:
        return any(
            evidence.ocr_confidence is not None
            and evidence.ocr_confidence < self.low_ocr_confidence_threshold
            for evidence in item.evidence
        )

    @staticmethod
    def _find_matching_block(
        value,
        blocks: list[OCRTextBlock],
    ) -> OCRTextBlock | None:
        """Find an OCR block corresponding to an extracted scalar value."""
        value_text = str(value).strip()
        normalized_value = InvoiceValidationService._normalize_text(value_text)

        # Prefer exact normalized text matches.
        for block in blocks:
            if InvoiceValidationService._normalize_text(block.text) == normalized_value:
                return block

        # Decimal values often differ only in OCR punctuation, e.g. 40.,00.
        decimal_value = InvoiceValidationService._to_decimal(value_text)
        if decimal_value is not None:
            for block in blocks:
                block_decimal = InvoiceValidationService._to_decimal(block.text)
                if block_decimal is not None and block_decimal == decimal_value:
                    return block

        return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.casefold().split())

    @staticmethod
    def _to_decimal(value: str) -> Decimal | None:
        cleaned = value.strip().replace(",", ".")
        # Handle OCR values such as "X3.0" / "x17,0".
        cleaned = re.sub(r"^[x×]\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace(" ", "")
        cleaned = re.sub(r"(?<=\d)\.(?=\.)", "", cleaned)
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    @staticmethod
    def _line_item_index_from_error(error: str) -> int | None:
        match = re.match(r"line item (\d+):", error)
        return int(match.group(1)) if match else None

    @staticmethod
    def _deduplicate(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))

    @staticmethod
    def _approximately_equal(left: Decimal, right: Decimal) -> bool:
        tolerance = Decimal("0.01")
        return abs(left - right) <= tolerance
