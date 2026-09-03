from __future__ import annotations

import re
from datetime import date
from typing import Any


NUMBER_PATTERN = re.compile(
    r"""
    (?:
        \b\d+(?:\.\d+)?%?\b
        |
        \$\s?\d+(?:\.\d+)?
        |
        \b\d+\+\b
    )
    """,
    re.VERBOSE,
)


def extract_numbers(text: str) -> set[str]:
    return set(
        NUMBER_PATTERN.findall(text or "")
    )


def validate_text_change(
    *,
    original_text: str,
    optimized_text: str,
) -> list[str]:

    errors: list[str] = []

    original_numbers = extract_numbers(
        original_text
    )

    optimized_numbers = extract_numbers(
        optimized_text
    )

    missing_numbers = (
        original_numbers - optimized_numbers
    )

    if missing_numbers:
        errors.append(
            "Optimization removed existing numeric facts: "
            + ", ".join(sorted(missing_numbers))
        )

    return errors