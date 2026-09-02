from pathlib import Path
import json
from app.services.resume.confidence_service import (
    ResumeConfidenceService,
)
from app.config.resume_settings import (
    ResumeSettings,
)
from app.integration.resume.document_reader import (
    DocumentReader,
)
from app.models.resume.resume_ast import (
    ResumeAST,
)
from app.services.resume.llm_resume_extractor import (
    LLMResumeExtractor,
)
from app.services.resume.resume_ast_builder import (
    ResumeASTBuilder,
)
from app.models.resume.confidence import ResumeAnalysis


class ResumeParserService:

    def __init__(
        self,
        settings: ResumeSettings,
        document_reader=None,
        llm_extractor=None,
        confidence_service=None,
    ):
        self.settings = settings

        self.document_reader = document_reader or DocumentReader()

        self.llm_extractor = llm_extractor or LLMResumeExtractor(settings)

        self.confidence_service = confidence_service or ResumeConfidenceService()

    def save_ast(
        self,
        analysis: ResumeAnalysis,
        output_path: str | Path,
    ) -> Path:
        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(
                analysis.resume.model_dump(mode="json"),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return output_path

    def load_ast(
        self,
        input_path: str | Path,
    ) -> ResumeAST:
        input_path = Path(input_path)

        data = json.loads(input_path.read_text(encoding="utf-8"))

        return ResumeAST.model_validate(data)

    def parse(
        self,
        file_path: str | Path,
    ) -> ResumeAnalysis:

        # Normalize filesystem path at the service boundary.
        file_path = Path(file_path)
        source_file = str(file_path)

        raw_text = self.document_reader.read(file_path)

        extracted_resume = self.llm_extractor.extract(raw_text)

        resume = ResumeASTBuilder().build(
            extraction=extracted_resume,
            source_text=raw_text,
            source_file=source_file,
            source_format=file_path.suffix.lower(),
        )

        confidence = self.confidence_service.calculate(resume)

        # Ensure metadata is normalized even if the builder
        # does not populate these fields correctly.
        resume.metadata.source_file = source_file
        resume.metadata.source_format = file_path.suffix.lower()

        resume.metadata.raw_text = (
            raw_text if self.settings.parser.preserve_source_text else None
        )

        return ResumeAnalysis(
            resume=resume,
            confidence=confidence,
        )
