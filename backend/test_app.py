from fastapi import FastAPI
from pydantic import BaseModel
from backend.agents.ingestion_agent import IngestionAgent

app = FastAPI(title="FastAPI Knowledge Assistant")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running"}

@app.post("/ingest")
def ingest_docs():
    agent = IngestionAgent()
    agent.run()
    return {"status": "success", "message": "FastAPI docs ingested into ChromaDB"}
@app.post("/summarize")
def summarize_docs():
    return {"status": "pending", "message": "SummaryAgent not wired yet"}

@app.post("/faqs")
def generate_faqs():
    return {"status": "pending", "message": "FAQAgent not wired yet"}

class AskRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_question(payload: AskRequest):
    return {
        "status": "pending",
        "question": payload.question,
        "message": "RAGAgent not wired yet"
    }
