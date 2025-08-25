import os, json
from dotenv import load_dotenv

# Load .env
load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
MAX_CONTEXT_HISTORY = 5

# Load Annoy index + embeddings
VECTOR_DIM = 384
ANNOY_INDEX_PATH = "vector_store/annoy_st_index.ann"
DOC_MAPPING_PATH = "data/doc_mapping.json"
FEEDBACK_LOG_PATH = "data/rlhf_feedback_log.jsonl"
