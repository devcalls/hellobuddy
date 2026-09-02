"""
LLM-based resume extraction service.

Responsibilities:
    1. Accept raw resume text.
    2. Send the text to the LLM.
    3. Request structured ResumeAST output.
    4. Return a validated ResumeAST.

This service does NOT:
    - perform ATS scoring
    - optimize the resume
    - rewrite resume content
    - calculate ATS keywords
    - calculate numeric extraction confidence

Those concerns belong to separate services.
"""

from app.config.resume_settings import ResumeSettings
from app.models.resume.resume_ast import ResumeAST
from app.models.resume.resume_extraction import ResumeExtraction
from app.prompts.resume.extraction_prompt import (
    RESUME_EXTRACTION_SYSTEM_PROMPT,
)
from app.config.llm import LLMProvider
from app.integration.ai.llm import (
    LLMService,
    LLMServiceFactory,
)


class LLMResumeExtractor:
    """
    Extracts a resume into the canonical ResumeAST
    using an LLM structured output.
    """

    def __init__(
        self,
        settings: ResumeSettings,
        llm_service: LLMService | None = None,
    ) -> None:

        self.settings = settings
        if llm_service:

            self.llm_service = llm_service

        else:

            self.llm_service = LLMServiceFactory.create(settings=settings.llm)

    def extract(
        self,
        resume_text: str,
    ) -> ResumeExtraction:
        """
        Extract structured ResumeExtraction from raw resume text.

        Args:
            resume_text:
                Text extracted from the original PDF/DOCX.

        Returns:
            A validated ResumeExtraction.

        Raises:
            ValueError:
                If the supplied resume text is empty or the
                LLM does not return structured output.
        """

        if not resume_text or not resume_text.strip():

            raise ValueError(
                "Cannot extract resume information because "
                "the supplied resume text is empty."
            )

        user_prompt = self._build_user_prompt(resume_text)

        return self.llm_service.generate_structured(
            system_prompt=(RESUME_EXTRACTION_SYSTEM_PROMPT),
            user_prompt=user_prompt,
            response_model=ResumeExtraction,
        )

    @staticmethod
    def _build_user_prompt(
        resume_text: str,
    ) -> str:
        """
        Build the extraction request sent to the LLM.
        """

        return f"""
Extract the resume information from the text below.

Rules:

1. Extract only information explicitly supported by the resume.
2. Do not invent missing information.
3. Preserve dates as written where possible.
4. Preserve achievement bullets faithfully.
5. Do not infer skills that are not present.
6. If a section does not exist, return an empty list.
7. If a value is not available, return null.

RESUME
======

{resume_text}
""".strip()
