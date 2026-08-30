from app.integration.reed import ReedProvider
from app.integration.adzuna import AdzunaProvider
from app.integration.serp import SerpProvider
#from config.config import ConfigManager
from app.config.job_settings import JobSearchSettings

class JobSearchProviderFactory():
    def __init__(self, settings: JobSearchSettings):
        #self.config_manager = config_manager
        self.settings = settings
    
    def get_active_providers(self):
        active_providers = []
        if self.settings.api_keys.adzuna_app_id is not None and self.settings.api_keys.adzuna_app_key is not None: 
            active_providers.append(AdzunaProvider(self.settings.api_keys.adzuna_app_id, self.settings.api_keys.adzuna_app_key))
            
        if self.settings.api_keys.reed_api_key is not None:
            active_providers.append(ReedProvider(self.settings.api_keys.reed_api_key))
            
        if self.settings.api_keys.serp_api_key is not None:
            active_providers.append(SerpProvider(self.settings.api_keys.serp_api_key))
            
        return active_providers
            
        