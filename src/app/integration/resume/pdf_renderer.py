from __future__ import annotations

from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from app.models.resume.resume_ast import (
    Achievement,
    Certification,
    Education,
    Experience,
    Project,
    ResumeAST,
    Skill,
)


class ResumePdfRenderer:
    """
    Render a ResumeAST into an ATS-friendly PDF.

    Rendering is intentionally read-only:
    - The ResumeAST is never modified.
    - Structured facts are rendered as-is.
    - Only presentation decisions happen here.
    """

    def __init__(
        self,
        *,
        page_size=A4,
        left_margin: float = 0.55 * inch,
        right_margin: float = 0.55 * inch,
        top_margin: float = 0.45 * inch,
        bottom_margin: float = 0.45 * inch,
    ) -> None:
        self.page_size = page_size
        self.left_margin = left_margin
        self.right_margin = right_margin
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin

        self.styles = self._build_styles()

    def render(
        self,
        resume: ResumeAST,
        output_path: str | Path,
    ) -> Path:
        """
        Render ResumeAST to PDF.

        Args:
            resume: Canonical ResumeAST.
            output_path: Destination PDF path.

        Returns:
            Path to generated PDF.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        document = SimpleDocTemplate(
            str(output_path),
            pagesize=self.page_size,
            rightMargin=self.right_margin,
            leftMargin=self.left_margin,
            topMargin=self.top_margin,
            bottomMargin=self.bottom_margin,
            title=self._document_title(resume),
            author=self._author_name(resume),
        )

        story = self._build_story(resume)

        document.build(
            story,
            onFirstPage=self._draw_page,
            onLaterPages=self._draw_page,
        )

        return output_path

    # ------------------------------------------------------------------
    # Document construction
    # ------------------------------------------------------------------

    def _build_story(self, resume: ResumeAST) -> list:
        story: list = []

        self._add_header(story, resume)

        if resume.summary:
            self._add_section_heading(story, "SUMMARY")
            story.append(
                Paragraph(
                    self._escape(resume.summary),
                    self.styles["body"],
                )
            )
            story.append(Spacer(1, 8))

        if resume.experience:
            self._add_section_heading(story, "EXPERIENCE")

            for experience in resume.experience:
                story.extend(self._render_experience(experience))

            story.append(Spacer(1, 4))

        if resume.projects:
            self._add_section_heading(story, "PROJECTS")

            for project in resume.projects:
                story.extend(self._render_project(project))

            story.append(Spacer(1, 4))

        if resume.skills:
            self._add_section_heading(story, "SKILLS")
            story.extend(self._render_skills(resume.skills))
            story.append(Spacer(1, 4))

        if resume.education:
            self._add_section_heading(story, "EDUCATION")

            for education in resume.education:
                story.extend(self._render_education(education))

            story.append(Spacer(1, 4))

        if resume.certifications:
            self._add_section_heading(story, "CERTIFICATIONS")

            for certification in resume.certifications:
                story.extend(self._render_certification(certification))

        return story

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _add_header(self, story: list, resume: ResumeAST) -> None:
        contact = resume.contact

        name = contact.name or resume.metadata.source_file or "Resume"

        story.append(
            Paragraph(
                self._escape(name),
                self.styles["name"],
            )
        )

        contact_parts = []

        if contact.location:
            contact_parts.append(contact.location)

        if contact.phone:
            contact_parts.append(contact.phone)

        if contact.email:
            contact_parts.append(contact.email)

        if contact.linkedin:
            contact_parts.append(contact.linkedin)

        if contact.github:
            contact_parts.append(contact.github)

        if contact.portfolio:
            contact_parts.append(contact.portfolio)

        if contact_parts:
            story.append(
                Paragraph(
                    self._escape(" | ".join(contact_parts)),
                    self.styles["contact"],
                )
            )

        story.append(Spacer(1, 7))

        story.append(
            HRFlowable(
                width="100%",
                thickness=0.7,
                color=colors.black,
                spaceBefore=0,
                spaceAfter=8,
            )
        )

    # ------------------------------------------------------------------
    # Experience
    # ------------------------------------------------------------------

    def _render_experience(
        self,
        experience: Experience,
    ) -> list:
        flowables = []

        company = self._escape(experience.company)
        title = self._escape(experience.title)

        flowables.append(
            Paragraph(
                f"<b>{company}</b> — {title}",
                self.styles["job_header"],
            )
        )

        metadata = []

        date_text = self._format_date_range(experience.date_range)

        if date_text:
            metadata.append(date_text)

        if experience.location:
            metadata.append(experience.location)

        if metadata:
            flowables.append(
                Paragraph(
                    self._escape(" | ".join(metadata)),
                    self.styles["metadata"],
                )
            )

        if experience.description:
            flowables.append(
                Spacer(1, 2)
            )
            flowables.append(
                Paragraph(
                    self._escape(experience.description),
                    self.styles["body"],
                )
            )

        for achievement in experience.achievements:
            flowables.append(
                self._render_bullet(achievement.text)
            )

        flowables.append(Spacer(1, 6))

        return [
            KeepTogether(flowables)
        ]

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def _render_project(
        self,
        project: Project,
    ) -> list:
        flowables = []

        technologies = ""

        if project.technologies:
            technologies = (
                " | "
                + ", ".join(project.technologies)
            )

        header = (
            f"<b>{self._escape(project.name)}</b>"
            f"{self._escape(technologies)}"
        )

        flowables.append(
            Paragraph(
                header,
                self.styles["job_header"],
            )
        )

        if project.description:
            flowables.append(
                Paragraph(
                    self._escape(project.description),
                    self.styles["body"],
                )
            )

        for achievement in project.achievements:
            flowables.append(
                self._render_bullet(achievement.text)
            )

        flowables.append(Spacer(1, 5))

        return [
            KeepTogether(flowables)
        ]

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------

    def _render_skills(
        self,
        skills: Iterable[Skill],
    ) -> list:
        flowables = []

        grouped: dict[str, list[str]] = {}

        for skill in skills:
            category = skill.category or "Skills"
            grouped.setdefault(category, []).append(skill.name)

        for category, names in grouped.items():
            text = (
                f"<b>{self._escape(category)}:</b> "
                f"{self._escape(', '.join(names))}"
            )

            flowables.append(
                Paragraph(
                    text,
                    self.styles["body"],
                )
            )

        return flowables

    # ------------------------------------------------------------------
    # Education
    # ------------------------------------------------------------------

    def _render_education(
        self,
        education: Education,
    ) -> list:
        flowables = []

        institution = self._escape(education.institution)

        degree_parts = []

        if education.degree:
            degree_parts.append(education.degree)

        if education.field_of_study:
            degree_parts.append(
                education.field_of_study
            )

        degree = ""

        if degree_parts:
            degree = " — " + self._escape(
                ", ".join(degree_parts)
            )

        flowables.append(
            Paragraph(
                f"<b>{institution}</b>{degree}",
                self.styles["job_header"],
            )
        )

        metadata = []

        date_text = self._format_date_range(
            education.date_range
        )

        if date_text:
            metadata.append(date_text)

        if education.location:
            metadata.append(education.location)

        if metadata:
            flowables.append(
                Paragraph(
                    self._escape(" | ".join(metadata)),
                    self.styles["metadata"],
                )
            )

        flowables.append(Spacer(1, 5))

        return [
            KeepTogether(flowables)
        ]

    # ------------------------------------------------------------------
    # Certifications
    # ------------------------------------------------------------------

    def _render_certification(
        self,
        certification: Certification,
    ) -> list:
        name = self._escape(certification.name)

        details = []

        if certification.issuer:
            details.append(certification.issuer)

        if certification.date:
            details.append(certification.date)

        if certification.credential_id:
            details.append(
                f"Credential ID: {certification.credential_id}"
            )

        text = f"<b>{name}</b>"

        if details:
            text += " — " + self._escape(
                " | ".join(details)
            )

        return [
            Paragraph(
                text,
                self.styles["body"],
            ),
            Spacer(1, 3),
        ]

    # ------------------------------------------------------------------
    # Common components
    # ------------------------------------------------------------------

    def _add_section_heading(
        self,
        story: list,
        title: str,
    ) -> None:
        story.append(
            Paragraph(
                self._escape(title),
                self.styles["section"],
            )
        )

    def _render_bullet(
        self,
        text: str,
    ) -> Paragraph:
        return Paragraph(
            f"&bull; {self._escape(text)}",
            self.styles["bullet"],
        )

    def _format_date_range(self, date_range) -> str:
        start = self._format_date(
            date_range.start_date
        )

        if date_range.current:
            end = "Present"
        else:
            end = self._format_date(
                date_range.end_date
            )

        if start and end:
            return f"{start} – {end}"

        if start:
            return start

        if end:
            return end

        if date_range.source_text:
            return date_range.source_text

        return ""

    @staticmethod
    def _format_date(value) -> str:
        if value is None:
            return ""

        return value.strftime("%b %Y")

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _build_styles(self):
        styles = getSampleStyleSheet()

        return {
            "name": ParagraphStyle(
                "ResumeName",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=18,
                leading=21,
                alignment=TA_LEFT,
                spaceAfter=2,
            ),
            "contact": ParagraphStyle(
                "ResumeContact",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                spaceAfter=0,
            ),
            "section": ParagraphStyle(
                "ResumeSection",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10.5,
                leading=13,
                spaceBefore=5,
                spaceAfter=4,
            ),
            "job_header": ParagraphStyle(
                "ResumeJobHeader",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9.5,
                leading=12,
                spaceAfter=1,
            ),
            "metadata": ParagraphStyle(
                "ResumeMetadata",
                parent=styles["Normal"],
                fontName="Helvetica-Oblique",
                fontSize=8,
                leading=10,
                spaceAfter=2,
            ),
            "body": ParagraphStyle(
                "ResumeBody",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                spaceAfter=2,
            ),
            "bullet": ParagraphStyle(
                "ResumeBullet",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                leftIndent=12,
                firstLineIndent=-7,
                spaceAfter=2,
            ),
        }

    # ------------------------------------------------------------------
    # PDF metadata / page
    # ------------------------------------------------------------------

    def _draw_page(self, canvas, document) -> None:
        canvas.saveState()

        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(
            self.page_size[0] - self.right_margin,
            0.25 * inch,
            f"{document.page}",
        )

        canvas.restoreState()

    @staticmethod
    def _document_title(resume: ResumeAST) -> str:
        return (
            resume.contact.name
            or resume.metadata.source_file
            or "Resume"
        )

    @staticmethod
    def _author_name(resume: ResumeAST) -> str:
        return resume.contact.name or ""

    @staticmethod
    def _escape(value: str) -> str:
        """
        Escape text for ReportLab Paragraph XML.
        """
        if not value:
            return ""

        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )