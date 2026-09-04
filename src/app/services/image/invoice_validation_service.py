from __future__ import annotations

from decimal import Decimal

from app.models.image.invoice import Invoice


class InvoiceValidationService:
    """Deterministic invoice checks. LLM extraction is not validation."""

    def validate(self, invoice: Invoice) -> Invoice:
        errors = self.collect_errors(invoice)

        if errors:
            raise ValueError(
                "Invoice validation failed:\n"
                + "\n".join(f"- {error}" for error in errors)
            )

        return invoice

    def collect_errors(self, invoice: Invoice) -> list[str]:
        errors: list[str] = []

        if invoice.total is not None and invoice.subtotal is not None:
            if invoice.tax is not None:
                expected = invoice.subtotal + invoice.tax
                if not self._approximately_equal(expected, invoice.total):
                    errors.append(
                        "subtotal + tax does not match total."
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

    @staticmethod
    def _approximately_equal(left: Decimal, right: Decimal) -> bool:
        tolerance = Decimal("0.01")
        return abs(left - right) <= tolerance
