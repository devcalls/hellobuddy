from __future__ import annotations

from pathlib import Path

from app.integration.resume.pdf_renderer import ResumePdfRenderer
from app.models.resume.resume_ast import ResumeAST
import json

class ResumeRendererService:
    """
    Application service responsible for rendering ResumeAST
    into user-facing document formats.
    """

    def __init__(self) -> None:
        self._pdf_renderer = ResumePdfRenderer()

    def render_pdf(
        self,
        resume: ResumeAST,
        output_path: str | Path,
    ) -> Path:
        return self._pdf_renderer.render(
            resume=resume,
            output_path=output_path,
        )
        
    def load_resume_ast(self, path: str | Path) -> ResumeAST:
        path = Path(path)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        # Optimizer output
        if "optimized_resume" in data:
            data = data["optimized_resume"]

        return ResumeAST.model_validate(data)
        
    
    