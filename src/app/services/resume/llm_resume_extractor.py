"""
LLM-based resume extraction service.

Responsibilities:
    1. Accept raw resume text.
    2. Send the text to the configured LLM.
    3. Request structured ResumeExtraction output.
    4. Return the validated ResumeExtraction.

This service does NOT:
    - perform ATS scoring
    - optimize the resume
    - rewrite resume content
    - calculate ATS keywords
    - calculate numeric extraction confidence

Those concerns belong to separate services.

Provider-specific behavior is intentionally hidden behind LLMService.
"""

from __future__ import annotations

from app.config.resume_settings import ResumeSettings
from app.integration.ai.llm import (
    LLMService,

)
from app.integration.ai.factory import LLMServiceFactory
from app.models.resume.resume_extraction import ResumeExtraction
from app.prompts.resume.extraction_prompt import (
    RESUME_EXTRACTION_SYSTEM_PROMPT,
)


class LLMResumeExtractor:
    """
    Extracts resume information into the application-level
    ResumeExtraction model using a provider-neutral LLM service.

    The extractor does not know whether the underlying LLM is
    Gemini, OpenAI, Anthropic, or another provider.
    """

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
        """
        Extract structured resume information from raw resume text.

        Args:
            resume_text:
                Text extracted from the original PDF/DOCX.

        Returns:
            A validated ResumeExtraction.

        Raises:
            ValueError:
                If the supplied resume text is empty or contains
                only whitespace.
        """

        self._validate_resume_text(resume_text)

        user_prompt = self._build_user_prompt(
            resume_text
        )

        return self.llm_service.generate_structured(
            system_prompt=RESUME_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ResumeExtraction,
        )

    @staticmethod
    def _validate_resume_text(
        resume_text: str,
    ) -> None:
        """
        Validate the raw resume text before sending it to the LLM.
        """

        if not resume_text or not resume_text.strip():
            raise ValueError(
                "Cannot extract resume information because "
                "the supplied resume text is empty."
            )

    @staticmethod
    def _build_user_prompt(
        resume_text: str,
    ) -> str:
        """
        Build the provider-neutral extraction prompt.

        Provider-specific formatting, schema handling, and API
        behavior belong to the LLM provider adapter.
        """

        return f"""
Extract the resume information from the text below.

Rules:

1. Extract only information explicitly supported by the resume.
2. Do not invent missing information.
3. Preserve dates as written where possible.
4. Preserve achievement bullets faithfully.
5. Do not infer skills, technologies, responsibilities, or
   achievements that are not explicitly supported.
6. If a section does not exist, return an empty list.
7. If a value is not available, return null.
8. Preserve source text/evidence fields where required by the
   ResumeExtraction schema.
9. Preserve the relationship between resume sections and records.
10. Do not optimize, rewrite, summarize, or improve the resume.
11. Extraction and optimization are separate operations.

RESUME
======

{resume_text}
""".strip()