from __future__ import annotations

import re
from typing import Any

from app.models.resume.resume_ast import ResumeAST


# ---------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------

NUMBER_PATTERN = re.compile(
    r"""
    (?<![\w.])
    (
        \d+(?:\.\d+)?
        |
        \d+(?:,\d{3})+
    )
    (?:\s*[%+])?
    (?![\w.])
    """,
    re.VERBOSE,
)

YEAR_PATTERN = re.compile(
    r"(?<!\d)(?:19|20)\d{2}(?!\d)"
)

DATE_PATTERN = re.compile(
    r"""
    (?:
        (?:19|20)\d{2}
        |
        \d{1,2}[/-]\d{1,2}[/-]\d{2,4}
        |
        \d{4}-\d{2}-\d{2}
    )
    """,
    re.VERBOSE,
)


# ---------------------------------------------------------------------
# Generic AST flattening
# ---------------------------------------------------------------------

def _collect_strings(value: Any) -> list[str]:
    result: list[str] = []

    if isinstance(value, str):
        if value.strip():
            result.append(value.strip())
        return result

    if isinstance(value, list):
        for item in value:
            result.extend(_collect_strings(item))
        return result

    if isinstance(value, dict):
        for key, item in value.items():
            if key in {
                "source_text",
                "raw_text",
                "evidence",
            }:
                continue

            result.extend(_collect_strings(item))

    return result


def _normalise_text(value: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        value.strip().lower(),
    )


def _contains_semantic_string(
    needle: str,
    haystack: str,
) -> bool:
    """
    Case-insensitive containment with whitespace normalization.

    This is intentionally conservative.
    """
    return _normalise_text(needle) in _normalise_text(haystack)


def _all_text(content: Any) -> str:
    return " ".join(_collect_strings(content))


# ---------------------------------------------------------------------
# Fact extraction
# ---------------------------------------------------------------------

def extract_numeric_facts(content: Any) -> set[str]:
    text = _all_text(content)

    facts: set[str] = set()

    for match in NUMBER_PATTERN.finditer(text):
        facts.add(match.group(0).strip())

    for match in YEAR_PATTERN.finditer(text):
        facts.add(match.group(0))

    return facts


def extract_date_facts(content: Any) -> set[str]:
    text = _all_text(content)

    return {
        match.group(0)
        for match in DATE_PATTERN.finditer(text)
    }


def extract_named_facts(content: Any) -> set[str]:
    """
    Extract high-value identity strings.

    We deliberately focus on fields whose accidental modification
    would be dangerous.
    """

    facts: set[str] = set()

    def visit(value: Any, field_name: str | None = None) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {
                    "name",
                    "company",
                    "title",
                    "degree",
                    "field_of_study",
                    "issuer",
                    "credential_id",
                }:
                    if isinstance(item, str) and item.strip():
                        facts.add(item.strip())

                visit(item, key)

        elif isinstance(value, list):
            for item in value:
                visit(item, field_name)

    visit(content)

    return facts


def extract_technology_facts(content: Any) -> set[str]:
    """
    Extract technology/tool/framework/platform names from the AST.

    The AST already represents the user's declared technologies, so
    these are safer than attempting to maintain a global technology
    dictionary.
    """

    technologies: set[str] = set()

    def visit(value: Any, field_name: str | None = None) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {
                    "technologies",
                    "skills",
                }:
                    visit(item, key)
                else:
                    visit(item, key)

        elif isinstance(value, list):
            for item in value:
                visit(item, field_name)

        elif isinstance(value, str):
            if field_name in {
                "technologies",
                "skills",
            }:
                if value.strip():
                    technologies.add(value.strip())

    visit(content)

    return technologies


# ---------------------------------------------------------------------
# Preservation validation
# ---------------------------------------------------------------------

