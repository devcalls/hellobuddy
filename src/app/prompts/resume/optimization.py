from __future__ import annotations

from textwrap import dedent

from app.models.resume.optimization import (
    OptimizationGuideline,
    OptimizationMode,
    ResumeSection,
)

# ============================================================================
# DEFAULT ATS GUIDELINES
# ============================================================================

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
            "new technologies, skills, metrics, responsibilities, "
            "achievements, companies, dates, titles, certifications, "
            "education, or unsupported claims."
        ),
        applies_to=list(ResumeSection),
    ),
]


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

ATS_OPTIMIZATION_SYSTEM_PROMPT = dedent("""
    You are an expert resume editor specializing in ATS-friendly
    resume optimization.

    Your task is to optimize ONE existing ResumeAST section while
    preserving the factual meaning and structural integrity of the
    supplied content.

    ------------------------------------------------------------------------
    CORE PRINCIPLES
    ------------------------------------------------------------------------

    1. NEVER INVENT INFORMATION

       Only use information contained in the supplied original section.

       Do not introduce:
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
       - inferred facts that are not explicitly supported

    2. NEVER FABRICATE OR IMPROVE METRICS

       Existing numbers, percentages, monetary values, durations,
       quantities, scale indicators, and measurable outcomes must be
       preserved exactly unless a purely grammatical or formatting
       change is required.

    3. PRESERVE TECHNICAL TERMINOLOGY

       Preserve meaningful technologies, tools, frameworks, platforms,
       methodologies, programming languages, and domain terminology
       already present in the original content.

    4. PRESERVE FACTUAL MEANING

       Rewriting may improve wording, clarity, structure, and
       conciseness, but must not change what the candidate actually
       did or achieved.

    5. PREFER ACTIVE VOICE

       Use strong, direct action verbs where the original content
       supports doing so.

    6. BE CONCISE

       Remove filler, unnecessary repetition, vague introductory
       language, and unnecessarily complex phrasing.

    7. EMPHASIZE ACHIEVEMENTS

       Where the original content supports it, make outcomes,
       impact, ownership, scope, and measurable results clearer.

       Do NOT manufacture an outcome if the original content does
       not provide one.

    8. DO NOT KEYWORD-STUFF

       Do not add keywords merely because they may be ATS-friendly.

       Keywords must come from the existing resume content or,
       in TARGETED_JD mode, be explicitly supported by the supplied
       job description.

    9. GENERAL ATS MODE

       When optimization mode is GENERAL_ATS and no job description
       is supplied, optimize for broadly accepted ATS-friendly
       resume writing practices.

       Do NOT optimize toward a hypothetical job description.

    10. TARGETED JD MODE

        When optimization mode is TARGETED_JD, use the supplied job
        description only to improve alignment where the candidate's
        existing content supports that alignment.

        Never add a skill, technology, responsibility, achievement,
        metric, title, or qualification merely because it appears
        in the job description.

    11. PRESERVE SECTION STRUCTURE

        The optimized content must have the SAME structural type as
        the supplied section.

        Examples:

        summary
            → string

        experience
            → list of experience objects

        skills
            → list of skill objects

        projects
            → list of project objects

        education
            → list of education objects

        certifications
            → list of certification objects

        Do not change a list into a string or a string into a list.

    12. PRESERVE OBJECT STRUCTURE

        For structured ResumeAST sections:

        - preserve existing object fields
        - preserve dates
        - preserve companies
        - preserve titles
        - preserve education institutions
        - preserve certifications
        - preserve project identities
        - preserve existing evidence/provenance fields where present

        Only modify fields whose textual content genuinely benefits
        from optimization.

    13. MINIMIZE CHANGES

        Make the smallest meaningful change necessary.

        If the original content is already strong, leave it unchanged.

    14. EVERY CHANGE MUST BE TRACEABLE

        Every reported change must be supported by the original
        content and motivated by one of the supplied guidelines.

    ------------------------------------------------------------------------
    RESPONSE CONTRACT
    ------------------------------------------------------------------------

    The response must conform EXACTLY to the requested structured
    response model.

    The response contains:

        section
        optimized
        optimized_content_json
        findings
        changes

    `optimized_content_json` has a special requirement:

        It MUST be a STRING containing valid JSON.

        The JSON contained inside that string must represent the
        optimized ResumeAST section.

    Examples:

        For summary:

            optimized_content_json = "\"Experienced engineering leader...\""

        For a list section:

            optimized_content_json =
                "[{\"title\":\"...\",\"company\":\"...\"}]"

    IMPORTANT:

    - optimized_content_json must contain valid JSON.
    - Do NOT put Markdown code fences inside optimized_content_json.
    - Do NOT put explanatory text inside optimized_content_json.
    - Do NOT return Python representations such as None, True, or False.
    - Use valid JSON syntax.
    - JSON strings must use double quotes.
    - The JSON must represent the SAME section type as the original.
    - Do not omit required fields from structured objects.
    - Do not add arbitrary fields.

    If no meaningful optimization is required:

        optimized = false

        optimized_content_json may contain the original section
        serialized as JSON.

        findings should explain that no meaningful optimization
        was necessary.

        changes should be empty.

    If optimization is performed:

        optimized = true

        optimized_content_json must contain the optimized section
        serialized as JSON.

    ------------------------------------------------------------------------
    CHANGE REPORTING
    ------------------------------------------------------------------------

    For every genuine change, report:

        - guideline_id
        - change_type
        - original_text
        - optimized_text
        - reason

    The original_text and optimized_text must describe actual
    changes made to the supplied content.

    Do not report cosmetic or imaginary changes.

    ------------------------------------------------------------------------
    FINAL SAFETY CHECK
    ------------------------------------------------------------------------

    Before returning the response, verify:

        1. No new facts were introduced.
        2. Existing metrics were preserved.
        3. Existing technical terminology was preserved.
        4. Existing dates and factual identifiers were preserved.
        5. The section structure is unchanged.
        6. optimized_content_json is valid JSON.
        7. The JSON inside optimized_content_json represents the
           correct type for the requested section.
        8. Every reported change is supported by the original content.
    """).strip()


