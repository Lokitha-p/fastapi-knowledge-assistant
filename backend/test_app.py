from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import os
from typing import List, Optional
from PyPDF2 import PdfReader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.agents.ingestion_agent import IngestionAgent
from backend.agents.summary_agent import SummaryAgent
from backend.agents.faq_agent import FAQAgent
from backend.agents.rag_agent import RAGAgent
from backend.core.llm import get_llm


app = FastAPI(title="FastAPI Knowledge Assistant")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the 'data' directory
app.mount("/data", StaticFiles(directory="backend/data"), name="data")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running"}

@app.post("/ingest")
def ingest_docs(
    urls: Optional[List[str]] = Form(None),
    pdf_files: Optional[List[UploadFile]] = None,
    html_files: Optional[List[UploadFile]] = None,
    raw_texts: Optional[List[str]] = Form(None),
):
    """
    Enhanced ingestion endpoint to handle multiple input types:
    - URLs: Scrape and store content.
    - PDF files: Extract and store text.
    - HTML files: Extract and store content.
    - Raw texts: Directly store provided text.
    """
    agent = IngestionAgent()

    if urls:
        for url in urls:
            agent.ingest_url(url)

    if pdf_files:
        for pdf in pdf_files:
            pdf_reader = PdfReader(pdf.file)
            text = "\n".join(page.extract_text() for page in pdf_reader.pages)
            agent.ingest_text(text, source=pdf.filename)

    if html_files:
        for html in html_files:
            content = html.file.read().decode("utf-8")
            agent.ingest_text(content, source=html.filename)

    if raw_texts:
        for text in raw_texts:
            agent.ingest_text(text, source="raw_input")

    return {"status": "success", "message": "Data ingested successfully."}

@app.post("/summarize")
def summarize_docs():
    agent = SummaryAgent()
    agent.run()
    return {"status": "success", "message": "Summaries generated"}


class FAQRequest(BaseModel):
    custom_topics: list[str] | None = None


@app.post("/faqs")
def generate_faqs(payload: FAQRequest = None):
    agent = FAQAgent()
    custom_topics = payload.custom_topics if payload else None
    result = agent.run(custom_topics=custom_topics)
    return {
        "status": "success",
        "message": "FAQs generated",
        "data": result
    }


class AskRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_question(payload: AskRequest):
    try:
        agent = RAGAgent()
        result = agent.run(payload.question)
        return {
            "status": "success",
            "question": result["question"],
            "answer": result["answer"]
        }
    except Exception as e:
        return {
            "status": "error",
            "question": payload.question,
            "error": str(e)
        }


@app.post("/test-llm")
def test_llm_connection():
    """
    Test endpoint to verify OpenRouter API connection with minimal token usage.
    Returns the LLM response to a simple prompt.
    """
    try:
        # Get the LLM instance
        llm = get_llm()

        # Simple test prompt (uses minimal tokens)
        test_prompt = "Say 'API Working' if you can read this."

        # Call the LLM
        response = llm(test_prompt)

        return {
            "status": "success",
            "message": "OpenRouter API is working correctly",
            "llm_response": response,
            "api_key_prefix": os.getenv("OPENROUTER_API_KEY", "")[:20] + "...",
            "model": os.getenv("LLM_MODEL", "arcee-ai/trinity-mini:free"),
            "using_mock": os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "api_key_prefix": os.getenv("OPENROUTER_API_KEY", "")[:20] + "...",
            "model": os.getenv("LLM_MODEL", "arcee-ai/trinity-mini:free"),
            "using_mock": os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        }

@app.get("/get-data")
def get_data():
    """
    Endpoint to retrieve all data stored in the ChromaDB collection.
    Returns the documents, metadata, and other details.
    """
    try:
        # Initialize the ChromaDB client and collection
        from backend.core.vectorstore import get_chroma_client
        from backend.config.settings import CHROMA_DB_PATH

        client = get_chroma_client(CHROMA_DB_PATH)
        collection = client.get_or_create_collection(name="fastapi_docs")

        # Fetch all data from the collection
        data = collection.get()

        return {
            "status": "success",
            "message": "Data retrieved successfully.",
            "data": {
                "documents": data["documents"],
                "metadatas": data["metadatas"],
                "ids": data["ids"],
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
