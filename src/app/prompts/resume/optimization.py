from __future__ import annotations

from app.models.resume.optimization import (
    OptimizationGuideline,
    ResumeSection,
)

from textwrap import dedent
from app.models.resume.optimization import (
    OptimizationGuideline,
    OptimizationMode,
    ResumeSection,
)

DEFAULT_ATS_GUIDELINES = [
    OptimizationGuideline(
        id="active_voice",
        description=(
            "Prefer active voice. Rewrite passive or indirect constructions "
            "using clear, direct action verbs while preserving factual meaning."
        ),
        applies_to=[
            ResumeSection.SUMMARY,
            ResumeSection.EXPERIENCE,
            ResumeSection.PROJECTS,
        ],
    ),
    OptimizationGuideline(
        id="concise_language",
        description=(
            "Use concise language. Remove unnecessary words, repetition, "
            "and vague introductory phrases without removing meaningful facts."
        ),
        applies_to=[
            ResumeSection.SUMMARY,
            ResumeSection.EXPERIENCE,
            ResumeSection.PROJECTS,
        ],
    ),
    OptimizationGuideline(
        id="achievement_oriented",
        description=(
            "Where the original content supports it, emphasize outcomes, "
            "impact, scope, ownership, and accomplishments rather than "
            "generic responsibilities."
        ),
        applies_to=[
            ResumeSection.EXPERIENCE,
            ResumeSection.PROJECTS,
        ],
    ),
    OptimizationGuideline(
        id="preserve_metrics",
        description=(
            "Preserve existing numbers, percentages, monetary values, "
            "timeframes, scale indicators, and measurable outcomes."
        ),
        applies_to=[
            ResumeSection.SUMMARY,
            ResumeSection.EXPERIENCE,
            ResumeSection.PROJECTS,
        ],
    ),
    OptimizationGuideline(
        id="preserve_technical_terms",
        description=(
            "Preserve meaningful technologies, tools, platforms, "
            "programming languages, frameworks, methodologies, and domain "
            "terminology already present in the source."
        ),
        applies_to=[
            ResumeSection.SUMMARY,
            ResumeSection.EXPERIENCE,
            ResumeSection.SKILLS,
            ResumeSection.PROJECTS,
        ],
    ),
    OptimizationGuideline(
        id="group_skills",
        description=(
            "Group existing skills into meaningful categories. Do not "
            "invent skills or add technologies that are not present in "
            "the original resume."
        ),
        applies_to=[
            ResumeSection.SKILLS,
        ],
    ),
    OptimizationGuideline(
        id="remove_redundancy",
        description=(
            "Reduce unnecessary repetition while preserving distinct "
            "facts and achievements."
        ),
        applies_to=[
            ResumeSection.SUMMARY,
            ResumeSection.EXPERIENCE,
            ResumeSection.SKILLS,
            ResumeSection.PROJECTS,
        ],
    ),
    OptimizationGuideline(
        id="standardize_terminology",
        description=(
            "Use consistent terminology for the same technology, role, "
            "methodology, or concept when the meaning is unchanged."
        ),
        applies_to=[
            ResumeSection.SUMMARY,
            ResumeSection.EXPERIENCE,
            ResumeSection.SKILLS,
            ResumeSection.PROJECTS,
        ],
    ),
    OptimizationGuideline(
        id="no_new_facts",
        description=(
            "Do not invent or infer unsupported facts. Never introduce "
            "new technologies, metrics, responsibilities, achievements, "
            "companies, dates, titles, certifications, or education."
        ),
        applies_to=list(ResumeSection),
    ),
]


ATS_OPTIMIZATION_SYSTEM_PROMPT = dedent("""
    You are an expert resume editor specializing in ATS-friendly
    resume optimization.

    Your task is to optimize existing resume content while preserving
    the factual meaning of the original content.

    CORE RULES:

    1. Never invent information.

    2. Do not introduce:
       - new technologies
       - new skills
       - new metrics
       - new achievements
       - new responsibilities
       - new companies
       - new job titles
       - new dates
       - new certifications
       - new education
       - unsupported claims

    3. Never fabricate or improve a metric.

    4. Preserve existing metrics and meaningful technical terminology.

    5. Prefer active voice over passive voice.

    6. Prefer concise, direct language.

    7. Where supported by the original content, emphasize achievements,
       outcomes, impact, ownership, scope, and results rather than
       generic responsibilities.

    8. Do not keyword-stuff the resume.

    9. Do not optimize toward a hypothetical job description when no
       job description has been provided.

    10. If the existing content is already good, do not rewrite it
        unnecessarily.

    11. For skills, organize existing skills into meaningful categories,
        but do not add skills.

    12. Preserve the semantic structure of the supplied section as much
        as possible.

    13. Every reported change must explain why the change improves the
        resume.

    14. Every change must be traceable to the supplied input.

    15. The response must conform exactly to the requested structured
        response model.
    """).strip()


def build_section_optimization_user_prompt(
    section: ResumeSection,
    content: object,
    guidelines: list,
    mode: OptimizationMode,
) -> str:

    applicable_guidelines = [
        guideline
        for guideline in guidelines
        if guideline.enabled
        and (not guideline.applies_to or section in guideline.applies_to)
    ]

    guideline_text = "\n".join(
        f"- {guideline.id}: {guideline.description}"
        for guideline in applicable_guidelines
    )

    return dedent(f"""
        Optimize the following resume section.

        Optimization mode:
        {mode.value}

        Resume section:
        {section.value}

        Applicable ATS guidelines:
        {guideline_text}

        ORIGINAL SECTION CONTENT
        ------------------------
        {content}

        TASK
        ----
        Analyze the original section against the applicable guidelines.

        Identify genuine optimization opportunities.

        If an improvement is needed:
        - make the smallest meaningful change
        - preserve the original factual meaning
        - preserve existing metrics
        - preserve existing technologies and terminology
        - do not introduce unsupported information

        If no meaningful improvement is required, return the original
        content unchanged and report no unnecessary changes.

        For every change, report:
        - the guideline that motivated it
        - the type of change
        - the original text
        - the optimized text
        - why the change was made

        Return the result using the requested structured response model.
        """).strip()
