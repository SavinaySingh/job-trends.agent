import os, json
from dotenv import load_dotenv

# Load .env
load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# File paths
ANNOY_INDEX_PATH = "annoy_st_index.ann"
DOC_MAPPING_PATH = "doc_mapping.json"
FEEDBACK_LOG_PATH = "rlhf_feedback_log.jsonl"
