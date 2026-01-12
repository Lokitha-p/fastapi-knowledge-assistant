import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

print(f"🔧 Loading .env from: {env_path}")
print(f"🔧 .env file exists: {env_path.exists()}")

FASTAPI_DOC_URLS = [
    "https://fastapi.tiangolo.com/tutorial/first-steps/",
    "https://fastapi.tiangolo.com/tutorial/path-params/",
    "https://fastapi.tiangolo.com/tutorial/query-params/",
    "https://fastapi.tiangolo.com/tutorial/body/",
    "https://fastapi.tiangolo.com/tutorial/response-model/",
    "https://fastapi.tiangolo.com/tutorial/request-files/",
    "https://fastapi.tiangolo.com/tutorial/dependencies/",
    "https://fastapi.tiangolo.com/tutorial/security/",
    "https://fastapi.tiangolo.com/tutorial/middleware/",
    "https://fastapi.tiangolo.com/tutorial/background-tasks/",
]

CHROMA_DB_PATH = "backend/data/chroma_db"

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
LLM_MODEL = "arcee-ai/trinity-mini:free"

print(f"🔧 OPENROUTER_API_KEY loaded: {OPENROUTER_API_KEY[:40] if OPENROUTER_API_KEY else 'NOT FOUND'}...")
print(f"🔧 API Base: {OPENROUTER_API_BASE}")
print(f"🔧 Model: {LLM_MODEL}")

# Use Mock LLM for testing (no API key needed)
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
