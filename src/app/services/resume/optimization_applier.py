from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.models.resume.optimization import (
    OptimizationChange,
    ResumeSection,
)
from app.models.resume.resume_ast import ResumeAST
from app.services.resume.optimization_guard import (
    validate_text_change,
)


class OptimizationApplier:

    def apply(
        self,
        *,
        resume: ResumeAST,
        section: ResumeSection,
        changes: list[OptimizationChange],
    ) -> tuple[ResumeAST, list[str], int]:

        optimized_resume = deepcopy(resume)

        errors: list[str] = []
        applied = 0

        for change in changes:

            try:
                current_value = self._get_field(
                    optimized_resume,
                    section,
                    change.record_id,
                    change.field,
                )

            except ValueError as exc:
                errors.append(str(exc))
                continue

            if not isinstance(current_value, str):
                errors.append(
                    f"{section.value}: "
                    f"{change.record_id}.{change.field} "
                    f"is not a text field."
                )
                continue

            if current_value != change.original_text:
                errors.append(
                    f"{section.value}: "
                    f"{change.record_id}.{change.field} "
                    f"original text does not match ResumeAST."
                )
                continue

            guard_errors = validate_text_change(
                original_text=current_value,
                optimized_text=change.optimized_text,
            )

            if guard_errors:
                errors.extend(
                    f"{section.value}: "
                    f"{change.record_id}.{change.field}: "
                    f"{error}"
                    for error in guard_errors
                )
                continue

            self._set_field(
                optimized_resume,
                section,
                change.record_id,
                change.field,
                change.optimized_text,
            )

            applied += 1

        return (
            optimized_resume,
            errors,
            applied,
        )

    def _get_field(
        self,
        resume: ResumeAST,
        section: ResumeSection,
        record_id: str,
        field: str,
    ) -> Any:

        record = self._find_record(
            resume,
            section,
            record_id,
        )

        return self._resolve_field(
            record,
            field,
        )

    def _set_field(
        self,
        resume: ResumeAST,
        section: ResumeSection,
        record_id: str,
        field: str,
        value: str,
    ) -> None:

        record = self._find_record(
            resume,
            section,
            record_id,
        )

        parts = field.split(".")

        target = record

        for part in parts[:-1]:
            target = self._resolve_field(
                target,
                part,
            )

        final_field = parts[-1]

        if hasattr(target, final_field):
            setattr(
                target,
                final_field,
                value,
            )
        elif isinstance(target, dict):
            target[final_field] = value
        else:
            raise ValueError(
                f"Unable to set field '{field}'."
            )

    def _find_record(
        self,
        resume: ResumeAST,
        section: ResumeSection,
        record_id: str,
    ) -> Any:
        if section == ResumeSection.SUMMARY:
            if record_id == "summary":
                return resume

            raise ValueError(
                f"Summary record '{record_id}' not found. "
                f"Expected record_id='summary'."
            )

        section_data = getattr(
            resume,
            section.value,
        )

        if not isinstance(section_data, list):
            raise ValueError(
                f"Section '{section.value}' is not a list."
            )

        record = self._search_by_id(
            section_data,
            record_id,
        )

        if record is None:
            raise ValueError(
                f"Record '{record_id}' not found "
                f"in section '{section.value}'."
            )

        return record

    def _search_by_id(
        self,
        items: list[Any],
        record_id: str,
    ) -> Any | None:

        for item in items:

            if getattr(item, "id", None) == record_id:
                return item

            nested = self._search_nested(
                item,
                record_id,
            )

            if nested is not None:
                return nested

        return None

    def _search_nested(
        self,
        value: Any,
        record_id: str,
    ) -> Any | None:

        if isinstance(value, list):

            for item in value:
                result = self._search_nested(
                    item,
                    record_id,
                )

                if result is not None:
                    return result

        elif hasattr(value, "model_dump"):

            if getattr(value, "id", None) == record_id:
                return value

            for field_value in value.__dict__.values():

                result = self._search_nested(
                    field_value,
                    record_id,
                )

                if result is not None:
                    return result

        return None

    @staticmethod
    def _resolve_field(
        target: Any,
        field: str,
    ) -> Any:

        if hasattr(target, field):
            return getattr(target, field)

        if isinstance(target, dict):
            if field in target:
                return target[field]

        raise ValueError(
            f"Field '{field}' not found."
        )