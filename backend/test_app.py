from fastapi import FastAPI
from pydantic import BaseModel
from backend.agents.ingestion_agent import IngestionAgent
from backend.agents.summary_agent import SummaryAgent
from backend.agents.faq_agent import FAQAgent
from backend.agents.rag_agent import RAGAgent


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
    agent = SummaryAgent()
    agent.run()
    return {"status": "success", "message": "Summaries generated"}

@app.post("/faqs")
def generate_faqs():
    agent = FAQAgent()
    agent.run()
    return {"status": "success", "message": "FAQs generated"}


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
