from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from app.models.image.invoice import Invoice


class OutputError(RuntimeError):
    """Raised when an output integration cannot write the extracted data."""


class Output(ABC):
    """Provider-neutral output interface for extracted invoice data."""

    @abstractmethod
    def write(self, invoices: Sequence[Invoice], **kwargs: Any) -> None:
        raise NotImplementedError
