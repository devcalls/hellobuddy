
from typing import Optional
from datetime import date

from app.models.resume.resume_ast import (
    ResumeAST,
    Experience,
    Achievement,
    Education,
    Skill,
    Certification,
    Project,
    DateRange,
    ExtractionEvidence,
    ResumeMetadata,
)

from app.models.resume.resume_extraction import (
    ResumeExtraction,
)


class ResumeASTBuilder:
    """
    Converts LLM ResumeExtraction into the canonical
    application ResumeAST.

    This is application-owned logic and does not depend
    on Gemini/OpenAI.
    """

    def build(
        self,
        extraction: ResumeExtraction,
        source_text: str,
        source_file: Optional[str] = None,
        source_format: Optional[str] = None,
    ) -> ResumeAST:

        return ResumeAST(
            source_text=source_text,

            metadata=self._build_metadata(
                source_file=source_file,
                source_format=source_format,
            ),

            summary=extraction.summary,

            experience=[
                self._build_experience(
                    item
                )
                for item in extraction.experiences
            ],

            education=[
                self._build_education(
                    item
                )
                for item in extraction.education
            ],

            skills=[
                Skill(
                    name=item.name,
                    category=item.category,
                )
                for item in extraction.skills
            ],

            certifications=[
                Certification(
                    name=item.name,
                    issuer=item.issuer,
                    date=item.date,
                    credential_id=item.credential_id,
                    credential_url=item.credential_url,
                )
                for item in extraction.certifications
            ],

            projects=[
                self._build_project(
                    item
                )
                for item in extraction.projects
            ],
        )
        

    @staticmethod
    def _build_date_range(
        start_date: str | None,
        end_date: str | None,
    ) -> DateRange | None:

        # Don't create an empty DateRange.
        if not start_date and not end_date:
            return None

        return DateRange(
            start_date=start_date,
            end_date=end_date,
        )

    @staticmethod
    def _build_experience(
        item,
    ) -> Experience:

        date_range = ResumeASTBuilder._build_date_range(
            start_date=item.start_date,
            end_date=item.end_date,
        )

        return Experience(
            company=item.company,
            title=item.job_title,
            location=item.location,
            date_range=date_range,

            achievements=[
                Achievement(
                    text=achievement.text
                )
                for achievement in item.achievements
            ],
        )

   

    @staticmethod
    def _parse_date(
        value: Optional[str],
    ) -> Optional[date]:
        """
        Convert an LLM-extracted date string into datetime.date.

        The LLM is instructed to return ISO dates where possible,
        but resumes can contain less precise dates.

        We therefore deliberately fail soft here.
        """

        if not value:
            return None

        value = value.strip()

        # -----------------------------------------
        # ISO date
        # -----------------------------------------

        try:
            return date.fromisoformat(value)
        except ValueError:
            pass

        # -----------------------------------------
        # Year only
        #
        # Example:
        #     "2021"
        #
        # We normalize this to January 1st.
        # The original value is still preserved in
        # DateRange.source_text.
        # -----------------------------------------

        if (
            len(value) == 4
            and value.isdigit()
        ):
            try:
                return date(
                    int(value),
                    1,
                    1,
                )
            except ValueError:
                pass

        # -----------------------------------------
        # Unknown / non-normalizable date
        #
        # Examples:
        #     "Present"
        #     "Current"
        #     "Jan 2021"
        #
        # Don't guess.
        # -----------------------------------------

        return None

    @staticmethod
    def _build_metadata(
        source_file: Optional[str],
        source_format: Optional[str],
    ) -> ResumeMetadata:

        return ResumeMetadata(
            source_file=source_file,
            source_format=source_format,
        )

    @staticmethod
    def _build_experience(
        item,
    ) -> Experience:

        date_range = None

        if item.start_date or item.end_date:

             date_range = ResumeASTBuilder._build_date_range(
                start_date=item.start_date,
                end_date=item.end_date,
            )

        return Experience(
            company=item.company,
            title=item.job_title,
            location=item.location,
            date_range=date_range,

            achievements=[
                Achievement(
                    text=achievement.text
                )
                for achievement
                in item.achievements
            ],
        )

    @staticmethod
    def _build_education(
        item,
    ) -> Education:

        date_range = None

        if item.start_date or item.end_date:

             date_range = ResumeASTBuilder._build_date_range(
                start_date=item.start_date,
                end_date=item.end_date,
            )

        return Education(
            institution=item.institution,
            degree=item.degree,
            field_of_study=item.field_of_study,
            date_range=date_range,
        )

    @staticmethod
    def _build_project(
        item,
    ) -> Project:

        return Project(
            name=item.name,
            description=item.description,
            technologies=item.technologies,

            achievements=[
                Achievement(
                    text=achievement.text
                )
                for achievement
                in item.achievements
            ],
        )
        
    @staticmethod
    def _build_date_range(
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> Optional[DateRange]:

        if not start_date and not end_date:
            return None

        normalized_start = (
            ResumeASTBuilder._parse_date(
                start_date
            )
        )

        normalized_end = (
            ResumeASTBuilder._parse_date(
                end_date
            )
        )

        # -----------------------------------------
        # Determine whether the role is current.
        # -----------------------------------------

        current = False

        if end_date:

            current = (
                end_date.strip().lower()
                in {
                    "present",
                    "current",
                    "ongoing",
                    "now",
                }
            )

        # -----------------------------------------
        # Preserve exactly what the LLM extracted.
        # -----------------------------------------

        source_parts = []

        if start_date:
            source_parts.append(
                start_date
            )

        if end_date:
            source_parts.append(
                end_date
            )

        source_text = " - ".join(
            source_parts
        ) if source_parts else None

        # -----------------------------------------
        # Build canonical DateRange
        # -----------------------------------------

        return DateRange(
            start_date=normalized_start,
            end_date=normalized_end,
            current=current,
            source_text=source_text,
        )

