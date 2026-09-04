from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from app.models.image.invoice import Invoice
from app.integration.output.output import Output, OutputError


class JSONOutput(Output):
    """Write one or more invoices as JSON."""

    def write(self, invoices: Sequence[Invoice], **kwargs) -> None:
        output_path_value = kwargs.get("output_path")
        payload = [invoice.model_dump(mode="json") for invoice in invoices]
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)

        if not output_path_value:
            print(serialized)
            return

        output_path = Path(output_path_value)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            output_path.write_text(serialized, encoding="utf-8")
        except OSError as exc:
            raise OutputError(
                f"Unable to write JSON output: {output_path}"
            ) from exc
