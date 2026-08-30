import os
import json
from app.services.job_search.resume_parser import ResumeParserEngine
#from config.config import ConfigManager
from app.config.job_settings import JobSearchSettings
from typing import List, Optional
from app.models.job import JobPosting
from app.models.resume import ResumeMetadata


class JobFilterService:
    def __init__(self, settings: JobSearchSettings):
        #self.config_manager = ConfigManager()
        self.settings = settings
        self.resume_parser = ResumeParserEngine()
    

    def resolve_resume_metadata(self) -> ResumeMetadata:
        """
        Resolves the user resume structure based on the configured environment flags.
        Handles checking, reading from cache, or forcing fresh generation dynamically.
        """
        extract_flag = 'Y'
        #cache_path = self.config_manager.get_value("STORAGE", "RESUME_METADATA_CACHE_PATH")
        #source_path = self.config_manager.get_value("STORAGE", "RESUME_FILE_PATH")
        
        cache_path = self.settings.storage.app_data_path
        source_path = self.settings.storage.resume_file_path

        # BRANCH N: Load directly from existing json cache layout
        if extract_flag == "N":
            return self.resume_parser.read_resume_metadata_from_cache(cache_path)
        else:
            print(f"[Warning] Cache file requested but not found at {cache_path}. Falling back to source extraction.")

        # BRANCH Y: Parse from scratch and save to the cache directory
        if not source_path or not os.path.exists(source_path):
            raise FileNotFoundError(f"Source resume PDF file not found at: {source_path}")

        # Execute extraction logic
        resume_raw_text = self.resume_parser.extract_text_from_pdf(source_path)
        resume_metadata = self.resume_parser.parse_resume_content(resume_raw_text)
        self.resume_parser.save_resume_metadata(resume_metadata, cache_path)
       
        return resume_metadata

    def filter_jobs(self, raw_job_pool: List[JobPosting]) -> List[JobPosting]:
        """
        Main pipeline method. Evaluates raw candidate jobs against exclusions 
        and hard candidate profiling attributes.
        """
        # Resolve the baseline resume state
        resume_md = self.resolve_resume_metadata()

        # Load standard exclusion lists from config
        banned_industries = self._parse_list_from_config("EXCLUSIONS", "banned_industries")
        banned_types = self._parse_list_from_config("EXCLUSIONS", "banned_company_types")
        
        filtered_pool = []

        print(f"\n--- Initiating Filter Pipeline on {len(raw_job_pool)} Job Entries ---")
        
        for job in raw_job_pool:
            # 1. Evaluate Explicit Industry Exclusion
            if job.industry.lower().strip() in banned_industries:
                print(f" -> Skipped [Job ID {job.job_id}]: Industry '{job.industry}' is explicitly banned.")
                continue

            # 2. Evaluate Explicit Company Type Exclusion (Sub-string check fallback)
            is_type_banned = False
            for banned_type in banned_types:
                if banned_type in job.company_type.lower():
                    is_type_banned = True
                    break
            if is_type_banned:
                print(f" -> Skipped [Job ID {job.job_id}]: Company type '{job.company_type}' matches banned criteria.")
                continue

            # 3. Evaluate Hard Constraint: Experience Levels
            # Filters out options if candidate's experience is strictly insufficient 
            if job.required_years_experience > resume_md.total_years_experience:
                print(f" -> Skipped [Job ID {job.job_id}]: Experience mismatch. Required: {job.required_years_experience}y, Candidate has: {resume_md.total_years_experience}y.")
                continue

            # If it passes all criteria gates, append it to the active pool
            filtered_pool.append(job)

        print(f"Pipeline Completed: {len(filtered_pool)} / {len(raw_job_pool)} items passed the criteria gates.\n")
        return filtered_pool