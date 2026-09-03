from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import BaseModel, TypeAdapter, ValidationError

from app.models.resume.optimization import (
    OptimizationGuideline,
    ResumeOptimizationRequest,
    ResumeOptimizationResult,
    ResumeSection,
    SectionOptimizationLLMResult,
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

# ---------------------------------------------------------------------------
# Section → ResumeAST type mapping
# ---------------------------------------------------------------------------
#
# This is the canonical conversion/validation boundary between LLM output
# and ResumeAST.
#
# The LLM is allowed to return JSON, but Python decides whether that JSON
# is actually valid ResumeAST content.
#
SECTION_TYPE_ADAPTERS: dict[ResumeSection, TypeAdapter] = {
    ResumeSection.SUMMARY: TypeAdapter(str),
    ResumeSection.EXPERIENCE: TypeAdapter(list[Experience]),
    ResumeSection.SKILLS: TypeAdapter(list[Skill]),
    ResumeSection.PROJECTS: TypeAdapter(list[Project]),
    ResumeSection.EDUCATION: TypeAdapter(list[Education]),
    ResumeSection.CERTIFICATIONS: TypeAdapter(list[Certification]),
}


class ResumeOptimizerService:
    """
    Orchestrates resume parsing and ATS optimization.

    Supported flows:

        Resume file
            ↓
        ResumeParserService
            ↓
        ResumeAST
            ↓
        SectionOptimizer
            ↓
        SectionOptimizationLLMResult
            ↓
        JSON deserialization
            ↓
        Pydantic validation
            ↓
        Validated ResumeAST section
            ↓
        Optimized ResumeAST


    Or:

        Existing ResumeAST JSON
            ↓
        ResumeAST.model_validate()
            ↓
        SectionOptimizer
            ↓
        JSON deserialization
            ↓
        Pydantic validation
            ↓
        Optimized ResumeAST

    Important design rules:

    1. The original ResumeAST is never mutated.
    2. The LLM never directly controls the ResumeAST.
    3. Every optimized section is validated before being applied.
    4. If an LLM call fails, the original section is retained.
    5. If LLM output fails Pydantic validation, the original section
       is retained.
    """

    def __init__(
        self,
        parser_service: ResumeParserService,
        section_optimizer: SectionOptimizer,
    ) -> None:
        self.parser_service = parser_service
        self.section_optimizer = section_optimizer

    # ======================================================================
    # PUBLIC API
    # ======================================================================

    def optimize_file(
        self,
        resume_path: str | Path,
        request: ResumeOptimizationRequest | None = None,
    ) -> ResumeOptimizationResult:
        """
        Parse a resume document and optimize the resulting ResumeAST.

        Example:

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
        """
        Load an existing ResumeAST JSON file and optimize it.

        This path deliberately does NOT invoke DocumentReader or the
        resume parser.

        Example:

            hellobuddy resume optimize resume.ast.json --input-type ast
        """

        request = request or ResumeOptimizationRequest()

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

        The supplied ResumeAST is never mutated.
        """

        request = request or ResumeOptimizationRequest()

        # Keep the original representation for comparison/output.
        original_resume = self._serialize_ast(resume_ast)

        # Work on a copy only.
        optimized_resume_ast = deepcopy(resume_ast)

        guidelines = self._get_guidelines(request)

        section_results: list[SectionOptimizationResult] = []
        validation_errors: list[str] = []

        for section in request.sections:

            # --------------------------------------------------------------
            # Get current section content.
            # --------------------------------------------------------------

            content = self._get_section_content(
                resume_ast=resume_ast,
                section=section,
            )

            # Empty / missing section.
            if content is None:
                continue

            # --------------------------------------------------------------
            # Determine applicable guidelines.
            # --------------------------------------------------------------

            applicable_guidelines = self._get_applicable_guidelines(
                section=section,
                guidelines=guidelines,
            )

            if not applicable_guidelines:
                continue

            # --------------------------------------------------------------
            # Call LLM.
            # --------------------------------------------------------------

            try:
                llm_result = self.section_optimizer.optimize(
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

            # --------------------------------------------------------------
            # Convert LLM response into application-level result.
            # --------------------------------------------------------------

            section_result = self._process_llm_result(
                section=section,
                original_content=content,
                llm_result=llm_result,
            )

            section_results.append(section_result)

            # --------------------------------------------------------------
            # Do not apply invalid output.
            # --------------------------------------------------------------

            if not section_result.validation_passed:
                validation_errors.extend(
                    self._prefix_validation_errors(
                        section=section,
                        errors=section_result.validation_errors,
                    )
                )
                continue

            # --------------------------------------------------------------
            # Do not apply a section that the LLM says was not optimized.
            # --------------------------------------------------------------

            if not section_result.optimized:
                continue

            # --------------------------------------------------------------
            # Apply only validated content.
            # --------------------------------------------------------------

            self._apply_section_result(
                resume_ast=optimized_resume_ast,
                result=section_result,
            )

        # ------------------------------------------------------------------
        # Serialize final optimized AST.
        # ------------------------------------------------------------------

        optimized_resume = self._serialize_ast(optimized_resume_ast)

        return ResumeOptimizationResult(
            mode=request.mode,
            original_resume=original_resume,
            optimized_resume=optimized_resume,
            sections=section_results,
            validation_passed=not validation_errors,
            validation_errors=validation_errors,
        )

    # ======================================================================
    # LLM RESULT PROCESSING
    # ======================================================================

    def _process_llm_result(
        self,
        section: ResumeSection,
        original_content: Any,
        llm_result: SectionOptimizationLLMResult,
    ) -> SectionOptimizationResult:
        """
        Convert the Gemini-facing result into the application-level result.

        The important boundary is:

            optimized_content_json
                    ↓
                json.loads()
                    ↓
            section-specific TypeAdapter
                    ↓
            validated ResumeAST content

        The LLM never gets to directly inject arbitrary Python objects
        into ResumeAST.
        """

        # --------------------------------------------------------------
        # Make sure the LLM responded for the expected section.
        # --------------------------------------------------------------

        if llm_result.section != section:
            error = (
                f"LLM returned section "
                f"'{llm_result.section.value}' while "
                f"'{section.value}' was requested."
            )

            return SectionOptimizationResult(
                section=section,
                optimized=False,
                original_content=original_content,
                optimized_content=original_content,
                findings=llm_result.findings,
                changes=llm_result.changes,
                validation_passed=False,
                validation_errors=[error],
            )

        # --------------------------------------------------------------
        # LLM explicitly says no optimization was made.
        #
        # We still parse/validate the returned content if present.
        # This allows the output to remain structurally safe.
        # --------------------------------------------------------------

        if not llm_result.optimized:
            return SectionOptimizationResult(
                section=section,
                optimized=False,
                original_content=original_content,
                optimized_content=original_content,
                findings=llm_result.findings,
                changes=llm_result.changes,
                validation_passed=True,
                validation_errors=[],
            )

        # --------------------------------------------------------------
        # optimized_content_json is required for an optimized result.
        # --------------------------------------------------------------

        if not llm_result.optimized_content_json:
            error = (
                f"{section.value}: "
                "LLM returned optimized=true but "
                "optimized_content_json is empty."
            )

            return SectionOptimizationResult(
                section=section,
                optimized=False,
                original_content=original_content,
                optimized_content=original_content,
                findings=llm_result.findings,
                changes=llm_result.changes,
                validation_passed=False,
                validation_errors=[error],
            )

        # --------------------------------------------------------------
        # Validate / convert.
        # --------------------------------------------------------------

        converted_content, conversion_errors = self._validate_and_convert_section(
            section=section,
            optimized_content_json=(llm_result.optimized_content_json),
        )

        if conversion_errors:
            return SectionOptimizationResult(
                section=section,
                optimized=False,
                original_content=original_content,
                optimized_content=original_content,
                findings=llm_result.findings,
                changes=llm_result.changes,
                validation_passed=False,
                validation_errors=conversion_errors,
            )

        # --------------------------------------------------------------
        # Successfully validated.
        # --------------------------------------------------------------

        return SectionOptimizationResult(
            section=section,
            optimized=True,
            original_content=original_content,
            optimized_content=converted_content,
            findings=llm_result.findings,
            changes=llm_result.changes,
            validation_passed=True,
            validation_errors=[],
        )

    # ======================================================================
    # SECTION EXTRACTION
    # ======================================================================

    def _get_section_content(
        self,
        resume_ast: ResumeAST,
        section: ResumeSection,
    ) -> Any:
        """
        Get a section from ResumeAST.

        Explicit mapping is intentional. It prevents the optimizer from
        depending on arbitrary attribute names.
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

    # ======================================================================
    # SECTION TYPE VALIDATION
    # ======================================================================

    def _validate_and_convert_section(
        self,
        section: ResumeSection,
        optimized_content_json: str,
    ) -> tuple[Any, list[str]]:
        """
        Deserialize and validate LLM-generated section content.

        The JSON is first parsed using json.loads(), then validated
        against the exact expected ResumeAST section type.

        Examples:

            summary
                → str

            experience
                → list[Experience]

            skills
                → list[Skill]

            projects
                → list[Project]

            education
                → list[Education]

            certifications
                → list[Certification]
        """

        adapter = SECTION_TYPE_ADAPTERS.get(section)

        if adapter is None:
            return (
                None,
                [
                    (
                        "No ResumeAST conversion rule exists "
                        f"for section '{section.value}'."
                    )
                ],
            )

        # ------------------------------------------------------------------
        # Deserialize JSON returned by the LLM.
        # ------------------------------------------------------------------

        try:
            raw_content = json.loads(optimized_content_json)
        except json.JSONDecodeError as exc:
            start = max(0, exc.pos - 200)
            end = min(len(optimized_content_json), exc.pos + 200)

            context = optimized_content_json[start:end]

            raise ValueError(
                f"optimized_content_json is not valid JSON: {exc}\n"
                f"Position: {exc.pos}\n"
                f"Context:\n{context}"
            ) from exc

        # ------------------------------------------------------------------
        # Validate against exact ResumeAST type.
        # ------------------------------------------------------------------

        try:
            validated_content = adapter.validate_python(raw_content)

            return validated_content, []

        except ValidationError as exc:
            errors = []

            for error in exc.errors():
                location = ".".join(str(part) for part in error.get("loc", ()))

                message = error.get(
                    "msg",
                    "Validation error",
                )

                if location:
                    errors.append((f"{section.value}" f"[{location}]: {message}"))
                else:
                    errors.append(f"{section.value}: {message}")

            return None, errors

        except Exception as exc:
            return (
                None,
                [
                    (
                        f"{section.value}: "
                        "Failed to validate optimized content: "
                        f"{exc}"
                    )
                ],
            )

    # ======================================================================
    # APPLY VALIDATED RESULT
    # ======================================================================

    def _apply_section_result(
        self,
        resume_ast: ResumeAST,
        result: SectionOptimizationResult,
    ) -> None:
        """
        Apply validated optimization content to ResumeAST.

        This method should only receive content that has already passed
        _validate_and_convert_section().
        """

        if not result.validation_passed:
            raise ValueError(
                "Cannot apply a section that failed validation: "
                f"{result.section.value}"
            )

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

    # ======================================================================
    # GUIDELINES
    # ======================================================================

    def _get_guidelines(
        self,
        request: ResumeOptimizationRequest,
    ) -> list[OptimizationGuideline]:
        """
        Return request-specific guidelines or the default ATS guidelines.
        """

        if request.guidelines:
            return request.guidelines

        return self._default_guidelines()

    def _get_applicable_guidelines(
        self,
        section: ResumeSection,
        guidelines: list[OptimizationGuideline],
    ) -> list[OptimizationGuideline]:
        """
        Filter guidelines applicable to the current section.
        """

        return [
            guideline
            for guideline in guidelines
            if guideline.enabled
            and (not guideline.applies_to or section in guideline.applies_to)
        ]

    def _default_guidelines(
        self,
    ) -> list[OptimizationGuideline]:
        """
        Default general ATS optimization guidelines.

        These guidelines constrain what the LLM is allowed to change.
        """

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
                applies_to=[
                    ResumeSection.SKILLS,
                ],
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

    # ======================================================================
    # SERIALIZATION
    # ======================================================================

    def _serialize_ast(
        self,
        resume_ast: ResumeAST,
    ) -> dict[str, Any]:
        """
        Serialize ResumeAST using Pydantic v2 JSON-compatible mode.
        """

        return resume_ast.model_dump(mode="json")

    # ======================================================================
    # ERROR HANDLING
    # ======================================================================

    def _failed_section_result(
        self,
        section: ResumeSection,
        content: Any,
        error: str,
    ) -> SectionOptimizationResult:
        """
        Create a safe failed result.

        The original content is retained so a failed LLM call can never
        destroy the existing ResumeAST content.
        """

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
        """
        Ensure validation errors are clearly associated with a section.

        Avoid double-prefixing errors that already start with the section
        name.
        """

        prefixed = []

        for error in errors:
            if error.startswith(f"{section.value}:"):
                prefixed.append(error)
            else:
                prefixed.append(f"{section.value}: {error}")

        return prefixed
