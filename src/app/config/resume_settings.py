from typing import Optional, ClassVar

from pydantic import BaseModel, Field
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator

from app.config.settings import BaseFeatureSettings
from app.config.llm import LLMSettings

BlankToNone = Annotated[
    Optional[str],
    BeforeValidator(lambda v: None if v == "" else v),
]


class StorageSettings(BaseModel):

    app_data_path: str

    resume_file_path: BlankToNone = Field(default=None)


class ApiKeysSettings(BaseModel):

    openai_api_key: BlankToNone = Field(default=None)


class ParserSettings(BaseModel):

    preserve_source_text: bool = True


class ResumeSettings(BaseFeatureSettings):

    INI_FILE_PATH: ClassVar[str] = "resume_config.ini"

    storage: StorageSettings

    llm: LLMSettings

    api_keys: ApiKeysSettings

    parser: ParserSettings
