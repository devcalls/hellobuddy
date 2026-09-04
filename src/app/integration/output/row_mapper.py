from __future__ import annotations

from typing import Any, Sequence

from app.models.image.invoice import Invoice


INVOICE_HEADERS = [
    "invoice_number",
    "vendor_name",
    "invoice_date",
    "due_date",
    "vendor_address",
    "vendor_tax_id",
    "customer_name",
    "customer_address",
    "customer_tax_id",
    "currency",
    "item_description",
    "quantity",
    "unit_price",
    "amount",
    "subtotal",
    "tax",
    "total",
    "category",
    "line_item_suspicious",
    "line_item_suspicion_reasons",
]


def invoice_rows(invoices: Sequence[Invoice]) -> list[list[Any]]:
    """Flatten invoices into line-item-oriented rows for tabular outputs."""
    rows: list[list[Any]] = []

    for invoice in invoices:
        items = invoice.line_items or [None]

        for item in items:
            rows.append(
                [
                    invoice.invoice_number,
                    invoice.vendor_name,
                    invoice.invoice_date,
                    invoice.due_date,
                    invoice.vendor_address,
                    invoice.vendor_tax_id,
                    invoice.customer_name,
                    invoice.customer_address,
                    invoice.customer_tax_id,
                    invoice.currency,
                    item.description if item else None,
                    item.quantity if item else None,
                    item.unit_price if item else None,
                    item.amount if item else None,
                    invoice.subtotal,
                    invoice.tax,
                    invoice.total,
                    item.category if item else "OK",
                    item.suspicious if item else False,
                    "; ".join(item.suspicion_reasons) if item else None,
                ]
            )

    return rows
