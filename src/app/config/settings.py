import sys
import configparser
from pathlib import Path
from typing import Any, Dict, Type, Optional, ClassVar
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, InitSettingsSource, PydanticBaseSettingsSource
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator
from pydantic import ValidationError

# A reusable type that converts empty strings ("") from the INI file into None
BlankToNone = Annotated[Optional[str], BeforeValidator(lambda v: None if v == "" else v)]

# Capture the exact directory where *this* script file lives
current_dir = Path(__file__).resolve().parent

# 1. Custom INI Source Parser
class IniConfigSettingsSource(PydanticBaseSettingsSource):
    def __init__(self, settings_cls: Type[BaseSettings], ini_file_path: str):
        super().__init__(settings_cls)
        # Store just the filename string so we can combine it with our dynamic root path
        self.config_filename = ini_file_path

    def get_field_value(self, field_name: str, field_title: str, file_content: Any = None) -> Any:
        pass
    
    def read_config(self) -> configparser.ConfigParser:
        # Walk up the directory tree until we find the parent folder that contains the 'src' directory.
        # If this file lives inside 'src/config/settings.py', it will look at 'src/config' (no 'src' folder inside),
        # then move up to your project root (which *does* contain the 'src' folder).
        root_dir = current_dir
        if (current_dir / 'src').is_dir():
            root_dir = current_dir
        else:
            for parent in current_dir.parents:
                if (parent / 'src').is_dir():
                    root_dir = parent
                    break
        
        # Target your config file at the project root level
        config_path = root_dir / self.config_filename
        
        print(f"🔎 Looking for config at: {config_path}")
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file missing at: {config_path.absolute()}")
            
        print('📖 Reading config file...')
        config = configparser.ConfigParser()
        config.read(config_path)
        return config

    def __call__(self) -> Dict[str, Any]:
        # Let read_config locate the file and handle it
        config = self.read_config()
        
        settings_dict: Dict[str, Any] = {}
        for section in config.sections():
            # Nest everything under the section name in lowercase
            settings_dict[section.lower()] = dict(config.items(section))
                    
        return settings_dict


class BaseFeatureSettings(BaseSettings):
    """
    Base settings class. All feature settings must inherit from this.
    Child classes MUST define `INI_FILE_PATH`.
    """
    model_config = SettingsConfigDict(case_sensitive=False)
    INI_FILE_PATH: ClassVar[str] = "default.ini"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: InitSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        
        ini_file = getattr(settings_cls, "INI_FILE_PATH", "default.ini")
        return (
            init_settings,
            env_settings,
            IniConfigSettingsSource(settings_cls, ini_file_path=ini_file),
        )
