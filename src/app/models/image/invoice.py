"""
Invoice domain model.

This is intentionally invoice-specific. It is not a generic document AST.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.image.ocr_document import BoundingBox


class ExtractionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Field within the semantic model that this evidence supports.
    # Examples: quantity, unit_price, amount, invoice_number, total.
    field: str | None = None
    source_text: str
    bounding_box: BoundingBox | None = None
    ocr_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    extraction_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )
    reason: str | None = None


class InvoiceLineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    amount: Decimal | None = None
    evidence: list[ExtractionEvidence] = Field(default_factory=list)

    # These are deterministic post-extraction annotations. The LLM does not
    # decide whether a line item is suspicious.
    suspicious: bool = False
    suspicion_reasons: list[str] = Field(default_factory=list)
    # Action-oriented post-extraction category:
    # OK = no issues, REVIEW = low-confidence field(s) but arithmetic reconciles,
    # URGENT = a validation inconsistency exists alongside low-confidence evidence.
    category: Literal["OK", "REVIEW", "URGENT"] = "OK"


class Invoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None

    vendor_name: str | None = None
    vendor_address: str | None = None
    vendor_tax_id: str | None = None

    customer_name: str | None = None
    customer_address: str | None = None
    customer_tax_id: str | None = None

    currency: str | None = None

    line_items: list[InvoiceLineItem] = Field(default_factory=list)

    subtotal: Decimal | None = None
    tax: Decimal | None = None
    # Positive or negative according to the extracted invoice representation.
    # The validator adds this value to subtotal + tax.
    discount: Decimal | None = None
    total: Decimal | None = None

    evidence: dict[str, list[ExtractionEvidence]] = Field(
        default_factory=dict,
        description=(
            "Field-level provenance. Keys are Invoice field names, "
            "for example invoice_number or total."
        ),
    )
