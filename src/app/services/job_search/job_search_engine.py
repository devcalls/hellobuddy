import asyncio
from typing import List, Dict, Any

from app.integration.job_provider import BaseJobProvider
from app.models.job import JobPosting, JobSearch
from app.integration.adzuna import AdzunaProvider
from app.services.job_search.job_history import LocalJobHistory


class JobSearchEngine:
    def __init__(self, providers: List[BaseJobProvider], job_history: LocalJobHistory):
        self.providers = providers
        self.job_history = job_history

    async def search_all_concurrent(
        self, query: str, location: str
    ) -> List[JobPosting]:
        # Run all provider searches concurrently
        tasks = [provider.search(query, location) for provider in self.providers]
        tasks_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs = []
        for result in tasks_results:
            if isinstance(result, list):
                all_jobs.extend(result)
            else:
                # Log or handle provider failures gracefully without crashing the whole CLI
                print(f"[Warning] A provider failed to fetch results: {result}")

        return all_jobs

    async def search_all(self, job_search: JobSearch) -> List[JobPosting]:
        """
        Searches across all providers
        """
        unique_jobs = {}

        # Run all configured provider connections concurrently *for this specific term*
        tasks = [provider.search(job_search) for provider in self.providers]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate and deduplicate the batch chunk
        for current_results in completed_tasks:
            if isinstance(current_results, list):
                for job in current_results:
                    key = job.job_id + job.provider_name
                    if key not in unique_jobs:
                        unique_jobs[key] = job
            else:
                # Logs individual provider failure trace gracefully without breaking the chain
                print(
                    f"[Warning] Provider interface connection error encountered: {current_results}"
                )

        new_jobs = list(unique_jobs.values())
        # Filter out jobs that are already in the history
        new_jobs = self.job_history.filter_and_commit_new_jobs(new_jobs)
        return new_jobs
