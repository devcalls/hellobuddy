
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

from app.models.resume.optimization import (
    OptimizationGuideline,
    ResumeOptimizationRequest,
    ResumeOptimizationResult,
    ResumeSection,
    SectionOptimizationResult,
)
from app.models.resume.resume_ast import (
    Achievement,
    Certification,
    Education,
    Experience,
    Project,
    ResumeAST,
    Skill,
)
from app.services.resume.optimization_guard import (
    preserve_provenance,
    validate_optimization_safety,
    validate_resume_ast_integrity,
)
from app.services.resume.resume_parser_service import (
    ResumeParserService,
)
from app.services.resume.section_optimizer import (
    SectionOptimizer,
)


# =====================================================================
# SECTION VALIDATION ADAPTERS
# =====================================================================

SECTION_TYPE_ADAPTERS = {
    ResumeSection.SUMMARY: TypeAdapter(str),

    ResumeSection.EXPERIENCE: TypeAdapter(
        list[Experience]
    ),

    ResumeSection.SKILLS: TypeAdapter(
        list[Skill]
    ),

    ResumeSection.PROJECTS: TypeAdapter(
        list[Project]
    ),

    ResumeSection.EDUCATION: TypeAdapter(
        list[Education]
    ),

    ResumeSection.CERTIFICATIONS: TypeAdapter(
        list[Certification]
    ),
}


