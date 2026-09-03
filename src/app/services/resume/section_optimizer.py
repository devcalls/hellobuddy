from __future__ import annotations

from typing import Any

from app.config.resume_settings import ResumeSettings
from app.integration.ai.llm import (
    LLMService,
    LLMServiceFactory,
)
from app.models.resume.optimization import (
    OptimizationGuideline,
    OptimizationMode,
    ResumeSection,
    SectionOptimizationLLMResult,
)
from app.prompts.resume.optimization import (
    ATS_OPTIMIZATION_SYSTEM_PROMPT,
    build_section_optimization_user_prompt,
)


class SectionOptimizer:
    """
    Performs LLM optimization of one ResumeAST section.

    This class intentionally does not mutate the ResumeAST.

    It is responsible only for:

        Resume section
             ↓
        optimization prompt
             ↓
        LLM
             ↓
        SectionOptimizationLLMResult
    """

    def __init__(
        self,
        settings: ResumeSettings,
        llm_service: LLMService | None = None,
    ) -> None:

        self.settings = settings

        if llm_service is not None:
            self.llm_service = llm_service
        else:
            self.llm_service = (
                LLMServiceFactory.create(
                    settings=settings.llm
                )
            )

    def optimize(
        self,
        section: ResumeSection,
        content: Any,
        guidelines: list[OptimizationGuideline],
        mode: OptimizationMode,
    ) -> SectionOptimizationLLMResult:

        user_prompt = (
            build_section_optimization_user_prompt(
                section=section,
                content=content,
                guidelines=guidelines,
                mode=mode,
            )
        )

        result = self.llm_service.generate_structured(
            system_prompt=ATS_OPTIMIZATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=SectionOptimizationLLMResult,
        )

        # The LLM must not be allowed to claim it optimized
        # one section while returning another.
        if result.section != section:
            raise ValueError(
                "LLM returned section "
                f"'{result.section.value}' while "
                f"'{section.value}' was requested."
            )

        return result