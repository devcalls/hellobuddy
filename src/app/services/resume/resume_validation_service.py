"""
Semantic validation of the canonical ResumeAST.

Pydantic validates shape. This service validates resume-specific
invariants that matter to downstream ATS analysis and optimization.
"""

from __future__ import annotations

import re
from collections import Counter

from app.models.resume.resume_ast import ResumeAST


class ResumeValidationService:

    def validate(
        self,
        resume: ResumeAST,
    ) -> ResumeAST:

        errors = self.collect_errors(resume)

        if errors:
            raise ValueError(
                "ResumeAST validation failed:\n"
                + "\n".join(
                    f"- {error}"
                    for error in errors
                )
            )

        return resume

    def collect_errors(
        self,
        resume: ResumeAST,
    ) -> list[str]:

        errors: list[str] = []

        errors.extend(
            self._validate_ids(resume)
        )

        errors.extend(
            self._validate_experience(resume)
        )

        errors.extend(
            self._validate_contact(resume)
        )

        errors.extend(
            self._validate_dates(resume)
        )

        errors.extend(
            self._validate_projects(resume)
        )

        errors.extend(
            self._validate_source_text(resume)
        )

        return errors

    # ------------------------------------------------------------------
    # IDs
    # ------------------------------------------------------------------

    def _validate_ids(
        self,
        resume: ResumeAST,
    ) -> list[str]:

        ids: list[str] = []

        for experience in resume.experience:
            ids.append(experience.id)

            for achievement in experience.achievements:
                ids.append(achievement.id)

        for project in resume.projects:
            ids.append(project.id)

            for achievement in project.achievements:
                ids.append(achievement.id)

        ids.extend(
            skill.id
            for skill in resume.skills
        )

        ids.extend(
            education.id
            for education in resume.education
        )

        ids.extend(
            certification.id
            for certification in resume.certifications
        )

        errors: list[str] = []

        duplicates = [
            value
            for value, count in Counter(ids).items()
            if count > 1
        ]

        if duplicates:
            errors.append(
                "Duplicate IDs: "
                + ", ".join(sorted(duplicates))
            )

        prefix_groups = {
            "experience_": [
                e.id for e in resume.experience
            ],
            "project_": [
                p.id for p in resume.projects
            ],
            "skill_": [
                s.id for s in resume.skills
            ],
            "education_": [
                e.id for e in resume.education
            ],
            "certification_": [
                c.id for c in resume.certifications
            ],
        }

        for prefix, values in prefix_groups.items():
            for value in values:
                if not value.startswith(prefix):
                    errors.append(
                        f"ID '{value}' must start with '{prefix}'."
                    )

        for achievement_id in [
            achievement.id
            for experience in resume.experience
            for achievement in experience.achievements
        ] + [
            achievement.id
            for project in resume.projects
            for achievement in project.achievements
        ]:
            if not achievement_id.startswith(
                "achievement_"
            ):
                errors.append(
                    f"Achievement ID '{achievement_id}' "
                    "must start with 'achievement_'."
                )

        return errors

    # ------------------------------------------------------------------
    # EXPERIENCE
    # ------------------------------------------------------------------

    def _validate_experience(
        self,
        resume: ResumeAST,
    ) -> list[str]:

        errors: list[str] = []

        for experience in resume.experience:

            if not experience.company.strip():
                errors.append(
                    "Experience contains an empty company name."
                )

            if not experience.title.strip():
                errors.append(
                    "Experience contains an empty title."
                )

        return errors

    # ------------------------------------------------------------------
    # CONTACT
    # ------------------------------------------------------------------

    def _validate_contact(
        self,
        resume: ResumeAST,
    ) -> list[str]:

        errors: list[str] = []

        source = resume.source_text or ""

        if re.search(
            r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
            source,
        ):
            if not resume.contact.email:
                errors.append(
                    "An email address exists in source_text, "
                    "but contact.email is empty."
                )

        if re.search(
            r"(?:ph|phone|mobile|tel)\s*[:.]",
            source,
            re.IGNORECASE,
        ):
            if not resume.contact.phone:
                errors.append(
                    "Phone information exists in source_text, "
                    "but contact.phone is empty."
                )

        return errors

    # ------------------------------------------------------------------
    # DATES
    # ------------------------------------------------------------------

    def _validate_dates(
        self,
        resume: ResumeAST,
    ) -> list[str]:

        errors: list[str] = []

        current_markers = (
            "till date",
            "till present",
            "to date",
            "to present",
            "present",
            "current",
            "ongoing",
        )

        for experience in resume.experience:

            date_range = experience.date_range
            source = (
                date_range.source_text or ""
            ).lower()

            if source and date_range.start_date is None:
                errors.append(
                    f"Experience '{experience.company}' has "
                    "date source text but no normalized start_date."
                )

            if any(
                marker in source
                for marker in current_markers
            ):
                if not date_range.current:
                    errors.append(
                        f"Experience '{experience.company}' contains "
                        "a current marker but current=false."
                    )

                if date_range.end_date is not None:
                    errors.append(
                        f"Experience '{experience.company}' is current "
                        "but end_date is not null."
                    )

        return errors

    # ------------------------------------------------------------------
    # PROJECTS / RELATIONSHIPS
    # ------------------------------------------------------------------

    def _validate_projects(
        self,
        resume: ResumeAST,
    ) -> list[str]:

        errors: list[str] = []

        projects_by_id = {
            project.id: project
            for project in resume.projects
        }

        for experience in resume.experience:

            for project_id in experience.project_ids:

                if project_id not in projects_by_id:
                    errors.append(
                        f"Experience '{experience.company}' references "
                        f"unknown project ID '{project_id}'."
                    )

        return errors

    # ------------------------------------------------------------------
    # PROVENANCE
    # ------------------------------------------------------------------

    def _validate_source_text(
        self,
        resume: ResumeAST,
    ) -> list[str]:

        errors: list[str] = []

        for experience in resume.experience:

            if not experience.source_text:
                errors.append(
                    f"Experience '{experience.company}' has no source_text."
                )

            for achievement in experience.achievements:

                if not achievement.source_text:
                    errors.append(
                        f"Achievement '{achievement.id}' under "
                        f"'{experience.company}' has no source_text."
                    )

        for project in resume.projects:

            if project.description or project.achievements:

                if not project.source_text:
                    errors.append(
                        f"Project '{project.name}' has content "
                        "but no source_text."
                    )

            for achievement in project.achievements:

                if not achievement.source_text:
                    errors.append(
                        f"Achievement '{achievement.id}' under project "
                        f"'{project.name}' has no source_text."
                    )

        return errors
