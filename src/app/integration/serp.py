import httpx
from app.integration.job_provider import BaseJobProvider
from app.models.job import JobPosting, JobSearch
from typing import List
import serpapi

class SerpProvider(BaseJobProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        

    @property
    def name(self) -> str:
        return "Serp"
    
    async def search(self, job_search: JobSearch) -> List[JobPosting]:
        query = self.get_query_by_provider(job_search.query_params, self.name)
        query_strings = self.parse_query(query)
            
        jobs = []
        for search_term in query_strings:
            print(f"[Engine] Executing search for batch segment for provider: {self.name} : '{search_term}'...")
            job_results = await self.search_internal(job_search, search_term)
            jobs.extend(job_results)
        return jobs

    async def search_internal(self, job_search: JobSearch, query_string: str) -> List[JobPosting]:
        location = job_search.location
        print(f"--- Fetching Jobs via SerpApi SDK for: '{query_string}' in '{location}' ---")
        client = serpapi.Client(api_key = self.api_key)
        num_pages = job_search.result_params.get("num_pages")
        date_posted = job_search.result_params.get("date_posted")
        country = job_search.country
        print(f"num_pages in Serp Provider: {num_pages}" )
        # Configure parameters explicitly for Google Jobs engine
        # 1. Inject the "remote" constraint explicitly into the keyword query
        params = {
            "engine": "google_jobs",
            "q": query_string, # Added remote here
            "location": location,                  # Use a valid geographic region
            "chips": f"date_posted:{date_posted}",            # Use the date_posted parameter
            "hl": "en",
            "gl": country
        }
        if date_posted == "all":
            params.pop("chips")  # Remove the date_posted filter if "all" is specified
        print(params)
        
        try:
            all_results = []
            total_desired = num_pages * 10
            results = client.search(params)
            for page in results.yield_pages(max_pages = num_pages):
                organic_results = page.get("jobs_results", [])
                all_results.extend(organic_results)
                
                if len(all_results) >= total_desired:
                    break
            
            if not all_results:
                print("No jobs found matching criteria.")
                return []
                
            print(f"Found {len(all_results)} jobs successfully.\n")
            
            extracted_jobs = []
            for index, job in enumerate(all_results, 1):
                job_data = {
                    "title": job.get("title"),
                    "company": job.get("company_name"),
                    "location": job.get("location"),
                    # This full description text is exactly what you pass to LangChain for skill parsing:
                    "description": job.get("description"), 
                    "via": job.get("via"), # e.g. "via LinkedIn", "via Indeed"
                    "apply_link": job.get("share_link"), # Share/Apply redirect link,
                    "job_id": job.get("job_id"),
                    "provider_name": self.name
                }
                # Look inside SerpApi's parsed response for the item loop:
                apply_options = job.get("apply_options", [])
                direct_apply_link = "";
                if apply_options:
                    # Option A: Grab the absolute first apply link available
                    direct_apply_link = apply_options[0].get("link")
                    
                    # Option B: Or loop through them to find an explicit target (like LinkedIn)
                    for option in apply_options:
                        if "linkedin" in option.get("title", "").lower():
                            direct_apply_link = option.get("link")
                            break
                else:
                    # Fallback to the share link if no deep apply array metadata was exposed
                    direct_apply_link = job.get("share_link")
                
                job_data['apply_link'] = direct_apply_link
                job_obj = JobPosting.model_validate(job_data)
                extracted_jobs.append(job_obj)
                
                # Print quick console preview summary
                #print(f"[{index}] {job_data['title']} at {job_data['company']} ({job_data['via']})")
                #print(f"    Snippet: {job_data['description'][:120]}...\n")
                
            return extracted_jobs

        except serpapi.HTTPError as e:
            print(f"SerpApi HTTP Error occurred: {e.status_code} - {e.error}")
        except Exception as e:
            print(f"Unexpected error: {e}")