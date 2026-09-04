from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from app.models.image.invoice import Invoice
from app.integration.output.output import Output, OutputError
from app.integration.output.row_mapper import INVOICE_HEADERS, invoice_rows


class GoogleSheetsOutput(Output):
    """Write consolidated invoice rows to a Google Sheet.

    Authentication uses a Google service-account JSON file. The target
    spreadsheet must be shared with the service-account email address.
    """

    def write(self, invoices: Sequence[Invoice], **kwargs) -> None:
        spreadsheet = kwargs.get("spreadsheet")
        worksheet = kwargs.get("worksheet", "Invoices")
        credentials_file = kwargs.get("credentials_file")

        if not spreadsheet:
            raise OutputError(
                "Google Sheets output requires a spreadsheet name or ID."
            )

        credentials_file = credentials_file or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE"
        )
        if not credentials_file:
            raise OutputError(
                "Google Sheets authentication requires "
                "GOOGLE_SERVICE_ACCOUNT_FILE or --credentials."
            )

        credentials_path = Path(credentials_file)
        if not credentials_path.is_file():
            raise OutputError(
                f"Google service-account file not found: {credentials_path}"
            )

        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError as exc:
            raise OutputError(
                "Google Sheets output requires gspread and google-auth. "
                "Install the optional Google Sheets dependencies."
            ) from exc

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        try:
            credentials = Credentials.from_service_account_file(
                str(credentials_path),
                scopes=scopes,
            )
            client = gspread.authorize(credentials)

            try:
                spreadsheet_obj = client.open_by_key(spreadsheet)
            except Exception:
                spreadsheet_obj = client.open(spreadsheet)

            try:
                sheet = spreadsheet_obj.worksheet(worksheet)
            except Exception:
                sheet = spreadsheet_obj.add_worksheet(
                    title=worksheet,
                    rows=max(len(invoices) * 2 + 10, 100),
                    cols=len(INVOICE_HEADERS),
                )

            values = [INVOICE_HEADERS, *invoice_rows(invoices)]
            sheet.clear()
            sheet.update(
                range_name="A1",
                values=values,
            )
        except Exception as exc:
            if isinstance(exc, OutputError):
                raise
            raise OutputError(
                f"Unable to write Google Sheets output: {exc}"
            ) from exc