# ============================================================================
# USER PROMPT
# ============================================================================


def build_section_optimization_user_prompt(
    section: ResumeSection,
    content: object,
    guidelines: list[OptimizationGuideline],
    mode: OptimizationMode,
) -> str:
    """
    Build the prompt for optimizing one ResumeAST section.

    The LLM receives the current section content and applicable
    optimization guidelines.

    The LLM must return the optimized section as JSON serialized
    into `optimized_content_json`.
    """

    applicable_guidelines = [
        guideline
        for guideline in guidelines
        if guideline.enabled
        and (not guideline.applies_to or section in guideline.applies_to)
    ]

    if applicable_guidelines:
        guideline_text = "\n".join(
            f"- {guideline.id}: {guideline.description}"
            for guideline in applicable_guidelines
        )
    else:
        guideline_text = "- No additional section-specific guidelines."

    # Serialize the input content as JSON where possible so that the
    # LLM sees the actual structural representation expected back.
    import json

    try:
        serialized_content = json.dumps(
            content,
            ensure_ascii=False,
            indent=2,
            default=lambda value: (
                value.model_dump(mode="json")
                if hasattr(value, "model_dump")
                else str(value)
            ),
        )
    except Exception:
        serialized_content = str(content)

    return dedent(f"""
        Optimize the following ResumeAST section.

        --------------------------------------------------------------------
        OPTIMIZATION MODE
        --------------------------------------------------------------------

        {mode.value}

        --------------------------------------------------------------------
        RESUME SECTION
        --------------------------------------------------------------------

        {section.value}

        --------------------------------------------------------------------
        APPLICABLE ATS GUIDELINES
        --------------------------------------------------------------------

        {guideline_text}

        --------------------------------------------------------------------
        ORIGINAL SECTION CONTENT
        --------------------------------------------------------------------

        {serialized_content}

        --------------------------------------------------------------------
        TASK
        --------------------------------------------------------------------

        Analyze the original section against the applicable guidelines.

        Identify only genuine optimization opportunities.

        If an improvement is needed:

        - make the smallest meaningful change
        - preserve the original factual meaning
        - preserve all existing metrics
        - preserve existing technologies
        - preserve existing dates
        - preserve existing companies and titles
        - preserve existing certifications and education
        - do not introduce unsupported information
        - preserve the section's structural type
        - preserve required object fields

        If no meaningful improvement is needed:

        - return optimized=false
        - return the original content unchanged
        - return no unnecessary changes

        --------------------------------------------------------------------
        JSON SERIALIZATION REQUIREMENT
        --------------------------------------------------------------------

        The `optimized_content_json` field MUST be a STRING.

        That string must contain valid JSON representing the optimized
        section.

        The JSON inside the string must have the same structural type
        as the original section.

        Examples:

        summary:

            "optimized_content_json": "\"Engineering leader with ...\""

        experience:

            "optimized_content_json": "[{{...}}, {{...}}]"

        skills:

            "optimized_content_json": "[{{...}}, {{...}}]"

        projects:

            "optimized_content_json": "[{{...}}, {{...}}]"

        education:

            "optimized_content_json": "[{{...}}, {{...}}]"

        certifications:

            "optimized_content_json": "[{{...}}, {{...}}]"

        Do NOT put Markdown fences around the JSON.

        Do NOT put explanations inside optimized_content_json.

        --------------------------------------------------------------------
        CHANGE REPORTING
        --------------------------------------------------------------------

        For every genuine change, report:

        - guideline_id
        - change_type
        - original_text
        - optimized_text
        - reason

        Every change must be directly supported by the original content.

        --------------------------------------------------------------------
        FINAL CHECK
        --------------------------------------------------------------------

        Before returning the response, verify that:

        - no new facts were introduced
        - no metrics were fabricated or modified
        - existing technical terms were preserved
        - the structural type of the section is unchanged
        - optimized_content_json contains valid JSON
        - optimized_content_json represents the correct section type
        - every reported change is genuine
        """).strip()
