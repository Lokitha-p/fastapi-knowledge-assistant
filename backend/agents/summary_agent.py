import json
import os

from backend.core.llm import get_llm
from backend.core.prompts import (
    EXECUTIVE_SUMMARY_PROMPT,
    SECTION_SUMMARY_PROMPT
)
from backend.core.vectorstore import get_chroma_client
from backend.config.settings import CHROMA_DB_PATH


class SummaryAgent:
    def __init__(self):
        self.persist_path = CHROMA_DB_PATH
        self.client = get_chroma_client(self.persist_path)
        self.collection = self.client.get_collection("fastapi_docs")
        self.llm = get_llm()

        os.makedirs("backend/data", exist_ok=True)

    def run(self):
        print("📝 SummaryAgent: Generating summaries...")

        docs = self.collection.get(include=["documents", "metadatas"])

        # -------- Executive Summary (map-reduce style) --------
        partial_summaries = []

        for doc in docs["documents"][:8]:
            summary = self.llm(
                EXECUTIVE_SUMMARY_PROMPT + "\n" + doc[:1000]
            )[0]["generated_text"]
            partial_summaries.append(summary)

        executive_summary = self.llm(
            EXECUTIVE_SUMMARY_PROMPT + "\n" + " ".join(partial_summaries)
        )[0]["generated_text"]

        with open("backend/data/executive_summary.txt", "w", encoding="utf-8") as f:
            f.write(executive_summary)

        # -------- Section Summaries --------
        section_summaries = {}

        for doc, meta in zip(docs["documents"][:10], docs["metadatas"][:10]):
            section = meta["source"]

            summary = self.llm(
                SECTION_SUMMARY_PROMPT + "\n" + doc[:800]
            )[0]["generated_text"]

            section_summaries.setdefault(section, summary)

        with open("backend/data/summaries.json", "w", encoding="utf-8") as f:
            json.dump(section_summaries, f, indent=2)

        print("✅ Executive summary + section summaries saved!")
