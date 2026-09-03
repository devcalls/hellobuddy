from __future__ import annotations

import json
from typing import Any

from app.integration.ai.llm import LLMService
from app.models.resume.optimization import (
    OptimizationGuideline,
    OptimizationMode,
    ResumeSection,
    SectionOptimizationLLMResult,
)
from app.models.resume.resume_ast import ResumeAST


class SectionOptimizer:

    def __init__(
        self,
        llm_service: LLMService,
    ) -> None:

        self.llm_service = llm_service

    def optimize_section(
        self,
        *,
        resume: ResumeAST,
        section: ResumeSection,
        mode: OptimizationMode,
        guidelines: list[OptimizationGuideline],
        job_description: str | None = None,
    ) -> SectionOptimizationLLMResult:

        section_data = self._get_section_data(
            resume,
            section,
        )

        system_prompt = self._build_system_prompt()

        user_prompt = self._build_user_prompt(
            section=section,
            section_data=section_data,
            mode=mode,
            guidelines=guidelines,
            job_description=job_description,
        )

        return self.llm_service.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=SectionOptimizationLLMResult,
        )

    @staticmethod
    def _get_section_data(
        resume: ResumeAST,
        section: ResumeSection,
    ) -> Any:
        if section == ResumeSection.SUMMARY:
            return {
                "record_id": "summary",
                "field": "summary",
                "text": resume.summary,
            }

        return getattr(resume, section.value)

    @staticmethod
    def _build_system_prompt() -> str:

        return """
You are an expert ATS resume optimization engine.

Your job is to propose improvements to existing resume text.

You DO NOT own the resume structure.

You DO NOT reconstruct ResumeAST objects.

You DO NOT create, delete, merge, split, or reorder records.

You DO NOT modify:
- company names
- job titles
- dates
- education
- certifications
- technologies unless only spelling/normalization is explicitly supported
- metrics
- numbers
- scope
- factual claims
- record identity

You may improve wording of existing textual fields.

Absolute fact-preservation rule:

Never invent:
- technologies
- tools
- responsibilities
- achievements
- metrics
- percentages
- users
- revenue
- performance improvements
- team sizes
- dates
- certifications
- education
- outcomes

An optimized statement must be supported by the original statement.

Prefer:

ACTION + WHAT + HOW + SCOPE/CONTEXT + OUTCOME

but only include components that are supported by the source.

Improve:
1. clarity
2. achievement orientation
3. strong action verbs
4. ATS terminology normalization
5. concision
6. readability

Do not make text longer merely for the sake of optimization.

Return optimization proposals only.

Each change must identify:
- the existing record ID
- the field to change
- the original text
- the optimized text
- the guideline
- the reason

The optimized_text must be plain text.

Do not return JSON inside strings.
Do not return ResumeAST objects.

Record identification rules:

- Never invent record IDs.
- For the summary section, always use record_id="summary".
- For the summary section, the only optimizable field is "summary".
- For all other sections, use the existing record ID from the supplied ResumeAST.
"""

    @staticmethod
    def _build_user_prompt(
        *,
        section: ResumeSection,
        section_data: Any,
        mode: OptimizationMode,
        guidelines: list[OptimizationGuideline],
        job_description: str | None,
    ) -> str:

        guidelines_text = "\n".join(
            f"- {g.id}: {g.description}"
            for g in guidelines
            if g.enabled
            and (
                not g.applies_to
                or section in g.applies_to
            )
        )

        return f"""
Optimize the following resume section.

SECTION:
{section.value}

MODE:
{mode.value}

GUIDELINES:
{guidelines_text or "- Apply standard ATS optimization rules."}

JOB DESCRIPTION:
{job_description or "No target job description supplied."}

IMPORTANT:
Only propose changes to existing text.

RESUME SECTION DATA:
{json.dumps(
    section_data,
    indent=2,
    default=str,
)}
"""