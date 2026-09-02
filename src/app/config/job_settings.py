from typing import Optional, ClassVar
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator

# Import the base class from your core config file
from app.config.settings import BaseFeatureSettings

BlankToNone = Annotated[
    Optional[str], BeforeValidator(lambda v: None if v == "" else v)
]


class StorageSettings(BaseModel):
    app_data_path: str
    resume_file_path: BlankToNone = Field(default=None)


class EmailSettings(BaseModel):
    recipient: str


class SchedulerSettings(BaseModel):
    schedule_time: str = Field(default=None)


class ApiKeysSettings(BaseModel):
    serp_api_key: BlankToNone = Field(default=None)
    mailtrap_api_token: str
    reed_api_key: BlankToNone = Field(default=None)
    adzuna_app_key: BlankToNone = Field(default=None)
    adzuna_app_id: BlankToNone = Field(default=None)


class SearchSettings(BaseModel):
    search_query_serp: BlankToNone = Field(default=None)
    search_query_reed: BlankToNone = Field(default=None)
    search_query_adzuna: BlankToNone = Field(default=None)
    search_query: str
    search_location: str
    search_country: str
    num_pages: int


class JobSearchSettings(BaseFeatureSettings):
    # Points to the specific INI file for this feature in the root folder
    INI_FILE_PATH: ClassVar[str] = "job_config.ini"

    storage: StorageSettings
    email: EmailSettings
    scheduler: SchedulerSettings
    api_keys: ApiKeysSettings
    search_settings: SearchSettings
