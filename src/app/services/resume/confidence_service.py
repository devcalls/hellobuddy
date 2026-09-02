from __future__ import annotations

from enum import Enum
from typing import Iterable

from pydantic import BaseModel, Field

from app.models.resume.resume_ast import (
    ResumeAST,
    ExtractionEvidence,
)
from app.models.resume.confidence import ConfidenceScore, ConfidenceLevel


class ResumeConfidenceService:
    """
    Calculates extraction confidence for a ResumeAST.

    The score is deterministic.

    Gemini does NOT determine the final score.
    """

    # Weights should sum to 1.0
    EVIDENCE_WEIGHT = 0.50
    COMPLETENESS_WEIGHT = 0.30
    NORMALIZATION_WEIGHT = 0.20

    def calculate(
        self,
        resume: ResumeAST,
    ) -> ConfidenceScore:

        evidence_score = self._calculate_evidence_score(resume)

        completeness_score = self._calculate_completeness_score(resume)

        normalization_score = self._calculate_normalization_score(resume)

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

    # ---------------------------------------------------------
    # Evidence
    # ---------------------------------------------------------

    def _calculate_evidence_score(
        self,
        resume: ResumeAST,
    ) -> float:

        evidences = list(self._collect_evidence(resume))

        if not evidences:
            return 0.0

        confidence_values = [
            evidence.confidence
            for evidence in evidences
            if evidence.confidence is not None
        ]

        if not confidence_values:
            return 0.0

        average = sum(confidence_values) / len(confidence_values)

        # Evidence coverage bonus.
        #
        # More supported facts means more confidence
        # in the extraction as a whole.

        coverage = min(
            len(evidences) / 10.0,
            1.0,
        )

        score = average * 80.0 + coverage * 20.0

        return min(
            100.0,
            score,
        )

    # ---------------------------------------------------------
    # Completeness
    # ---------------------------------------------------------

    def _calculate_completeness_score(
        self,
        resume: ResumeAST,
    ) -> float:

        checks = [
            bool(resume.metadata),
            bool(resume.contact),
            bool(resume.summary),
            bool(resume.experience),
            bool(resume.skills),
            bool(resume.education),
            bool(resume.certifications),
            bool(resume.projects),
        ]

        if not checks:
            return 0.0

        return (sum(checks) / len(checks)) * 100.0

    # ---------------------------------------------------------
    # Normalization
    # ---------------------------------------------------------

    def _calculate_normalization_score(
        self,
        resume: ResumeAST,
    ) -> float:

        checks: list[bool] = []

        for experience in resume.experience:

            if experience.date_range:

                # A date that successfully normalized
                # contributes positively.

                if experience.date_range.start_date:
                    checks.append(True)

                if experience.date_range.end_date or experience.date_range.current:
                    checks.append(True)

        for education in resume.education:

            if education.date_range:

                if education.date_range.start_date:
                    checks.append(True)

                if education.date_range.end_date or education.date_range.current:
                    checks.append(True)

        if not checks:
            # No dates to normalize.
            #
            # Don't penalize a resume simply because
            # it doesn't contain date information.

            return 100.0

        return (sum(checks) / len(checks)) * 100.0

    # ---------------------------------------------------------
    # Evidence collection
    # ---------------------------------------------------------

    def _collect_evidence(
        self,
        resume: ResumeAST,
    ) -> Iterable[ExtractionEvidence]:

        for experience in resume.experience:

            if experience.date_range:
                yield from (experience.date_range.evidence)

            for achievement in experience.achievements:
                yield from achievement.evidence

        for skill in resume.skills:
            yield from skill.evidence

        for education in resume.education:

            if education.date_range:
                yield from (education.date_range.evidence)

        for certification in resume.certifications:
            yield from certification.evidence

        for project in resume.projects:
            yield from project.evidence

    # ---------------------------------------------------------
    # Level
    # ---------------------------------------------------------

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
