from __future__ import annotations

from typing import Iterable

from app.models.resume.resume_ast import (
    ExtractionEvidence,
    ResumeAST,
)
from app.models.resume.confidence import (
    ConfidenceLevel,
    ConfidenceScore,
)


class ResumeConfidenceService:
    """
    Deterministic confidence calculation.

    The LLM supplies qualitative evidence quality.
    The application derives numeric confidence.
    """

    EVIDENCE_WEIGHT = 0.50
    COMPLETENESS_WEIGHT = 0.30
    NORMALIZATION_WEIGHT = 0.20

    def calculate(
        self,
        resume: ResumeAST,
    ) -> ConfidenceScore:

        evidence_score = (
            self._calculate_evidence_score(resume)
        )

        completeness_score = (
            self._calculate_completeness_score(resume)
        )

        normalization_score = (
            self._calculate_normalization_score(resume)
        )

        score = (
            evidence_score * self.EVIDENCE_WEIGHT
            + completeness_score * self.COMPLETENESS_WEIGHT
            + normalization_score * self.NORMALIZATION_WEIGHT
        )

        score = round(
            max(0.0, min(100.0, score)),
            2,
        )

        return ConfidenceScore(
            score=score,
            level=self._get_level(score),
            evidence_score=round(
                evidence_score,
                2,
            ),
            completeness_score=round(
                completeness_score,
                2,
            ),
            normalization_score=round(
                normalization_score,
                2,
            ),
        )

    def _calculate_evidence_score(
        self,
        resume: ResumeAST,
    ) -> float:

        evidences = list(
            self._collect_evidence(resume)
        )

        if not evidences:
            return 0.0

        average = (
            sum(
                evidence.confidence
                for evidence in evidences
            )
            / len(evidences)
        )

        coverage = min(
            len(evidences) / 20.0,
            1.0,
        )

        return min(
            100.0,
            average * 80.0 + coverage * 20.0,
        )

    def _calculate_completeness_score(
        self,
        resume: ResumeAST,
    ) -> float:

        checks = [
            bool(resume.metadata.source_file),
            bool(
                resume.contact.name
                or resume.contact.email
                or resume.contact.phone
            ),
            bool(resume.summary),
            bool(resume.experience),
            bool(resume.skills),
            bool(resume.education),
            bool(resume.certifications),
            bool(resume.projects),
        ]

        return (
            sum(checks)
            / len(checks)
            * 100.0
        )

    def _calculate_normalization_score(
        self,
        resume: ResumeAST,
    ) -> float:

        checks: list[bool] = []

        for experience in resume.experience:

            date_range = experience.date_range

            if date_range.source_text:

                checks.append(
                    date_range.start_date is not None
                )

                if date_range.current:
                    checks.append(
                        date_range.end_date is None
                    )
                elif date_range.end_date is not None:
                    checks.append(True)

        for education in resume.education:

            date_range = education.date_range

            if date_range.source_text:

                # Education may legitimately have only a completion year.
                checks.append(
                    date_range.end_date is not None
                    or date_range.start_date is not None
                )

        if not checks:
            return 100.0

        return (
            sum(checks)
            / len(checks)
            * 100.0
        )

    def _collect_evidence(
        self,
        resume: ResumeAST,
    ) -> Iterable[ExtractionEvidence]:

        yield from resume.contact.evidence

        for experience in resume.experience:

            yield from experience.evidence
            yield from experience.date_range.evidence

            for achievement in experience.achievements:
                yield from achievement.evidence

        for skill in resume.skills:
            yield from skill.evidence

        for education in resume.education:

            yield from education.evidence
            yield from education.date_range.evidence

        for certification in resume.certifications:
            yield from certification.evidence

        for project in resume.projects:

            yield from project.evidence

            for achievement in project.achievements:
                yield from achievement.evidence

    @staticmethod
    def _get_level(
        score: float,
    ) -> ConfidenceLevel:

        if score >= 90:
            return ConfidenceLevel.HIGH

        if score >= 75:
            return ConfidenceLevel.GOOD

        if score >= 50:
            return ConfidenceLevel.MEDIUM

        if score >= 25:
            return ConfidenceLevel.LOW

        return ConfidenceLevel.VERY_LOW
