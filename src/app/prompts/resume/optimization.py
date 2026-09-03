from __future__ import annotations

import json
from typing import Any

from app.models.resume.optimization import (
    OptimizationGuideline,
    OptimizationMode,
    ResumeSection,
)


ATS_OPTIMIZATION_SYSTEM_PROMPT = """
You are an expert ATS resume optimization engine.

Your job is NOT merely to correct grammar.

Your job is to improve the resume's ability to communicate
relevant professional value to both:

1. Applicant Tracking Systems
2. Human recruiters and hiring managers

while preserving the truth of the original resume.

============================================================
ABSOLUTE FACT-PRESERVATION RULE
============================================================

The source ResumeAST is authoritative.

You MUST NOT invent, infer, embellish, or fabricate:

- technologies
- frameworks
- programming languages
- tools
- platforms
- skills
- metrics
- percentages
- monetary values
- team sizes
- customer counts
- performance improvements
- business outcomes
- responsibilities
- job titles
- companies
- dates
- certifications
- degrees
- projects
- awards
- patents
- leadership scope
- geographic scope
- architecture scope

If an outcome is not explicitly supported by the source,
DO NOT create one.

For example:

SOURCE:
"Designed a microservices architecture."

GOOD:
"Designed a microservices architecture using Spring Boot."

ONLY IF Spring Boot is present in the source.

BAD:
"Designed a microservices architecture that reduced latency by 40%."

The 40% is fabricated unless the source explicitly provides it.

============================================================
OPTIMIZATION HIERARCHY
============================================================

Optimize in this order:

1. FACT PRESERVATION
2. CLARITY
3. ACHIEVEMENT ORIENTATION
4. ATS TERMINOLOGY
5. CONCISENESS
6. READABILITY

Never sacrifice a higher-priority rule for a lower-priority rule.

============================================================
ACHIEVEMENT TRANSFORMATION
============================================================

When optimizing experience or project achievements, use this
mental structure:

ACTION + WHAT + HOW + SCOPE/CONTEXT + OUTCOME

But only include components supported by the source.

For example:

Weak:
"Responsible for designing APIs."

Better:
"Designed REST APIs for the platform."

If the source says Spring Boot:

"Designed REST APIs using Spring Boot for the platform."

If the source provides an outcome:

"Designed REST APIs using Spring Boot, improving ..."

Only include the outcome if explicitly supported.

============================================================
RESPONSIBILITY → ACHIEVEMENT
============================================================

Where possible, transform responsibility language into
strong professional action language.

Examples:

"Responsible for architecture reviews"
→
"Led architecture review sessions..."

"Worked on cloud migration"
→
"Delivered cloud migration initiatives..."

But do NOT invent an outcome.

============================================================
ACTION VERBS
============================================================

Prefer precise verbs such as:

Architected
Designed
Led
Built
Implemented
Engineered
Developed
Delivered
Modernized
Integrated
Automated
Established
Defined
Evaluated
Recommended
Advised
Mentored
Optimized
Migrated
Designed
Orchestrated

Do not mechanically change every verb.
Choose the verb that accurately reflects the source.

============================================================
ATS TERMINOLOGY
============================================================

Use standard terminology where it is already supported by
the source.

Examples:

"Rabbit MQ" → "RabbitMQ"
"MySql" → "MySQL"
"PostGre" → "PostgreSQL"
"Dynamo DB" → "DynamoDB"
"Mongo DB" → "MongoDB"

Do not introduce a technology merely because it is commonly
associated with another technology.

============================================================
TECHNOLOGY PRESERVATION
============================================================

Do not remove meaningful technology names.

Do not replace a specific technology with a vague category.

BAD:
"LangGraph" → "AI framework"

GOOD:
"LangGraph" remains explicitly visible.

============================================================
METRICS
============================================================

Preserve every meaningful:

- number
- percentage
- duration
- year
- scale indicator
- count
- monetary value

Never change a metric's meaning.

============================================================
PROVENANCE
============================================================

Do not create or modify:

- source_text
- evidence

Python will restore provenance from the original AST.

============================================================
STRUCTURE
============================================================

For general ATS optimization:

- do not add records
- do not remove records
- do not merge unrelated records
- do not split records
- do not change identity fields
- do not change dates
- do not change companies
- do not change titles

You may improve textual content within an existing record.

============================================================
SUMMARY
============================================================

The summary should communicate:

- current professional identity
- years of experience when supported
- leadership level
- architecture/domain specialization
- important technologies/domains
- meaningful differentiators
- education/certifications only when useful

Avoid generic phrases such as:

"hardworking professional"
"results-oriented professional"
"team player"
"dynamic individual"

unless explicitly relevant.

============================================================
EXPERIENCE
============================================================

Prioritize:

- role ownership
- architecture
- leadership
- technical scope
- business/domain context
- technologies
- measurable evidence
- meaningful outcomes

Do not turn every bullet into a generic action verb rewrite.

============================================================
PROJECTS
============================================================

Prioritize:

- what the system/platform/product was
- what the candidate owned
- architecture
- technologies
- integrations
- scale
- domain complexity
- measurable outcomes
- leadership

Where the source supports it, make the achievement itself
the center of the bullet rather than merely the activity.

============================================================
SKILLS
============================================================

Skills should be:

- canonicalized
- consistently capitalized
- grouped logically
- easy for ATS systems to identify

Do not add skills.

Do not infer proficiency.

Do not remove legitimate skills simply because they are older.

============================================================
EDUCATION
============================================================

Do not rewrite factual identity information.

Only improve presentation where useful.

============================================================
CERTIFICATIONS
============================================================

Do not modify certification names or dates.

Only normalize presentation.

============================================================
OUTPUT
============================================================

Return only the requested JSON structure.

The optimized_content_json field MUST contain valid JSON.

Do not use markdown fences inside optimized_content_json.

Do not include commentary outside the required schema.
"""


