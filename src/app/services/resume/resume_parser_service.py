from pathlib import Path

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
    ResumeMetadata,
    ResumeAST,
)

from app.services.resume.llm_resume_extractor import (
    LLMResumeExtractor,
)
from app.services.resume.resume_ast_builder import ( ResumeASTBuilder, )
from app.models.resume.confidence import ResumeAnalysis

class ResumeParserService:

    def __init__(
        self,
        settings,
        document_reader=None,
        llm_extractor=None,
        confidence_service=None,
    ):

        self.settings = settings

        self.document_reader = (
            document_reader
            or DocumentReader()
        )

        self.llm_extractor = (
            llm_extractor
            or LLMResumeExtractor(settings)
        )

        self.confidence_service = (
            confidence_service
            or ResumeConfidenceService()
        )

    def parse(
        self,
        file_path: str,
    )-> ResumeAnalysis:

        raw_text = self.document_reader.read(
            file_path
        )

        extracted_resume = self.llm_extractor.extract(
            raw_text
        )
        
        resume = ResumeASTBuilder().build(
            extraction=extracted_resume,
            source_text=raw_text,
            source_file=file_path,
            source_format=""
        )

        confidence = self.confidence_service.calculate(
            resume
        )
        

        resume.metadata.source_file = file_path

        resume.metadata.source_format = (
            Path(file_path).suffix.lower()
        )

        resume.metadata.raw_text = (
            raw_text
            if self.settings.parser.preserve_source_text
            else None
        )
        
        return ResumeAnalysis(
            resume=resume,
            confidence=confidence,
        )

        return resume