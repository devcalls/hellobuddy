from __future__ import annotations

from typing import Any

from app.integration.ai.llm import (
    LLMService,
    LLMServiceFactory,
)
from app.config.resume_settings import ResumeSettings
from app.models.resume.optimization import (
    OptimizationGuideline,
    OptimizationMode,
    ResumeSection,
    SectionOptimizationResult,
)
from app.prompts.resume.optimization import (
    ATS_OPTIMIZATION_SYSTEM_PROMPT,
    build_section_optimization_user_prompt,
)


class SectionOptimizer:
    """
    Optimizes a single ResumeAST section using the LLM.

    The optimizer does not modify ResumeAST directly. It returns a
    SectionOptimizationResult which is subsequently validated and
    applied by the resume optimization service.
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

    def optimize(
        self,
        section: ResumeSection,
        content: Any,
        guidelines: list[OptimizationGuideline],
        mode: OptimizationMode,
    ) -> SectionOptimizationResult:

        user_prompt = build_section_optimization_user_prompt(
            section=section,
            content=content,
            guidelines=guidelines,
            mode=mode,
        )

        return self.llm_service.generate_structured(
            system_prompt=ATS_OPTIMIZATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=SectionOptimizationResult,
        )
