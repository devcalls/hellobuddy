import httpx
from app.integration.job_provider import BaseJobProvider
from app.models.job import JobPosting, JobSearch
from typing import List
import urllib.parse

class AdzunaProvider(BaseJobProvider):
    def __init__(self, app_id: str, app_key: str):
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://api.adzuna.com/v1/api/jobs/gb/search/1"

    @property
    def name(self) -> str:
        return "Adzuna"
    
    async def search(self, job_search: JobSearch) -> List[JobPosting]:
        query = self.get_query_by_provider(job_search.query_params, self.name)
        
        query_strings = self.parse_query(query)
        print(f"search term in adzuna {query_strings}") 
        jobs = []
        for search_term in query_strings:
            print(f"[Engine] Executing search for batch segment for provider: {self.name} : '{search_term}'...")
            job_results = await self.search_internal(job_search, search_term)
            jobs.extend(job_results)
        return jobs

    async def search_internal(self, job_search: JobSearch, query_string: str) -> List[JobPosting]:
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": urllib.parse.quote(query_string),
            "where": job_search.location,
            "content-type": "application/json",
            "results_per_page": 50
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            if response.status_code != 200:
                return []
                
            data = response.json()
            results = []
            print('Adzuna API Integration')  # Debugging line to inspect the API response
            for job in data.get("results", []):
                results.append(JobPosting(
                    job_id=str(job.get("jobId", "")),
                    title=job.get("jobTitle", ""),
                    company=job.get("employerName", "Unknown"),
                    expiration_date=job.get("expirationDate", ""),
                    location=job.get("location", {}).get("display_name", "UK"),
                    via="Adzuna",
                    #salary=f"£{job.get('salary_min', '')} - £{job.get('salary_max', '')}" if job.get('salary_min') else "Not specified",
                    apply_link=job.get("jobUrl", ""),
                    description=job.get("jobDescription", ""),
                    provider_name=self.name
                ))
            return results