def validate_fact_preservation(
    original_content: Any,
    optimized_content: Any,
) -> list[str]:
    """
    Deterministically verify that optimization did not silently remove
    important facts.

    Returns an empty list when safe.
    """

    errors: list[str] = []

    original_numbers = extract_numeric_facts(
        original_content
    )

    optimized_numbers = extract_numeric_facts(
        optimized_content
    )

    for fact in sorted(original_numbers):
        if fact not in optimized_numbers:
            errors.append(
                f"Numeric fact '{fact}' from the original "
                f"content was not preserved."
            )

    original_dates = extract_date_facts(
        original_content
    )

    optimized_dates = extract_date_facts(
        optimized_content
    )

    for fact in sorted(original_dates):
        if fact not in optimized_dates:
            errors.append(
                f"Date fact '{fact}' from the original "
                f"content was not preserved."
            )

    original_names = extract_named_facts(
        original_content
    )

    optimized_text = _all_text(
        optimized_content
    )

    for fact in sorted(original_names):
        if not _contains_semantic_string(
            fact,
            optimized_text,
        ):
            errors.append(
                f"Named fact '{fact}' from the original "
                f"content was not preserved."
            )

    original_technologies = extract_technology_facts(
        original_content
    )

    for technology in sorted(original_technologies):
        if not _contains_semantic_string(
            technology,
            optimized_text,
        ):
            errors.append(
                f"Technology/skill '{technology}' from the "
                f"original content was not preserved."
            )

    return errors


# ---------------------------------------------------------------------
# Structural validation
# ---------------------------------------------------------------------

def validate_structure_preservation(
    original_content: Any,
    optimized_content: Any,
) -> list[str]:
    errors: list[str] = []

    if isinstance(original_content, list):
        if not isinstance(optimized_content, list):
            return [
                "Original section is a list but optimized section "
                "is not a list."
            ]

        if len(original_content) != len(optimized_content):
            errors.append(
                "Optimization changed the number of items in the "
                "section. Items must not be added or removed during "
                "general ATS optimization."
            )

    return errors


# ---------------------------------------------------------------------
# Combined validation
# ---------------------------------------------------------------------

def validate_optimization_safety(
    original_content: Any,
    optimized_content: Any,
) -> list[str]:
    errors: list[str] = []

    errors.extend(
        validate_fact_preservation(
            original_content=original_content,
            optimized_content=optimized_content,
        )
    )

    errors.extend(
        validate_structure_preservation(
            original_content=original_content,
            optimized_content=optimized_content,
        )
    )

    return errors


# ---------------------------------------------------------------------
# Provenance preservation
# ---------------------------------------------------------------------

PROVENANCE_FIELDS = {
    "source_text",
    "evidence",
}


def preserve_provenance(
    original: Any,
    optimized: Any,
) -> Any:
    """
    Restore provenance from the original AST.

    The LLM should never be trusted to recreate provenance.

    For lists, items are matched by position because general ATS
    optimization is not allowed to add/remove records.
    """

    if isinstance(original, dict) and isinstance(optimized, dict):
        result = dict(optimized)

        for field in PROVENANCE_FIELDS:
            if field in original:
                original_value = original[field]

                # Always preserve original provenance.
                result[field] = original_value

        for key in set(original.keys()) & set(optimized.keys()):
            if key in PROVENANCE_FIELDS:
                continue

            result[key] = preserve_provenance(
                original[key],
                optimized[key],
            )

        return result

    if isinstance(original, list) and isinstance(optimized, list):
        result = []

        for index, optimized_item in enumerate(
            optimized
        ):
            if index < len(original):
                result.append(
                    preserve_provenance(
                        original[index],
                        optimized_item,
                    )
                )
            else:
                result.append(optimized_item)

        return result

    return optimized


# ---------------------------------------------------------------------
# AST-level safety validation
# ---------------------------------------------------------------------

def validate_resume_ast_integrity(
    original_ast: ResumeAST,
    optimized_ast: ResumeAST,
) -> list[str]:
    """
    High-level safety checks after all sections have been applied.
    """

    errors: list[str] = []

    original = original_ast.model_dump(
        mode="json"
    )

    optimized = optimized_ast.model_dump(
        mode="json"
    )

    # source_text must remain identical.
    if original.get("source_text") != optimized.get(
        "source_text"
    ):
        errors.append(
            "ResumeAST.source_text was modified."
        )

    # Contact information is not an optimization target.
    if original.get("contact") != optimized.get(
        "contact"
    ):
        errors.append(
            "Contact information was modified during "
            "optimization."
        )

    # Metadata is not an optimization target.
    if original.get("metadata") != optimized.get(
        "metadata"
    ):
        errors.append(
            "Resume metadata was modified during "
            "optimization."
        )

    return errors