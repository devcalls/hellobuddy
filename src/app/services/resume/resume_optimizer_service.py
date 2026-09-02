from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from app.models.resume.optimization import (
    OptimizationGuideline,
    OptimizationMode,
    ResumeOptimizationRequest,
    ResumeOptimizationResult,
    ResumeSection,
    SectionOptimizationResult,
)
from app.models.resume.resume_ast import (
    Certification,
    Education,
    Experience,
    Project,
    ResumeAST,
    Skill,
)
from app.services.resume.resume_parser_service import ResumeParserService
from app.services.resume.section_optimizer import SectionOptimizer


class ResumeOptimizerService:
    """
    Orchestrates resume analysis and ATS optimization.

    Main pipeline:

        Resume file
            ↓
        ResumeParserService
            ↓
        ResumeAST
            ↓
        SectionOptimizer
            ↓
        SectionOptimizationResult
            ↓
        Pydantic validation/conversion
            ↓
        Optimized ResumeAST

    The original ResumeAST is never mutated.
    """

    def __init__(
        self,
        parser_service: ResumeParserService,
        section_optimizer: SectionOptimizer,
    ) -> None:
        self.parser_service = parser_service
        self.section_optimizer = section_optimizer

    # ================================================================
    # PUBLIC API
    # ================================================================

    def optimize_file(
        self,
        resume_path: Path,
        request: ResumeOptimizationRequest | None = None,
    ) -> ResumeOptimizationResult:
        """
        Analyze a resume file and optimize the resulting ResumeAST.

        This is the primary entry point for:

            hellobuddy resume optimize resume.pdf
        """

        request = request or ResumeOptimizationRequest()

        analysis = self.parser_service.parse(resume_path)

        return self.optimize_ast(
            resume_ast=analysis.resume,
            request=request,
        )

    def optimize_ast_file(
        self,
        ast_path: str | Path,
        request: ResumeOptimizationRequest | None = None,
    ) -> ResumeOptimizationResult:

        resume_ast = self.parser_service.load_ast(ast_path)

        return self.optimize_ast(
            resume_ast=resume_ast,
            request=request,
        )

    def optimize_ast(
        self,
        resume_ast: ResumeAST,
        request: ResumeOptimizationRequest | None = None,
    ) -> ResumeOptimizationResult:
        """
        Optimize an existing ResumeAST.

        Useful when an AST has already been generated and should
        not be parsed again.
        """

        request = request or ResumeOptimizationRequest()

        original_resume = self._serialize_ast(resume_ast)

        # Never mutate the caller's ResumeAST.
        optimized_resume_ast = deepcopy(resume_ast)

        guidelines = self._get_guidelines(request)

        section_results: list[SectionOptimizationResult] = []
        validation_errors: list[str] = []

        for section in request.sections:

            content = self._get_section_content(
                resume_ast=resume_ast,
                section=section,
            )

            # Section does not exist / is empty.
            if content is None:
                continue

            applicable_guidelines = self._get_applicable_guidelines(
                section=section,
                guidelines=guidelines,
            )

            # No applicable guidelines means there is nothing
            # for this section to optimize.
            if not applicable_guidelines:
                continue

            try:
                result = self.section_optimizer.optimize(
                    section=section,
                    content=content,
                    guidelines=applicable_guidelines,
                    mode=request.mode,
                )

            except Exception as exc:
                error = f"{section.value}: " f"LLM optimization failed: {exc}"

                validation_errors.append(error)

                section_results.append(
                    self._failed_section_result(
                        section=section,
                        content=content,
                        error=error,
                    )
                )

                continue

            # --------------------------------------------------------
            # Validate and convert the LLM-generated section.
            # --------------------------------------------------------

            converted_content, conversion_errors = self._validate_and_convert_section(
                section=section,
                optimized_content=result.optimized_content,
            )

            if conversion_errors:
                result.validation_passed = False
                result.validation_errors.extend(conversion_errors)

                validation_errors.extend(
                    self._prefix_validation_errors(
                        section=section,
                        errors=conversion_errors,
                    )
                )

                section_results.append(result)

                continue

            # --------------------------------------------------------
            # Replace the generic LLM content with the validated
            # Pydantic content.
            # --------------------------------------------------------

            result.optimized_content = converted_content

            # --------------------------------------------------------
            # Apply only validated content.
            # --------------------------------------------------------

            self._apply_section_result(
                resume_ast=optimized_resume_ast,
                result=result,
            )

            section_results.append(result)

        optimized_resume = self._serialize_ast(optimized_resume_ast)

        return ResumeOptimizationResult(
            mode=request.mode,
            original_resume=original_resume,
            optimized_resume=optimized_resume,
            sections=section_results,
            validation_passed=not validation_errors,
            validation_errors=validation_errors,
        )

    # ================================================================
    # SECTION EXTRACTION
    # ================================================================

    def _get_section_content(
        self,
        resume_ast: ResumeAST,
        section: ResumeSection,
    ) -> Any:
        """
        Get a section from ResumeAST.

        Explicit mapping is intentional. It prevents the optimizer
        from depending on arbitrary attribute names.
        """

        section_mapping: dict[ResumeSection, Any] = {
            ResumeSection.SUMMARY: resume_ast.summary,
            ResumeSection.EXPERIENCE: resume_ast.experience,
            ResumeSection.SKILLS: resume_ast.skills,
            ResumeSection.PROJECTS: resume_ast.projects,
            ResumeSection.EDUCATION: resume_ast.education,
            ResumeSection.CERTIFICATIONS: resume_ast.certifications,
        }

        return section_mapping.get(section)

    # ================================================================
    # SECTION TYPE MAPPING
    # ================================================================

    def _get_section_model(
        self,
        section: ResumeSection,
    ) -> Type[BaseModel] | None:
        """
        Return the Pydantic model expected for an individual item
        in a structured ResumeAST section.

        Sections that contain primitive values rather than Pydantic
        models return None.
        """

        model_mapping: dict[
            ResumeSection,
            Type[BaseModel],
        ] = {
            ResumeSection.EXPERIENCE: Experience,
            ResumeSection.SKILLS: Skill,
            ResumeSection.PROJECTS: Project,
            ResumeSection.EDUCATION: Education,
            ResumeSection.CERTIFICATIONS: Certification,
        }

        return model_mapping.get(section)

    # ================================================================
    # LLM OUTPUT VALIDATION / CONVERSION
    # ================================================================

    def _validate_and_convert_section(
        self,
        section: ResumeSection,
        optimized_content: Any,
    ) -> tuple[Any, list[str]]:
        """
        Convert generic LLM output into the exact type expected
        by ResumeAST.

        This is the critical safety boundary between the LLM and
        the canonical ResumeAST.
        """

        try:

            # --------------------------------------------------------
            # SUMMARY
            # --------------------------------------------------------

            if section == ResumeSection.SUMMARY:

                if optimized_content is None:
                    return None, []

                if not isinstance(optimized_content, str):
                    return (
                        None,
                        ["Summary optimization must return a string."],
                    )

                return optimized_content.strip(), []

            # --------------------------------------------------------
            # Structured list sections
            # --------------------------------------------------------

            model_class = self._get_section_model(section)

            if model_class is not None:

                if not isinstance(optimized_content, list):
                    return (
                        None,
                        [f"{section.value} optimization must " "return a list."],
                    )

                validated_items: list[BaseModel] = []

                for index, item in enumerate(optimized_content):

                    try:
                        if isinstance(item, model_class):
                            validated_item = item
                        else:
                            validated_item = model_class.model_validate(item)

                        validated_items.append(validated_item)

                    except ValidationError as exc:
                        return (
                            None,
                            [
                                (
                                    f"{section.value}[{index}] "
                                    f"failed validation: {error}"
                                )
                                for error in exc.errors()
                            ],
                        )

                return validated_items, []

            return (
                None,
                [
                    (
                        f"No ResumeAST conversion rule exists "
                        f"for section '{section.value}'."
                    )
                ],
            )

        except Exception as exc:
            return (
                None,
                [f"Failed to validate {section.value} " f"optimization: {exc}"],
            )

    # ================================================================
    # APPLY VALIDATED RESULT
    # ================================================================

    def _apply_section_result(
        self,
        resume_ast: ResumeAST,
        result: SectionOptimizationResult,
    ) -> None:
        """
        Apply validated optimization content to a ResumeAST.

        This method should only receive content that has already
        passed _validate_and_convert_section().
        """

        section = result.section
        content = result.optimized_content

        if section == ResumeSection.SUMMARY:
            resume_ast.summary = content
            return

        if section == ResumeSection.EXPERIENCE:
            resume_ast.experience = content
            return

        if section == ResumeSection.SKILLS:
            resume_ast.skills = content
            return

        if section == ResumeSection.PROJECTS:
            resume_ast.projects = content
            return

        if section == ResumeSection.EDUCATION:
            resume_ast.education = content
            return

        if section == ResumeSection.CERTIFICATIONS:
            resume_ast.certifications = content
            return

        raise ValueError(f"Unsupported resume section: {section}")

    # ================================================================
    # GUIDELINES
    # ================================================================

    def _get_guidelines(
        self,
        request: ResumeOptimizationRequest,
    ) -> list[OptimizationGuideline]:

        if request.guidelines:
            return request.guidelines

        return self._default_guidelines()

    def _get_applicable_guidelines(
        self,
        section: ResumeSection,
        guidelines: list[OptimizationGuideline],
    ) -> list[OptimizationGuideline]:

        return [
            guideline
            for guideline in guidelines
            if guideline.enabled
            and (not guideline.applies_to or section in guideline.applies_to)
        ]

    def _default_guidelines(
        self,
    ) -> list[OptimizationGuideline]:

        return [
            OptimizationGuideline(
                id="active_voice",
                description=(
                    "Prefer active voice and direct sentence "
                    "construction over passive voice."
                ),
            ),
            OptimizationGuideline(
                id="concise_language",
                description=(
                    "Remove unnecessary words, filler, repetition, "
                    "and verbose phrasing while preserving meaning."
                ),
            ),
            OptimizationGuideline(
                id="achievement_oriented",
                description=(
                    "Where supported by the original content, "
                    "emphasize achievements, outcomes, impact, "
                    "ownership, scope, and results."
                ),
            ),
            OptimizationGuideline(
                id="preserve_metrics",
                description=(
                    "Preserve all existing numbers, percentages, "
                    "monetary values, durations, scale indicators, "
                    "and other quantifiable evidence."
                ),
            ),
            OptimizationGuideline(
                id="preserve_technical_terms",
                description=(
                    "Preserve meaningful technologies, tools, "
                    "frameworks, platforms, programming languages, "
                    "and domain terminology."
                ),
            ),
            OptimizationGuideline(
                id="group_skills",
                description=(
                    "Group existing skills into meaningful categories "
                    "without adding skills."
                ),
                applies_to=[ResumeSection.SKILLS],
            ),
            OptimizationGuideline(
                id="remove_redundancy",
                description=(
                    "Reduce redundant statements and repeated "
                    "information without removing meaningful evidence."
                ),
            ),
            OptimizationGuideline(
                id="standardize_terminology",
                description=(
                    "Use consistent terminology and capitalization "
                    "for the same technology, skill, role, or concept."
                ),
            ),
            OptimizationGuideline(
                id="no_new_facts",
                description=(
                    "Do not introduce technologies, skills, metrics, "
                    "achievements, responsibilities, companies, "
                    "titles, dates, certifications, education, or "
                    "unsupported claims."
                ),
            ),
        ]

    # ================================================================
    # SERIALIZATION
    # ================================================================

    def _serialize_ast(
        self,
        resume_ast: ResumeAST,
    ) -> dict[str, Any]:
        """
        Serialize ResumeAST using Pydantic v2's JSON-compatible mode.
        """

        return resume_ast.model_dump(mode="json")

    # ================================================================
    # ERROR HANDLING
    # ================================================================

    def _failed_section_result(
        self,
        section: ResumeSection,
        content: Any,
        error: str,
    ) -> SectionOptimizationResult:

        return SectionOptimizationResult(
            section=section,
            optimized=False,
            original_content=content,
            optimized_content=content,
            validation_passed=False,
            validation_errors=[error],
            findings=[],
            changes=[],
        )

    def _prefix_validation_errors(
        self,
        section: ResumeSection,
        errors: list[str],
    ) -> list[str]:

        return [f"{section.value}: {error}" for error in errors]
