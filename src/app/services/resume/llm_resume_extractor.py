"""
LLM-based semantic resume extraction.
"""

from __future__ import annotations

from app.config.resume_settings import ResumeSettings
from app.integration.ai.llm import LLMService
from app.integration.ai.factory import LLMServiceFactory
from app.models.resume.resume_extraction import ResumeExtraction
from app.prompts.resume.extraction_prompt import (
    RESUME_EXTRACTION_SYSTEM_PROMPT,
)


class LLMResumeExtractor:

    def __init__(
        self,
        settings: ResumeSettings,
        llm_service: LLMService | None = None,
    ) -> None:

        self.settings = settings
        self.llm_service = (
            llm_service
            if llm_service is not None
            else LLMServiceFactory.create(
                settings=settings.llm,
            )
        )

    def extract(
        self,
        resume_text: str,
    ) -> ResumeExtraction:

        self._validate_resume_text(resume_text)

        return self.llm_service.generate_structured(
            system_prompt=RESUME_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=self._build_user_prompt(
                resume_text
            ),
            response_model=ResumeExtraction,
        )

    @staticmethod
    def _validate_resume_text(
        resume_text: str,
    ) -> None:

        if not resume_text or not resume_text.strip():
            raise ValueError(
                "Cannot extract resume information because "
                "the supplied resume text is empty."
            )

    @staticmethod
    def _build_user_prompt(
        resume_text: str,
    ) -> str:

        return f"""
Extract the resume into the ResumeExtraction schema.

Before extracting the rest of the document, inspect the header for
contact information.

Then identify section boundaries and preserve the hierarchy between
employers, projects, and achievements.

Pay particular attention to:
- all employment dates
- "Till Date", "Present", "Current", and "Ongoing"
- projects nested under employers
- achievement/responsibility bullets
- explicitly named technologies
- source_text and evidence

Do not optimize or rewrite content.

SOURCE RESUME
=============

{resume_text}
""".strip()