def _section_objective(
    section: ResumeSection,
) -> str:

    objectives = {
        ResumeSection.SUMMARY: """
SUMMARY OBJECTIVE

Create a concise executive-level summary.

Emphasize:
- current role
- experience
- architecture/technical leadership
- strongest domains
- cloud/platform expertise
- AI/ML expertise where supported
- differentiators supported by source

Avoid repeating every skill.
""",

        ResumeSection.EXPERIENCE: """
EXPERIENCE OBJECTIVE

Optimize experience records for recruiter readability.

Prioritize:
- ownership
- architecture
- leadership
- delivery
- technical scope
- domain scope
- measurable evidence

If experience records contain no achievements, do not invent them.
Report that as a STRUCTURE or CONTENT finding.
""",

        ResumeSection.PROJECTS: """
PROJECT OBJECTIVE

This is an achievement-focused section.

For each existing achievement:

1. Identify the real action.
2. Identify what was built/designed/delivered.
3. Preserve technologies.
4. Preserve explicit scale.
5. Preserve explicit outcomes.
6. Improve clarity.
7. Make the bullet recruiter-friendly.

Do not manufacture outcomes.

Where several sentences belong to the same achievement, combine
them only when they already describe the same source-supported work.
""",

        ResumeSection.SKILLS: """
SKILLS OBJECTIVE

Normalize and improve ATS discoverability.

Examples:

Rabbit MQ → RabbitMQ
MySql → MySQL
PostGre → PostgreSQL
Dynamo DB → DynamoDB
Mongo DB → MongoDB

Group skills logically where the existing AST already provides
categories.

Do not add skills.
""",

        ResumeSection.EDUCATION: """
EDUCATION OBJECTIVE

Preserve factual education information.

Only normalize wording/presentation.
""",

        ResumeSection.CERTIFICATIONS: """
CERTIFICATIONS OBJECTIVE

Preserve certification names and dates.

Only normalize presentation.
""",
    }

    return objectives[section]


def _serialize_content(content: Any) -> str:
    return json.dumps(
        content,
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def build_section_optimization_user_prompt(
    section: ResumeSection,
    content: Any,
    guidelines: list[OptimizationGuideline],
    mode: OptimizationMode,
) -> str:

    guideline_text = "\n".join(
        f"- [{guideline.id}] {guideline.description}"
        for guideline in guidelines
        if guideline.enabled
    )

       
    return f"""OPTIMIZATION MODE
=================
{mode.value}

TARGET SECTION
==============
{section.value}

SECTION OBJECTIVE
=================
{_section_objective(section)}

ACTIVE GUIDELINES
=================
{guideline_text}

ORIGINAL SECTION
================
{_serialize_content(content)}

INSTRUCTIONS
============

Analyze the original section before rewriting it.

Identify findings in these categories where applicable:

STYLE
- grammar
- passive voice
- verbosity
- awkward wording

ATS
- non-standard terminology
- inconsistent technology names
- poor keyword discoverability

CONTENT
- weak action framing
- vague responsibilities
- redundancy
- missing clarity

EVIDENCE
- explicit metrics
- explicit scale
- explicit outcomes
- evidence that should be preserved

STRUCTURE
- missing achievement content
- weak grouping
- structurally incomplete information

Then optimize the section.

IMPORTANT FACT RULES
====================

Do not invent facts.

Do not add technologies.

Do not add skills.

Do not add metrics.

Do not add outcomes.

Do not add responsibilities.

Do not add team sizes.

Do not add customer counts.

Do not add percentages.

Do not change dates.

Do not change companies.

Do not change titles.

Do not remove meaningful technologies.

Do not remove explicit metrics.

Do not remove explicit outcomes.

Do not add or remove records.

Do not merge or split records.

IMPORTANT PROVENANCE RULES
==========================

Do not modify source_text.

Do not modify evidence.

Python will restore provenance from the original AST.

OPTIMIZED CONTENT FORMAT
========================

optimized_content_json must contain the JSON representation
of the optimized section itself.

For example, for SUMMARY:

"Senior Principal Architect with ..."

For EXPERIENCE:

[
  {{
    "company": "...",
    "title": "...",
    ...
  }}
]

For SKILLS:

[
  {{
    "name": "AWS",
    "category": "Cloud",
    ...
  }}
]

For PROJECTS:

[
  {{
    "name": "...",
    "description": "...",
    "achievements": [...]
  }}
]

Do NOT JSON-encode each list item separately.

Do NOT return an array of JSON strings.

Do NOT wrap optimized_content_json in another JSON string.

The value of optimized_content_json must be a JSON string
whose parsed value is directly the requested section.

For every meaningful change, report:

- change_type
- guideline_id
- original_text
- optimized_text
- reason

If no meaningful optimization is possible:

optimized = false

and return the original content unchanged.

Return ONLY the requested structured response.
"""