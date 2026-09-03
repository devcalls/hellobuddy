"""
Build the canonical ResumeAST from the LLM extraction model.

Application-owned responsibilities:
- canonical IDs
- date normalization
- provenance conversion
- experience/project relationship resolution
- deterministic structural validation
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Iterable

from app.models.resume.resume_ast import (
    Achievement,
    Certification,
    ContactInformation,
    DateRange,
    Education,
    Experience,
    ExtractionEvidence,
    Project,
    ResumeAST,
    ResumeMetadata,
    Skill,
)
from app.models.resume.resume_extraction import (
    ExtractedAchievement,
    ExtractedCertification,
    ExtractedContactInformation,
    ExtractedDateRange,
    ExtractedEducation,
    ExtractedEvidence,
    ExtractedExperience,
    ExtractedProject,
    ExtractedSkill,
    ResumeExtraction,
)
from uuid import uuid4


def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class ResumeASTBuilder:

    PARSER_VERSION = "3.0-llm"

    def build(
        self,
        extraction: ResumeExtraction,
        source_text: str,
        source_file: str | None = None,
        source_format: str | None = None,
    ) -> ResumeAST:

        projects = [
            self._build_project(project)
            for project in extraction.projects
        ]

        project_lookup = self._build_project_lookup(projects)

        experiences = [
            self._build_experience(
                item,
                project_lookup=project_lookup,
            )
            for item in extraction.experience
        ]

        resume = ResumeAST(
            metadata=ResumeMetadata(
                source_file=source_file,
                source_format=source_format,
                parser_version=self.PARSER_VERSION,
                raw_text=source_text,
            ),
            contact=self._build_contact(
                extraction.contact
            ),
            summary=extraction.summary,
            experience=experiences,
            skills=[
                self._build_skill(item)
                for item in extraction.skills
            ],
            education=[
                self._build_education(item)
                for item in extraction.education
            ],
            certifications=[
                self._build_certification(item)
                for item in extraction.certifications
            ],
            projects=projects,
            source_text=source_text,
        )

        self._validate_relationships(resume)

        return resume

    # ------------------------------------------------------------------
    # CONTACT
    # ------------------------------------------------------------------

    def _build_contact(
        self,
        item: ExtractedContactInformation,
    ) -> ContactInformation:

        return ContactInformation(
            name=item.name,
            email=item.email,
            phone=item.phone,
            location=item.location,
            linkedin=item.linkedin,
            github=item.github,
            portfolio=item.portfolio,
            source_text=item.source_text,
            evidence=[
                self._build_evidence(e)
                for e in item.evidence
            ],
        )

    # ------------------------------------------------------------------
    # EXPERIENCE
    # ------------------------------------------------------------------

    def _build_experience(
        self,
        item: ExtractedExperience,
        *,
        project_lookup: dict[str, Project],
    ) -> Experience:

        project_ids: list[str] = []

        for project_name in item.project_names:
            project = self._lookup_project(
                project_name,
                project_lookup,
            )

            if project is not None:
                if project.id not in project_ids:
                    project_ids.append(project.id)

        return Experience(
            id=generate_id("experience"),
            company=item.company,
            title=item.title,
            date_range=self._build_date_range(
                item.date_range
            ),
            location=item.location,
            description=item.description,
            achievements=[
                self._build_achievement(a)
                for a in item.achievements
            ],
            project_ids=project_ids,
            source_text=item.source_text,
            evidence=[
                self._build_evidence(e)
                for e in item.evidence
            ],
        )

    # ------------------------------------------------------------------
    # PROJECT
    # ------------------------------------------------------------------

    def _build_project(
        self,
        item: ExtractedProject,
    ) -> Project:

        return Project(
            id=generate_id("project"),
            name=item.name,
            description=item.description,
            technologies=self._deduplicate(
                item.technologies
            ),
            achievements=[
                self._build_achievement(a)
                for a in item.achievements
            ],
            source_text=item.source_text,
            evidence=[
                self._build_evidence(e)
                for e in item.evidence
            ],
        )

    # ------------------------------------------------------------------
    # ACHIEVEMENT
    # ------------------------------------------------------------------

    def _build_achievement(
        self,
        item: ExtractedAchievement,
    ) -> Achievement:

        return Achievement(
            id=generate_id("achievement"),
            text=item.text,
            action=item.action,
            technologies=self._deduplicate(
                item.technologies
            ),
            skills=self._deduplicate(
                item.skills
            ),
            metrics=self._deduplicate(
                item.metrics
            ),
            impact=item.impact,
            source_text=item.source_text,
            evidence=[
                self._build_evidence(e)
                for e in item.evidence
            ],
        )

    # ------------------------------------------------------------------
    # SKILL
    # ------------------------------------------------------------------

    def _build_skill(
        self,
        item: ExtractedSkill,
    ) -> Skill:

        return Skill(
            id=generate_id("skill"),
            name=item.name,
            category=item.category,
            proficiency=item.proficiency,
            source_text=item.source_text,
            evidence=[
                self._build_evidence(e)
                for e in item.evidence
            ],
        )

    # ------------------------------------------------------------------
    # EDUCATION
    # ------------------------------------------------------------------

    def _build_education(
        self,
        item: ExtractedEducation,
    ) -> Education:

        return Education(
            id=generate_id("education"),
            institution=item.institution,
            degree=item.degree,
            field_of_study=item.field_of_study,
            date_range=self._build_date_range(
                item.date_range
            ),
            location=item.location,
            source_text=item.source_text,
            evidence=[
                self._build_evidence(e)
                for e in item.evidence
            ],
        )

    # ------------------------------------------------------------------
    # CERTIFICATION
    # ------------------------------------------------------------------

    def _build_certification(
        self,
        item: ExtractedCertification,
    ) -> Certification:

        return Certification(
            id=generate_id("certification"),
            name=item.name,
            issuer=item.issuer,
            date=item.date,
            credential_id=item.credential_id,
            credential_url=item.credential_url,
            source_text=item.source_text,
            evidence=[
                self._build_evidence(e)
                for e in item.evidence
            ],
        )

    # ------------------------------------------------------------------
    # DATE
    # ------------------------------------------------------------------

    def _build_date_range(
        self,
        item: ExtractedDateRange,
    ) -> DateRange:

        source_text = item.source_text

        current = item.current
        end_date = item.end_date

        if self._contains_current_marker(source_text):
            current = True
            end_date = None

        if current:
            end_date = None

        return DateRange(
            start_date=item.start_date,
            end_date=end_date,
            current=current,
            source_text=source_text,
            evidence=[
                self._build_evidence(e)
                for e in item.evidence
            ],
        )

    @staticmethod
    def _contains_current_marker(
        source_text: str | None,
    ) -> bool:

        if not source_text:
            return False

        text = source_text.lower().strip()

        markers = (
            "till date",
            "till present",
            "to date",
            "to present",
            "present",
            "current",
            "ongoing",
        )

        return any(marker in text for marker in markers)

    # ------------------------------------------------------------------
    # EVIDENCE
    # ------------------------------------------------------------------

    @staticmethod
    def _build_evidence(
        item: ExtractedEvidence,
    ) -> ExtractionEvidence:

        # LLM supplies qualitative quality.
        # Application derives numeric confidence.
        quality_to_confidence = {
            "high": 1.0,
            "medium": 0.75,
            "low": 0.40,
        }

        return ExtractionEvidence(
            source_text=item.source_text,
            source_section=item.source_section,
            quality=item.quality,
            reason=item.reason,
            confidence=quality_to_confidence.get(
                item.quality,
                0.40,
            ),
            needs_review=item.quality != "high",
            extraction_method="llm",
        )

    # ------------------------------------------------------------------
    # PROJECT RELATIONSHIPS
    # ------------------------------------------------------------------

    @staticmethod
    def _build_project_lookup(
        projects: list[Project],
    ) -> dict[str, Project]:

        return {
            ResumeASTBuilder._normalize_name(project.name): project
            for project in projects
        }

    @staticmethod
    def _lookup_project(
        project_name: str,
        project_lookup: dict[str, Project],
    ) -> Project | None:

        normalized = ResumeASTBuilder._normalize_name(
            project_name
        )

        exact = project_lookup.get(normalized)

        if exact is not None:
            return exact

        # Conservative matching only. The LLM has already established
        # the relationship; this only tolerates harmless formatting
        # differences in the project name.
        for name, project in project_lookup.items():
            if normalized == name:
                return project

        return None

    @staticmethod
    def _validate_relationships(
        resume: ResumeAST,
    ) -> None:

        project_ids = {
            project.id
            for project in resume.projects
        }

        for experience in resume.experience:

            missing = (
                set(experience.project_ids)
                - project_ids
            )

            if missing:
                raise ValueError(
                    f"Experience '{experience.company}' references "
                    f"unknown project IDs: {sorted(missing)}"
                )

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_name(
        value: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            value.strip().lower(),
        )

    @staticmethod
    def _deduplicate(
        values: Iterable[str],
    ) -> list[str]:

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            value = value.strip()

            if not value:
                continue

            key = value.lower()

            if key not in seen:
                seen.add(key)
                result.append(value)

        return result
