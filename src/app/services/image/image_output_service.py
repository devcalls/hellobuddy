from __future__ import annotations

from collections.abc import Sequence

from app.integration.output.factory import OutputFactory
from app.models.image.invoice import Invoice


class ImageOutputService:
    """Writes extracted invoices using the selected output integration."""

    def write(
        self,
        invoices: Sequence[Invoice],
        *,
        output_format: str,
        output_path: str | None = None,
        spreadsheet: str | None = None,
        worksheet: str = "Invoices",
        credentials_file: str | None = None,
    ) -> None:
        output = OutputFactory.create(output_format)
        output.write(
            invoices,
            output_path=output_path,
            spreadsheet=spreadsheet,
            worksheet=worksheet,
            credentials_file=credentials_file,
        )
