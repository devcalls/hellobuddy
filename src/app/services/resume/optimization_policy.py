from __future__ import annotations

from app.models.resume.optimization import ResumeSection

# ONLY narrative/prose fields may be changed by ATS optimization.
EDITABLE_FIELDS: dict[ResumeSection, frozenset[str]] = {
    ResumeSection.SUMMARY: frozenset({"summary"}),
    ResumeSection.EXPERIENCE: frozenset({"description", "text"}),
    ResumeSection.PROJECTS: frozenset({"description", "text"}),
    ResumeSection.SKILLS: frozenset(),
    ResumeSection.EDUCATION: frozenset(),
    ResumeSection.CERTIFICATIONS: frozenset(),
}


def is_field_editable(section: ResumeSection, field: str) -> bool:
    leaf = field.rsplit(".", 1)[-1]
    return leaf in EDITABLE_FIELDS.get(section, frozenset())


def editable_fields_text(section: ResumeSection) -> str:
    fields = sorted(EDITABLE_FIELDS.get(section, frozenset()))
    return ", ".join(fields) if fields else "none"
