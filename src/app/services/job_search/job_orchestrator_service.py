from app.services.job_search.job_scraping_service import JobScrapingService

# from config.config import ConfigManager
from app.config.job_settings import JobSearchSettings
from app.services.job_search.email_service import EmailService
from app.services.job_search.scheduler import setup_scheduler
from datetime import datetime
from pathlib import Path
import glob
import os
import asyncio
from typing import List
from app.util.file_handler import (
    read_json_from_file,
    write_json_list_to_file,
    get_absolute_path,
    create_folder,
)
from app.services.job_search.job_filter_service import JobFilterService
from app.services.job_search.job_search_engine import JobSearchEngine
from app.services.job_search.job_search_provider_factory import JobSearchProviderFactory
from app.services.job_search.job_history import LocalJobHistory
from app.models.job import JobPosting, JobSearch

RAW_JOB_POOL_FILENAME = "raw_job_pool.json"
REPORT_FOLDER = "reports"


class JobOrchestratorService:
    def __init__(self, settings: JobSearchSettings):
        # self.config_manager = ConfigManager()
        self.settings = settings
        self.job_scraping_service = JobScrapingService(settings)
        self.email_service = EmailService(settings)
        jobs_provider_factory = JobSearchProviderFactory(settings)
        self.active_providers = jobs_provider_factory.get_active_providers()
        # Initialize job history
        # file_path = self.config_manager.get_value("STORAGE", "APP_DATA_PATH")
        file_path = self.settings.storage.app_data_path
        file_path = os.path.join(file_path, "history")
        job_history = LocalJobHistory(history_file_path=file_path)
        job_history = LocalJobHistory(history_file_path=file_path)
        self.search_engine = JobSearchEngine(
            providers=self.active_providers, job_history=job_history
        )
        create_folder(self.settings.storage.app_data_path, REPORT_FOLDER)
        self.report_path = get_absolute_path(
            os.path.join(self.settings.storage.app_data_path, REPORT_FOLDER)
        )

    async def orchestrate(self):

        query = self.settings.search_settings.search_query
        location = self.settings.search_settings.search_location
        country = self.settings.search_settings.search_country

        query_params = {
            "search_query": query,
            "search_query_adzuna": self.settings.search_settings.search_query_adzuna,
            "search_query_reed": self.settings.search_settings.search_query_reed,
            "search_query_serp": self.settings.search_settings.search_query_serp,
        }

        result_params = {"num_pages": self.settings.search_settings.num_pages}

        job_search = JobSearch(
            query_params=query_params,
            result_params=result_params,
            location=location,
            country=country,
        )

        jobs = await self.search_jobs(job_search)
        self.send_email(jobs)

    def get_job_search_chips(self, target_folder):
        # Check if the folder contains any markdown (.md) files
        # recursive=False looks only inside the immediate folder
        md_files = glob.glob(os.path.join(target_folder, "*.md"))

        if not md_files:
            print("No .md files found. Setting date filter to: PAST MONTH")
            return "all"
        else:
            print(f"Found {len(md_files)} .md file(s). Setting date filter to: TODAY")
            return "today"

    def filter_jobs(self):
        job_filter_service = JobFilterService()

        raw_job_pool_path = os.path.join(self.report_path, RAW_JOB_POOL_FILENAME)
        if not os.path.exists(raw_job_pool_path):
            raise FileNotFoundError(
                f"Raw job pool file not found at: {raw_job_pool_path}"
            )
        raw_job_pool = read_json_from_file(raw_job_pool_path)
        job_filter_service.filter_jobs(raw_job_pool)

    def append_timestamp_to_filepath(
        self, base_directory: str, base_filename: str, extension: str
    ) -> Path:
        """
        Appends a safe ISO-like datetime string suffix to a filename
        and resolves it into an absolute cross-platform Path.
        """
        # 1. Generate a filename-safe timestamp (e.g., "2026-07-02_16-35-12")
        # Using underscores and hyphens ensures Windows, macOS, and Linux compatibility
        timestamp_suffix = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # 2. Combine the original filename string with the suffix
        final_filename = f"{base_filename}_{timestamp_suffix}{extension}"

        # 3. Use pathlib to securely anchor it to the target folder path
        absolute_path = Path(base_directory).resolve() / final_filename

        return absolute_path

    async def search_jobs(self, job_search: JobSearch) -> List[JobPosting]:

        date_posted = self.get_job_search_chips(self.report_path)
        job_search.result_params["date_posted"] = date_posted

        jobs = await self.search_engine.search_all(job_search)
        return jobs

    def send_email(self, extracted_jobs: List[JobPosting]):
        write_json_list_to_file(
            extracted_jobs, os.path.join(self.report_path, RAW_JOB_POOL_FILENAME)
        )
        file_prefix = "job_matches"
        file_ext = ".md"

        # Execute the resolution
        resolved_file = self.append_timestamp_to_filepath(
            self.report_path, file_prefix, file_ext
        )
        md_content = None
        if len(extracted_jobs) > 0:
            md_content = self.job_scraping_service.save_job_list_to_markdown(
                extracted_jobs, resolved_file
            )
        else:
            print("No jobs found matching criteria.")
            md_content = "# No job matches found for the given criteria."

        html_body = self.job_scraping_service.convert_md_file_to_html_body(md_content)
        self.email_service.background_send_email_task(
            self.settings.email.recipient, "Job Match Alert from Hello Buddy", html_body
        )

    def extract_jobs_send_email(self, query: str, location: str, search_country: str):

        num_pages = self.settings.search_settings.num_pages
        date_posted = self.get_job_search_chips(
            self.report_path
        )  # Determine the date filter based on existing .md files

        extracted_jobs = self.job_scraping_service.search_jobs_with_sdk(
            query,
            location,
            num_pages=num_pages,
            date_posted=date_posted,
            country=search_country,
        )

        write_json_list_to_file(
            extracted_jobs, os.path.join(self.report_path, RAW_JOB_POOL_FILENAME)
        )
        file_prefix = "job_matches"
        file_ext = ".md"

        # Execute the resolution
        resolved_file = self.append_timestamp_to_filepath(
            self.report_path, file_prefix, file_ext
        )
        md_content = None
        if len(extracted_jobs) > 0:
            md_content = self.job_scraping_service.save_job_list_to_markdown(
                extracted_jobs, resolved_file
            )
        else:
            print("No jobs found matching criteria.")
            md_content = "# No job matches found for the given criteria."

        html_body = self.job_scraping_service.convert_md_file_to_html_body(md_content)
        self.email_service.background_send_email_task(
            self.settings.email.recipient, "Job Match Alert from Hello Buddy", html_body
        )


def extract_jobs_send_email(settings: JobSearchSettings):

    query = settings.search_settings.search_query
    location = settings.search_settings.search_location
    country = settings.search_settings.search_country
    job_orchestrator = JobOrchestratorService(settings)
    # job_orchestrator.extract_jobs_send_email(query, location, country)
    job_orchestrator.filter_jobs()


def orchestrate(settings: JobSearchSettings):

    job_orchestrator = JobOrchestratorService(settings)
    asyncio.run(job_orchestrator.orchestrate())
