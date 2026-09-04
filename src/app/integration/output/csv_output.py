from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

from app.models.image.invoice import Invoice
from app.integration.output.output import Output, OutputError
from app.integration.output.row_mapper import INVOICE_HEADERS, invoice_rows


class CSVOutput(Output):
    """Write invoices as a consolidated, line-item-oriented CSV file."""

    def write(self, invoices: Sequence[Invoice], **kwargs) -> None:
        output_path_value = kwargs.get("output_path")
        if not output_path_value:
            raise OutputError("CSV output requires an output_path.")

        output_path = Path(output_path_value)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with output_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(INVOICE_HEADERS)
                writer.writerows(invoice_rows(invoices))
        except OSError as exc:
            raise OutputError(
                f"Unable to write CSV output: {output_path}"
            ) from exc
