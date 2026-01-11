import json
import os

from backend.core.llm import get_llm
from backend.core.prompts import FAQ_PROMPT
from backend.core.vectorstore import get_chroma_client
from backend.config.settings import CHROMA_DB_PATH


class FAQAgent:
    def __init__(self):
        self.persist_path = CHROMA_DB_PATH
        self.client = get_chroma_client(self.persist_path)
        self.collection = self.client.get_collection("fastapi_docs")
        self.llm = get_llm()

        os.makedirs("backend/data", exist_ok=True)

    def run(self):
        print("❓ FAQAgent: Generating developer FAQs...")

        docs = self.collection.get(include=["documents"])
        context = " ".join(doc[:700] for doc in docs["documents"][:6])

        response = self.llm(
            FAQ_PROMPT + "\n" + context
        )[0]["generated_text"]

        faqs = []
        blocks = response.split("\n\n")

        for block in blocks:
            if "Question:" in block and "Answer:" in block:
                try:
                    q = block.split("Question:")[1].split("Answer:")[0].strip()
                    a = block.split("Answer:")[1].strip()
                    faqs.append({"question": q, "answer": a})
                except Exception:
                    continue

        if not faqs:
            faqs = [{
                "question": "FAQ extraction failed",
                "answer": response
            }]

        with open("backend/data/faqs.json", "w", encoding="utf-8") as f:
            json.dump(faqs, f, indent=2)

        print("✅ Generated developer FAQs!")
