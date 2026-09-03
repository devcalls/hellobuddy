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
from app.services.resume.optimization_policy import editable_fields_text


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
        excluded_record_ids: set[str] | None = None,
    ) -> SectionOptimizationLLMResult:

        section_data = self._get_section_data(
            resume,
            section,
            excluded_record_ids=excluded_record_ids or set(),
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
        *,
        excluded_record_ids: set[str] | None = None,
    ) -> Any:
        if section == ResumeSection.SUMMARY:
            return {
                "record_id": "summary",
                "field": "summary",
                "text": resume.summary,
            }

        excluded_record_ids = excluded_record_ids or set()

        if section == ResumeSection.EXPERIENCE:
            projects_by_id = {
                project.id: project
                for project in resume.projects
            }

            result = []
            for experience in resume.experience:
                result.append({
                    "record": experience.model_dump(mode="json"),
                    "associated_projects": [
                        projects_by_id[project_id].model_dump(mode="json")
                        for project_id in experience.project_ids
                        if project_id in projects_by_id
                        and project_id not in excluded_record_ids
                    ],
                })
            return result

        records = getattr(resume, section.value)
        if section == ResumeSection.PROJECTS and excluded_record_ids:
            return [
                record
                for record in records
                if record.id not in excluded_record_ids
            ]

        return records

    @staticmethod
    def _build_system_prompt() -> str:
        return """
You are an expert ATS resume optimization engine.

Inspect the supplied resume section and propose concrete, factual, high-value
improvements to existing narrative text. Python owns the ResumeAST; you only
propose text replacements.

IMMUTABLE FACTS
- record IDs
- company names, job titles, dates/date ranges, locations
- technologies, tools, skills
- metrics, numbers, percentages, monetary values and scale
- education and certifications
- credential IDs/URLs
- project relationships
- source_text and evidence/provenance

Never invent facts, responsibilities, achievements, outcomes, metrics,
technologies, skills, dates, users, revenue, team sizes or performance claims.

CHANGE CONTRACT
Each change must contain only:
- record_id: an existing record ID
- field: an editable field from EDITABLE FIELDS
- change_type: rewrite or normalize
- optimized_text: replacement plain text
- guideline_id: a supplied guideline ID
- reason: concise explanation

Do NOT return original_text. The application obtains the authoritative
original text from the ResumeAST.

OPTIMIZATION STANDARD
Look for material improvements in clarity, precision, action orientation,
achievement orientation where supported, ATS terminology already present,
concision, readability, and removal of vague/repetitive/filler wording.
Prefer ACTION + WHAT + HOW + SCOPE/OUTCOME only when those facts are supported.

GENERAL ATS MODE
Do not mechanically rewrite every bullet. But do not return an empty change
list merely because the resume is reasonably good. Inspect the editable text
records and identify the highest-value opportunities. When material
improvements exist, normally propose 1-5 concrete changes for a substantial
section. Prefer high-value changes over cosmetic edits.

If a section genuinely needs no textual improvement, return optimized=false,
changes=[], and findings explaining what was reviewed and why no change is
warranted.

TARGETED JD MODE
Use the supplied job description to improve alignment only where the resume
already contains supporting evidence. Never add missing facts merely because
they appear in the JD.

EDITABLE FIELDS are authoritative. If the value is "none", return no changes.

Record identification rules:
- Never invent record IDs.
- Summary: record_id="summary", field="summary".
- Achievement text: existing achievement ID, field="text".
- Project description: existing project ID, field="description".
- Experience description: existing experience ID, field="description".

Return one structured SectionOptimizationLLMResult and nothing else.
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

EDITABLE FIELDS FOR THIS SECTION:
{editable_fields_text(section)}

IMPORTANT:
- Inspect every editable narrative record in the supplied section data.
- If material improvements exist, return 1-5 concrete changes.
- Do not return original_text; Python obtains it from the AST.
- Do not invent or alter immutable facts.

RESUME SECTION DATA:
{json.dumps(
    section_data,
    indent=2,
    default=str,
)}
"""