class ResumeOptimizerService:
    """
    Orchestrates resume optimization.

    Pipeline:

        Resume
          |
          v
        ResumeAST
          |
          v
        SectionOptimizer
          |
          v
        Gemini
          |
          v
        SectionOptimizationLLMResult
          |
          v
        Decode optimized_content_json
          |
          v
        Normalize nested JSON serialization
          |
          v
        Pydantic validation
          |
          v
        Fact preservation
          |
          v
        Provenance restoration
          |
          v
        Re-validation
          |
          v
        Optimized ResumeAST

    Important design rule:

        The ResumeAST remains strict.

    If Gemini accidentally returns:

        "{"text": "..."}"

    instead of:

        {"text": "..."}

    we repair the serialization boundary.

    We do NOT loosen the Pydantic models to accept arbitrary strings.
    """

    def __init__(
        self,
        parser_service: ResumeParserService,
        section_optimizer: SectionOptimizer,
    ) -> None:

        self.parser_service = parser_service
        self.section_optimizer = section_optimizer

    # =================================================================
    # PUBLIC API
    # =================================================================

    def optimize_file(
        self,
        resume_path: Path,
        request: ResumeOptimizationRequest | None = None,
    ) -> ResumeOptimizationResult:

        request = (
            request
            or ResumeOptimizationRequest()
        )

        analysis = self.parser_service.parse(
            resume_path
        )

        return self.optimize_ast(
            resume_ast=analysis.resume,
            request=request,
        )

    def optimize_ast_file(
        self,
        ast_path: str | Path,
        request: ResumeOptimizationRequest | None = None,
    ) -> ResumeOptimizationResult:

        resume_ast = (
            self.parser_service.load_ast(
                ast_path
            )
        )

        return self.optimize_ast(
            resume_ast=resume_ast,
            request=request,
        )

    def optimize_ast(
        self,
        resume_ast: ResumeAST,
        request: ResumeOptimizationRequest | None = None,
    ) -> ResumeOptimizationResult:

        request = (
            request
            or ResumeOptimizationRequest()
        )

        original_resume = (
            self._serialize_ast(
                resume_ast
            )
        )

        # Never mutate caller-owned AST.
        optimized_resume_ast = deepcopy(
            resume_ast
        )

        guidelines = self._get_guidelines(
            request
        )

        section_results: list[
            SectionOptimizationResult
        ] = []

        validation_errors: list[str] = []

        for section in request.sections:

            original_content = (
                self._get_section_content(
                    resume_ast,
                    section,
                )
            )

            if self._is_empty_section(
                original_content
            ):
                continue

            applicable_guidelines = (
                self._get_applicable_guidelines(
                    section=section,
                    guidelines=guidelines,
                )
            )

            if not applicable_guidelines:
                continue

            # ---------------------------------------------------------
            # LLM optimization
            # ---------------------------------------------------------

            try:

                llm_result = (
                    self.section_optimizer.optimize(
                        section=section,
                        content=original_content,
                        guidelines=applicable_guidelines,
                        mode=request.mode,
                    )
                )

            except Exception as exc:

                error = (
                    f"{section.value}: "
                    f"LLM optimization failed: {exc}"
                )

                validation_errors.append(
                    error
                )

                section_results.append(
                    self._failed_section_result(
                        section=section,
                        content=original_content,
                        error=error,
                    )
                )

                continue

            # ---------------------------------------------------------
            # Decode + validate LLM content
            # ---------------------------------------------------------

            optimized_content, errors = (
                self._validate_optimized_content(
                    section=section,
                    optimized_content_json=(
                        llm_result.optimized_content_json
                    ),
                )
            )

            if errors:

                section_results.append(
                    SectionOptimizationResult(
                        section=section,
                        optimized=False,
                        original_content=original_content,
                        optimized_content=original_content,
                        findings=llm_result.findings,
                        changes=llm_result.changes,
                        validation_passed=False,
                        validation_errors=errors,
                    )
                )

                validation_errors.extend(
                    errors
                )

                continue

            # ---------------------------------------------------------
            # Deterministic fact preservation
            # ---------------------------------------------------------

            safety_errors = (
                validate_optimization_safety(
                    original_content=original_content,
                    optimized_content=optimized_content,
                )
            )

            if safety_errors:

                section_results.append(
                    SectionOptimizationResult(
                        section=section,
                        optimized=False,
                        original_content=original_content,
                        optimized_content=original_content,
                        findings=llm_result.findings,
                        changes=llm_result.changes,
                        validation_passed=False,
                        validation_errors=safety_errors,
                    )
                )

                validation_errors.extend(
                    safety_errors
                )

                continue

            # ---------------------------------------------------------
            # Restore provenance
            # ---------------------------------------------------------

            optimized_content = (
                preserve_provenance(
                    original=original_content,
                    optimized=optimized_content,
                )
            )

            # ---------------------------------------------------------
            # Re-validate after provenance merge
            # ---------------------------------------------------------

            optimized_content, errors = (
                self._validate_content(
                    section=section,
                    content=optimized_content,
                )
            )

            if errors:

                section_results.append(
                    SectionOptimizationResult(
                        section=section,
                        optimized=False,
                        original_content=original_content,
                        optimized_content=original_content,
                        findings=llm_result.findings,
                        changes=llm_result.changes,
                        validation_passed=False,
                        validation_errors=errors,
                    )
                )

                validation_errors.extend(
                    errors
                )

                continue

            # ---------------------------------------------------------
            # Apply
            # ---------------------------------------------------------

            section_result = (
                SectionOptimizationResult(
                    section=section,
                    optimized=llm_result.optimized,
                    original_content=original_content,
                    optimized_content=optimized_content,
                    findings=llm_result.findings,
                    changes=llm_result.changes,
                    validation_passed=True,
                    validation_errors=[],
                )
            )

            self._apply_section_result(
                resume_ast=optimized_resume_ast,
                result=section_result,
            )

            section_results.append(
                section_result
            )

        # =================================================================
        # Final AST integrity validation
        # =================================================================

        ast_integrity_errors = (
            validate_resume_ast_integrity(
                original_ast=resume_ast,
                optimized_ast=optimized_resume_ast,
            )
        )

        if ast_integrity_errors:

            validation_errors.extend(
                ast_integrity_errors
            )

        optimized_resume = (
            self._serialize_ast(
                optimized_resume_ast
            )
        )

        return ResumeOptimizationResult(
            mode=request.mode,
            original_resume=original_resume,
            optimized_resume=optimized_resume,
            sections=section_results,
            validation_passed=not validation_errors,
            validation_errors=validation_errors,
        )

    # =================================================================
    # SECTION ACCESS
    # =================================================================

    def _get_section_content(
        self,
        resume_ast: ResumeAST,
        section: ResumeSection,
    ) -> Any:

        mapping = {
            ResumeSection.SUMMARY:
                resume_ast.summary,

            ResumeSection.EXPERIENCE:
                resume_ast.experience,

            ResumeSection.SKILLS:
                resume_ast.skills,

            ResumeSection.PROJECTS:
                resume_ast.projects,

            ResumeSection.EDUCATION:
                resume_ast.education,

            ResumeSection.CERTIFICATIONS:
                resume_ast.certifications,
        }

        return mapping.get(section)

    def _is_empty_section(
        self,
        content: Any,
    ) -> bool:

        if content is None:
            return True

        if isinstance(content, str):
            return not content.strip()

        if isinstance(content, list):
            return len(content) == 0

        return False

    # =================================================================
    # JSON DECODING
    # =================================================================

    @classmethod
    def _decode_json_value(
        cls,
        value: Any,
        *,
        max_depth: int = 5,
    ) -> Any:
        """
        Recursively decode accidentally double/triple encoded JSON.

        Examples:

            '{"name": "x"}'
                ->
            {"name": "x"}

            '"{\\"name\\": \\"x\\"}"'
                ->
            {"name": "x"}

            [
                '{"name": "x"}',
                '{"name": "y"}'
            ]
                ->
            [
                {"name": "x"},
                {"name": "y"}
            ]

        The recursion is intentionally bounded.

        This method ONLY repairs serialization. It does not create
        missing resume information.
        """

        if max_depth <= 0:
            return value

        # -------------------------------------------------------------
        # STRING
        # -------------------------------------------------------------

        if isinstance(value, str):

            stripped = (
                cls._strip_json_markdown_fence(
                    value.strip()
                )
            )

            if not stripped:
                return value

            # A string can itself contain serialized JSON.

            if stripped.startswith(
                ("{", "[", '"')
            ):

                try:

                    decoded = json.loads(
                        stripped
                    )

                    return cls._decode_json_value(
                        decoded,
                        max_depth=max_depth - 1,
                    )

                except json.JSONDecodeError:

                    # Plain text is left untouched.
                    return value

            return value

        # -------------------------------------------------------------
        # LIST
        # -------------------------------------------------------------

        if isinstance(value, list):

            return [
                cls._decode_json_value(
                    item,
                    max_depth=max_depth - 1,
                )
                for item in value
            ]

        # -------------------------------------------------------------
        # DICTIONARY
        # -------------------------------------------------------------

        if isinstance(value, dict):

            return {
                key: cls._decode_json_value(
                    item,
                    max_depth=max_depth - 1,
                )
                for key, item in value.items()
            }

        return value

    @staticmethod
    def _strip_json_markdown_fence(
        value: str,
    ) -> str:
        """
        Remove markdown JSON fences.

        Handles:

            ```json
            {...}
            ```

        and:

            ```
            {...}
            ```
        """

        stripped = value.strip()

        if stripped.startswith(
            "```json"
        ):

            stripped = stripped[
                len("```json"):
            ].strip()

            if stripped.endswith("```"):
                stripped = stripped[
                    :-3
                ].strip()

        elif stripped.startswith(
            "```"
        ):

            stripped = stripped[
                3:
            ].strip()

            if stripped.endswith("```"):
                stripped = stripped[
                    :-3
                ].strip()

        return stripped

    @classmethod
    def _parse_optimized_json(
        cls,
        optimized_content_json: Any,
    ) -> Any:
        """
        Parse the outer optimized_content_json.

        Gemini is instructed to return this field as a string, e.g.:

            "[{\"name\":\"AWS\"}]"

        The method then recursively decodes the contents.
        """

        if optimized_content_json is None:

            raise ValueError(
                "optimized_content_json is null."
            )

        # Normally this is a string because that is how the Gemini
        # response model is defined.

        if not isinstance(
            optimized_content_json,
            str,
        ):

            return cls._decode_json_value(
                optimized_content_json
            )

        raw = (
            cls._strip_json_markdown_fence(
                optimized_content_json.strip()
            )
        )

        if not raw:

            raise ValueError(
                "optimized_content_json is empty."
            )

        try:

            decoded = json.loads(
                raw
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                "optimized_content_json is not valid JSON: "
                f"{exc}"
            ) from exc

        return cls._decode_json_value(
            decoded
        )

    # =================================================================
    # NESTED SECTION NORMALIZATION
    # =================================================================

    @classmethod
    def _normalize_project_content(
        cls,
        content: Any,
    ) -> Any:
        """
        Normalize Project content before Pydantic validation.

        The important case here is:

            projects[]
                └── achievements[]

        Gemini occasionally returns an achievement as:

            "{\"text\": \"...\", ...}"

        rather than:

            {"text": "...", ...}

        The generic decoder normally catches this. This method provides
        an explicit second normalization boundary for Project because
        Achievement is nested inside Project.

        IMPORTANT:

        If an achievement is ordinary prose rather than a serialized
        Achievement dictionary, it remains unchanged and Pydantic will
        reject it. We do not fabricate an Achievement object.
        """

        content = cls._decode_json_value(
            content
        )

        if not isinstance(
            content,
            list,
        ):
            return content

        normalized_projects: list[Any] = []

        for project_index, project in enumerate(
            content
        ):

            project = cls._decode_json_value(
                project
            )

            if not isinstance(
                project,
                dict,
            ):

                normalized_projects.append(
                    project
                )

                continue

            normalized_project = dict(
                project
            )

            # ---------------------------------------------------------
            # Project achievements
            # ---------------------------------------------------------

            achievements = (
                normalized_project.get(
                    "achievements"
                )
            )

            if isinstance(
                achievements,
                list,
            ):

                normalized_achievements: list[
                    Any
                ] = []

                for achievement_index, achievement in enumerate(
                    achievements
                ):

                    decoded_achievement = (
                        cls._decode_json_value(
                            achievement
                        )
                    )

                    # Diagnostic logging without changing content.
                    if not isinstance(
                        decoded_achievement,
                        dict,
                    ):

                        # Do not fail here. Pydantic should provide the
                        # authoritative validation error.
                        #
                        # This also lets us distinguish:
                        #
                        #   serialized Achievement
                        #
                        # from:
                        #
                        #   genuinely malformed LLM output
                        pass

                    normalized_achievements.append(
                        decoded_achievement
                    )

                normalized_project[
                    "achievements"
                ] = normalized_achievements

            normalized_projects.append(
                normalized_project
            )

        return normalized_projects

    @classmethod
    def _normalize_section_content(
        cls,
        section: ResumeSection,
        content: Any,
    ) -> Any:
        """
        Normalize LLM output according to the shape of the section.

        This is deliberately conservative.

        We only normalize representation/serialization. We do not
        modify resume facts.
        """

        content = cls._decode_json_value(
            content
        )

        # -------------------------------------------------------------
        # Summary
        # -------------------------------------------------------------

        if section == ResumeSection.SUMMARY:

            return content

        # -------------------------------------------------------------
        # Project
        # -------------------------------------------------------------

        if section == ResumeSection.PROJECTS:

            return cls._normalize_project_content(
                content
            )

        # -------------------------------------------------------------
        # Other list-based sections
        # -------------------------------------------------------------

        if section in {
            ResumeSection.EXPERIENCE,
            ResumeSection.SKILLS,
            ResumeSection.EDUCATION,
            ResumeSection.CERTIFICATIONS,
        }:

            if not isinstance(
                content,
                list,
            ):
                return content

            return [
                cls._decode_json_value(
                    item
                )
                for item in content
            ]

        return content

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_optimized_content(
        self,
        section: ResumeSection,
        optimized_content_json: Any,
    ) -> tuple[Any, list[str]]:
        """
        Decode, normalize and validate Gemini's section output.
        """

        if not optimized_content_json:

            return (
                None,
                [
                    f"{section.value}: "
                    "LLM returned empty "
                    "optimized_content_json."
                ],
            )

        try:

            parsed_content = (
                self._parse_optimized_json(
                    optimized_content_json
                )
            )

        except ValueError as exc:

            return (
                None,
                [
                    f"{section.value}: {exc}"
                ],
            )

        normalized_content = (
            self._normalize_section_content(
                section=section,
                content=parsed_content,
            )
        )

        return self._validate_content(
            section=section,
            content=normalized_content,
        )

    def _validate_content(
        self,
        section: ResumeSection,
        content: Any,
    ) -> tuple[Any, list[str]]:
        """
        Validate a section against its canonical Pydantic type.
        """

        adapter = (
            SECTION_TYPE_ADAPTERS.get(
                section
            )
        )

        if adapter is None:

            return (
                None,
                [
                    f"{section.value}: "
                    "No validation adapter exists."
                ],
            )

        try:

            validated = (
                adapter.validate_python(
                    content
                )
            )

            return (
                validated,
                [],
            )

        except ValidationError as exc:

            errors: list[str] = []

            for error in exc.errors():

                location_parts = [
                    str(part)
                    for part in error["loc"]
                ]

                location = ".".join(
                    location_parts
                )

                if location:

                    error_location = (
                        f"{section.value}."
                        f"{location}"
                    )

                else:

                    error_location = (
                        section.value
                    )

                errors.append(
                    f"{error_location}: "
                    f"{error['msg']}"
                )

            return (
                None,
                errors,
            )

    # =================================================================
    # APPLY
    # =================================================================

    def _apply_section_result(
        self,
        resume_ast: ResumeAST,
        result: SectionOptimizationResult,
    ) -> None:

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

        raise ValueError(
            f"Unsupported resume section: {section}"
        )

    # =================================================================
    # GUIDELINES
    # =================================================================

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
            and (
                not guideline.applies_to
                or section in guideline.applies_to
            )
        ]

    def _default_guidelines(
        self,
    ) -> list[OptimizationGuideline]:

        return [

            OptimizationGuideline(
                id="active_voice",
                description=(
                    "Use active, precise action verbs where "
                    "this accurately reflects the original "
                    "content."
                ),
                applies_to=[
                    ResumeSection.SUMMARY,
                    ResumeSection.EXPERIENCE,
                    ResumeSection.PROJECTS,
                ],
            ),

            OptimizationGuideline(
                id="concise_language",
                description=(
                    "Remove filler, repetition and unnecessary "
                    "words without removing meaningful facts."
                ),
            ),

            OptimizationGuideline(
                id="achievement_framing",
                description=(
                    "Transform responsibility-oriented language "
                    "into achievement-oriented language when "
                    "the underlying source supports doing so."
                ),
                applies_to=[
                    ResumeSection.SUMMARY,
                    ResumeSection.EXPERIENCE,
                    ResumeSection.PROJECTS,
                ],
            ),

            OptimizationGuideline(
                id="preserve_evidence",
                description=(
                    "Preserve explicit metrics, scale, durations, "
                    "numbers, outcomes, awards, patents and other "
                    "evidence."
                ),
            ),

            OptimizationGuideline(
                id="use_evidence",
                description=(
                    "Make existing evidence more visible and "
                    "prominent when doing so does not change "
                    "its meaning."
                ),
                applies_to=[
                    ResumeSection.SUMMARY,
                    ResumeSection.EXPERIENCE,
                    ResumeSection.PROJECTS,
                ],
            ),

            OptimizationGuideline(
                id="preserve_technical_terms",
                description=(
                    "Preserve meaningful technologies, tools, "
                    "frameworks, platforms, programming languages "
                    "and domain terminology."
                ),
            ),

            OptimizationGuideline(
                id="ats_terminology",
                description=(
                    "Normalize technology and professional "
                    "terminology to common ATS-recognizable "
                    "spellings without adding new technologies."
                ),
            ),

            OptimizationGuideline(
                id="skill_grouping",
                description=(
                    "Group skills into meaningful categories and "
                    "normalize capitalization without adding "
                    "skills."
                ),
                applies_to=[
                    ResumeSection.SKILLS
                ],
            ),

            OptimizationGuideline(
                id="reduce_redundancy",
                description=(
                    "Remove repeated wording while preserving "
                    "distinct evidence and technologies."
                ),
            ),

            OptimizationGuideline(
                id="no_new_facts",
                description=(
                    "Do not introduce technologies, skills, "
                    "metrics, responsibilities, outcomes, "
                    "companies, titles, dates, certifications, "
                    "education or unsupported claims."
                ),
            ),

            OptimizationGuideline(
                id="preserve_structure",
                description=(
                    "Do not add, remove, merge or split records "
                    "during general ATS optimization."
                ),
            ),

            OptimizationGuideline(
                id="preserve_provenance",
                description=(
                    "Do not modify source_text or evidence. "
                    "Original provenance must remain attached "
                    "to optimized content."
                ),
            ),
        ]

    # =================================================================
    # SERIALIZATION
    # =================================================================

    def _serialize_ast(
        self,
        resume_ast: ResumeAST,
    ) -> dict[str, Any]:

        return resume_ast.model_dump(
            mode="json"
        )

    # =================================================================
    # ERROR RESULT
    # =================================================================

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
            findings=[],
            changes=[],
            validation_passed=False,
            validation_errors=[error],
        )
