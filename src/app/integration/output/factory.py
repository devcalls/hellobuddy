from __future__ import annotations

from app.integration.output.csv_output import CSVOutput
from app.integration.output.google_sheets_output import GoogleSheetsOutput
from app.integration.output.json_output import JSONOutput
from app.integration.output.output import Output


class OutputFactory:
    @staticmethod
    def create(output_format: str) -> Output:
        normalized = output_format.lower()

        if normalized == "json":
            return JSONOutput()
        if normalized == "csv":
            return CSVOutput()
        if normalized in {"google-sheets", "google_sheets", "sheets"}:
            return GoogleSheetsOutput()

        raise ValueError(
            f"Unsupported output format: {output_format}. "
            "Supported formats: json, csv, google-sheets"
        )
