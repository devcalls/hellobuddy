from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel
from app.models.job import JobPosting, JobSearch

class BaseJobProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the identifier string for the provider."""
        pass

    @abstractmethod
    async def search(self, job_search: JobSearch) -> List[JobPosting]:
        """Queries the specific job board API and returns unified JobPosting items."""
        pass
    
    def get_query_by_provider(self, query_params: Dict, provider_name: str):
        # Target structure in lowercase for safe matching
        target_key = f"search_query_{provider_name.lower()}"
        
        for key, value in query_params.items():
            if key.lower() == target_key:
                if value is not None:
                    return value
        
        # Fallback, if provider specific search query is not set.
        target_key = f"search_query"
        
        for key, value in query_params.items():
            if key.lower() == target_key:
                return value
                
        return None
    
    def parse_query(self, query: str) -> List[str]:
        query_strings = None
        if ";" in query:
            query_strings = [q.strip() for q in query.split(";") if q.strip()]
        else:
            query_strings = [query.strip()]
        
        return query_strings