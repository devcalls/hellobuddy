import os
from typing import List
from app.services.job_search.llm_drivers import GroqDriver
from pypdf import PdfReader
from app.models.resume import ResumeMetadata
from app.prompts.resume import FILTER_PROMPT
from pydantic import ValidationError

RESUME_METADATA_FILE_NAME = "resume_metadata.json"

# ==========================================
# 2. PDF Extraction & LLM Parsing Service
# ==========================================
class ResumeParserEngine:
    def __init__(self, api_key: str = None):
        # Initializes the native Groq Client (picks up GROQ_API_KEY from environment if None)
        #self.client = Groq(api_key=api_key)
        # Using llama-3.3-70b-versatile for nuanced text analysis
        self.model_name = "openai/gpt-oss-20b"
        


    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Reads a local PDF file and extracts all raw text content safely."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Target resume PDF file not found at: {pdf_path}")
        
        print(f"[File System] Reading raw text layout from: {pdf_path}")
        reader = PdfReader(pdf_path)
        full_text = []
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text.append(text)
                
        return "\n".join(full_text)
    
    def read_resume_metadata_from_cache(self, cache_path_dir: str) -> ResumeMetadata:
        """Reads a pre-compiled ResumeMetadata JSON file from the local cache."""
        cache_path = os.path.join(cache_path_dir, RESUME_METADATA_FILE_NAME)
        if not os.path.exists(cache_path):
            raise FileNotFoundError(f"Resume metadata cache file not found at: {cache_path}")
        
        print(f"[Cache System] Loading cached resume metadata from: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            data = f.read()
        
        return ResumeMetadata.model_validate_json(data)

    def save_resume_metadata(self, metadata: ResumeMetadata, output_dir: str, output_filename: str = RESUME_METADATA_FILE_NAME):
        """
        Serializes a populated ResumeMetadata object and saves it 
        as a formatted JSON file to the local directory cache.
        """
        
        full_output_path = os.path.join(output_dir, output_filename)
        # 1. Ensure the target directory structure exists to prevent FileNotFoundError
        directory = os.path.dirname(full_output_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        # 2. Open the file layout and dump the structural JSON string
        # We use indent=4 to keep the generated file clean and human-readable on disk
        with open(full_output_path, "w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=4))
            
        print(f"[Cache System] Successfully stored anonymized profile cache at: {full_output_path}")

    def parse_resume_content(self, raw_text: str) -> ResumeMetadata:
        """Sends raw text to llm forcing response structural alignment via JSON Schema."""
        print(f"[LLM] Dispatching extraction sequence to {self.model_name}...")
        
        # 1. Generate the JSON schema dynamically from our Pydantic structure
        json_schema = ResumeMetadata.model_json_schema()
        
        try:
            driver = GroqDriver(self.model_name)
            resume_profile = driver.generate_structured_output(
                system_prompt = FILTER_PROMPT,
                user_prompt = raw_text,
                response_schema = ResumeMetadata # Pass the schema definition
            )
            print(resume_profile.total_years_experience)
            
        except ValidationError as e:
            # Triggers if the schema rules were violated (e.g. a string placed inside a float field)
            print(f"[Schema Invalidation Error]: {e.json()}")
            # Fallback default instantiation or raising to caller service
            raise e
            
        except Exception as e:
            print(f"Generic parsing error: {e}")
            raise e
       
        return resume_profile


# ==========================================
# 3. CLI Operational Runner
# ==========================================
if __name__ == "__main__":
    # Make sure you have set your export GROQ_API_KEY="gsk_..." in your terminal
    SAMPLE_PDF_PATH = "";#ConfigManager().get_value("STORAGE", "RESUME_FILE_PATH")  # Validates presence of the key
    
    
    # Simple boilerplate setup to test the script stand-alone
    try:
        parser = ResumeParserEngine()
        
        # Step 1: Read the File
        raw_text = parser.extract_text_from_pdf(SAMPLE_PDF_PATH)
        print(raw_text)
     
       

    except Exception as e:
        print(f"\n[Parser Failure] Encountered exception: {e}")
        
        
def test():
     # Step 2: Query the LLM
        structured_profile = parser.parse_resume_content(raw_text)
        
        # Step 3: Print result summary out to the console
        print("\n==========================================")
        print("     SUCCESSFULLY PARSED METADATA         ")
        print("==========================================")
        print(f"Name:       {structured_profile.name}")
        print(f"Experience: {structured_profile.total_years_experience} Years")
        print(f"Roles:      {', '.join(structured_profile.primary_roles)}")
        print(f"Skills:     {', '.join(structured_profile.skills)}")
        
        # Note: You can easily save this directly into your file caching loop now:
        # print(structured_profile.model_dump_json(indent=4))