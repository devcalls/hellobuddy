import os
import json
import os
import markdown
#from config.config import ConfigManager
from app.config.job_settings import JobSearchSettings
from app.models.job import JobPosting
from typing import List

class JobScrapingService:
    def __init__(self, settings: JobSearchSettings):
        #self.config_manager = ConfigManager()
        self.settings = settings
        #self.api_key = self.config_manager.get_value("API_KEYS", "SERPAPI_KEY")
        self.api_key = self.settings.api_keys.serp_api_key


    # --- Advanced Version: Handling a LIST of multiple jobs ---
    def save_job_list_to_markdown(self, jobs_list: list, filepath: str = "all_job_matches.md"):
        """
        Takes a list of job dictionaries and creates a comprehensive report
        complete with a summary overview table at the top.
        """
        if not jobs_list:
            print("No jobs provided to save.")
            return

        # Create the top summary table header
        md_content = "# 🚀 Hellobuddy Job Match Report\n\n"
        md_content += "| Position | Company | Location | Platform | Provider |\n"
        md_content += "| :--- | :--- | :--- | :--- | :--- |\n"
        jobs: List[JobPosting] = jobs_list
        # Populate the summary table rows
        for job in jobs:
            title = job.title
            company = job.company
            location = job.location
            via = job.via if job.via else "NA"
            apply = job.apply_link if job.apply_link else "#"
            provider = job.provider_name
            
            md_content += f"| [{title}]({apply}) | **{company}** | {location} | *{via}* | {provider} |\n"
            
        md_content += "\n\n---\n\n"
        
        # Append the detailed descriptions below the table
        for idx, job in enumerate(jobs, 1):
            link = job.apply_link if job.apply_link else "#"
            md_content += f"## {idx}. {job.title} at {job.company}\n"
            md_content += f"> 📍 **Location:** {job.location} | 🌐 **Source:** {job.via} | 🔗 [Apply Direct]({link})\n\n"
            md_content += f"### Description\n{job.description}\n\n"
            md_content += "...\n\n"

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(md_content)
        print(f"Full report with {len(jobs_list)} jobs compiled at {filepath}")
        return md_content


    def convert_md_file_to_html_body(self, md_content: str) -> str:
        """Converts markdown content to converted HTML into a responsive styling wrapper."""
            
        # Convert native markdown syntax to HTML string layout
        html_content = markdown.markdown(md_content, extensions=['tables'])
        
        # Wrap the raw HTML inside a clean, modern responsive email wrapper
        # styled_email_html = f"""
        # <!DOCTYPE html>
        # <html>
        # <head>
        #     <style>
        #         body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        #         h1 {{ color: #1e293b; font-size: 24px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }}
        #         h2 {{ color: #334155; font-size: 20px; margin-top: 24px; }}
        #         h3 {{ color: #475569; font-size: 16px; }}
        #         a {{ color: #2563eb; text-decoration: none; font-weight: bold; }}
        #         a:hover {{ text-decoration: underline; }}
        #         table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
        #         th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: left; }}
        #         th {{ background-color: #f8fafc; font-weight: 600; color: #1e293b; }}
        #         blockquote {{ margin: 16px 0; padding: 4px 16px; border-left: 4px solid #3b82f6; background-color: #f0fdf4; color: #1e293b; font-style: italic; }}
        #         hr {{ border: 0; height: 1px; background: #e2e8f0; margin: 24px 0; }}
        #     </style>
        # </head>
        # <body>
        #     {html_content}
        #     <hr />
        #     <p style="font-size: 12px; color: #64748b; text-align: center;">Sent automatically by your Hellobuddy AI Agent.</p>
        # </body>
        # </html>
        # """
        
        styled_email_html = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                            max-width: 1200px;
                            margin: 0 auto;
                            padding: 20px;
                            background-color: #f9f9f9;
                        }}
                        h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
                        h2 {{ color: #202124; margin-top: 40px; }}
                        h3 {{ color: #5f6368; }}
                        
                        /* Responsive Grid Table Layout Styling */
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin: 25px 0;
                            font-size: 0.95em;
                            box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
                            background: #fff;
                            border-radius: 8px;
                            overflow: hidden;
                        }}
                        th {{
                            background-color: #1a73e8;
                            color: #ffffff;
                            text-align: left;
                            font-weight: bold;
                            padding: 12px 15px;
                        }}
                        td {{
                            padding: 12px 15px;
                            border-bottom: 1px solid #dddddd;
                        }}
                        tr:nth-of-type(even) {{
                            background-color: #f3f3f3;
                        }}
                        tr:last-of-type {{
                            border-bottom: 2px solid #1a73e8;
                        }}
                        a {{
                            color: #1a73e8;
                            text-decoration: none;
                        }}
                        a:hover {{
                            text-decoration: underline;
                        }}
                        blockquote {{
                            background: #f1f3f4;
                            border-left: 4px solid #1a73e8;
                            margin: 1.5em 10px;
                            padding: 0.5em 10px;
                            border-radius: 0 4px 4px 0;
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
        return styled_email_html

