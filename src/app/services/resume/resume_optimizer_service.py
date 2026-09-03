from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from app.models.resume.optimization import (
    OptimizationMode,
    ResumeOptimizationRequest,
    ResumeOptimizationResult,
    ResumeSection,
    SectionOptimizationResult,
)
from app.models.resume.resume_ast import ResumeAST
from app.services.resume.optimization_applier import (
    OptimizationApplier,
)
from app.services.resume.section_optimizer import (
    SectionOptimizer,
)


class ResumeOptimizerService:

    def __init__(
        self,
        section_optimizer: SectionOptimizer,
        optimization_applier: OptimizationApplier,
    ) -> None:

        self.section_optimizer = section_optimizer
        self.optimization_applier = optimization_applier

    def optimize_ast(
        self,
        *,
        resume: ResumeAST,
        request: ResumeOptimizationRequest,
    ) -> ResumeOptimizationResult:

        original_resume = deepcopy(resume)

        current_resume = deepcopy(resume)

        section_results: list[
            SectionOptimizationResult
        ] = []

        validation_errors: list[str] = []

        for section in request.sections:

            if not self._section_exists(
                current_resume,
                section,
            ):
                continue

            llm_result = (
                self.section_optimizer.optimize_section(
                    resume=current_resume,
                    section=section,
                    mode=request.mode,
                    guidelines=request.guidelines,
                    job_description=request.job_description,
                )
            )

            (
                current_resume,
                errors,
                applied,
            ) = self.optimization_applier.apply(
                resume=current_resume,
                section=section,
                changes=llm_result.changes,
            )

            section_result = SectionOptimizationResult(
                section=section,
                optimized=llm_result.optimized,
                findings=llm_result.findings,
                changes=llm_result.changes,
                applied_changes=applied,
                validation_passed=not errors,
                validation_errors=errors,
            )

            section_results.append(
                section_result
            )

            validation_errors.extend(
                errors
            )

        return ResumeOptimizationResult(
            mode=request.mode,
            original_resume=original_resume.model_dump(
                mode="json"
            ),
            optimized_resume=current_resume.model_dump(
                mode="json"
            ),
            sections=section_results,
            validation_passed=not validation_errors,
            validation_errors=validation_errors,
        )

    @staticmethod
    def _section_exists(
        resume: ResumeAST,
        section: ResumeSection,
    ) -> bool:

        if not hasattr(
            resume,
            section.value,
        ):
            return False

        value = getattr(
            resume,
            section.value,
        )

        if section == ResumeSection.SUMMARY:
            return bool(value)

        return bool(value)