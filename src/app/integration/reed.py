import httpx
from app.integration.job_provider import BaseJobProvider
from app.models.job import JobPosting, JobSearch
from typing import List


class ReedProvider(BaseJobProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.reed.co.uk/api/1.0/search"

    @property
    def name(self) -> str:
        return "Reed"

    async def search(self, job_search: JobSearch) -> List[JobPosting]:
        query = self.get_query_by_provider(job_search.query_params, self.name)
        query_strings = self.parse_query(query)

        jobs = []
        for search_term in query_strings:
            print(
                f"[Engine] Executing search for batch segment for provider: {self.name} : '{search_term}'..."
            )
            job_results = await self.search_internal(job_search, search_term)
            jobs.extend(job_results)
        return jobs

    async def search_internal(
        self, job_search: JobSearch, query_string: str
    ) -> List[JobPosting]:
        params = {"keywords": query_string, "locationName": job_search.location}
        # Reed uses standard HTTP Basic Auth, passing the API key as the username
        auth = (self.api_key, "")

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params, auth=auth)
            if response.status_code != 200:
                return []

            data = response.json()
            print("Reed API Integration")  # Debugging line to inspect the API response
            results = []
            for job in data.get("results", []):
                results.append(
                    JobPosting(
                        job_id=str(job.get("jobId", "")),
                        title=job.get("jobTitle", ""),
                        company=job.get("employerName", "Unknown"),
                        expiration_date=job.get("expirationDate", ""),
                        location=job.get("location", {}).get("display_name", "UK"),
                        via="reed",
                        # salary=f"£{job.get('salary_min', '')} - £{job.get('salary_max', '')}" if job.get('salary_min') else "Not specified",
                        apply_link=job.get("jobUrl", ""),
                        description=job.get("jobDescription", ""),
                        provider_name=self.name,
                    )
                )
            return results
