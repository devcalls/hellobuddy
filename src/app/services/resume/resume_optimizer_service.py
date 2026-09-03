from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from app.models.resume.optimization import (
    OptimizationGuideline,
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

        # CLI requests normally omit guidelines. The optimizer must still
        # have a concrete policy, otherwise the LLM receives no guideline IDs
        # it can legally attach to proposed changes.
        guidelines = request.guidelines or self._default_guidelines()

        experience_selected = ResumeSection.EXPERIENCE in request.sections

        for section in request.sections:

            if not self._section_exists(
                current_resume,
                section,
            ):
                continue

            excluded_record_ids: set[str] = set()
            if section == ResumeSection.PROJECTS and experience_selected:
                excluded_record_ids = {
                    project_id
                    for experience in current_resume.experience
                    for project_id in experience.project_ids
                }

            llm_result = (
                self.section_optimizer.optimize_section(
                    resume=current_resume,
                    section=section,
                    mode=request.mode,
                    guidelines=guidelines,
                    job_description=request.job_description,
                    excluded_record_ids=excluded_record_ids,
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
                # "optimized" is an application-level outcome, not merely
                # the LLM's declaration. A section is optimized only when at
                # least one proposal survives validation and is applied.
                optimized=applied > 0,
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
    def _default_guidelines() -> list[OptimizationGuideline]:
        return [
            OptimizationGuideline(
                id="active_voice",
                description="Prefer active voice and direct sentence construction over passive voice.",
            ),
            OptimizationGuideline(
                id="concise_language",
                description="Remove unnecessary words, filler, repetition, and verbose phrasing while preserving meaning.",
            ),
            OptimizationGuideline(
                id="achievement_oriented",
                description="Where supported by the original content, emphasize achievements, outcomes, impact, ownership, scope, and results.",
            ),
            OptimizationGuideline(
                id="preserve_metrics",
                description="Preserve all existing numbers, percentages, monetary values, durations, scale indicators, and other quantifiable evidence.",
            ),
            OptimizationGuideline(
                id="preserve_technical_terms",
                description="Preserve meaningful technologies, tools, frameworks, platforms, programming languages, and domain terminology.",
            ),
            OptimizationGuideline(
                id="group_skills",
                description="Group existing skills into meaningful categories without adding skills.",
                applies_to=[ResumeSection.SKILLS],
            ),
            OptimizationGuideline(
                id="remove_redundancy",
                description="Reduce redundant statements and repeated information without removing meaningful evidence.",
            ),
            OptimizationGuideline(
                id="standardize_terminology",
                description="Use consistent terminology and capitalization for the same technology, skill, role, or concept.",
            ),
            OptimizationGuideline(
                id="no_new_facts",
                description="Do not introduce technologies, skills, metrics, achievements, responsibilities, companies, titles, dates, certifications, education, or unsupported claims.",
            ),
        ]

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