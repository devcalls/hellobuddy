import os
import json
from typing import List, Dict, Set
from app.models.job import JobPosting 
from app.util.file_handler import read_json_from_file, write_json_list_to_file

class LocalJobHistory:
    def __init__(self, history_file_path: str, history_filename: str = "job_history.json"):
        self.history_file_path = history_file_path
        self.history_file_name = history_filename
        self.filename = os.path.join(history_file_path, history_filename)
        

    def filter_and_commit_new_jobs(self, incoming_jobs: List[JobPosting]) -> List[JobPosting]:
        # 1. Read existing data and convert to a lookup set of tuples: {("id", "provider")}
        # Tuples allow lightning-fast O(1) hash lookups instead of looping over a list
        seen_pairs: Set[tuple] = set()
        existing_data = []
        try:
            historical_data = read_json_from_file(self.filename)
        except FileNotFoundError:
            historical_data = []
            
        for item in historical_data:
                seen_pairs.add((str(item.get("job_id")), item.get("provider")))

        new_jobs: List[JobPosting] = []
        new_records_to_append = []

        # 2. Check incoming items
        for job in incoming_jobs:
            if not job.job_id:
                continue
                
            job_id_str = str(job.job_id)
            pair = (job_id_str, job.provider_name)
            
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                new_jobs.append(job)
                # Prepare payload match for the file structure
                new_records_to_append.append({
                    "job_id": job_id_str,
                    "provider": job.provider_name
                })

        # 3. If new elements exist, merge lists and write out
        if new_records_to_append:
            all_data = historical_data + new_records_to_append
            write_json_list_to_file(all_data, self.history_file_path, self.history_file_name)

        return new_jobs