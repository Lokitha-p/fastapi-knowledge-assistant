import json
import os
from pathlib import Path

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

        # Get absolute path to data directory
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)

        self.exec_summary_path = self.data_dir / "executive_summary.txt"
        self.summaries_path = self.data_dir / "summaries.json"

        print(f"📁 Data directory: {self.data_dir}")
        print(f"📄 Executive summary path: {self.exec_summary_path}")
        print(f"📄 Summaries JSON path: {self.summaries_path}")

    def run(self):
        print("📝 SummaryAgent: Generating summaries...")

        docs = self.collection.get(include=["documents", "metadatas"])
        print(f"📊 Total documents retrieved: {len(docs['documents'])}")

        # -------- Executive Summary (map-reduce style) --------
        print("🔄 Generating executive summary...")
        partial_summaries = []

        for i, doc in enumerate(docs["documents"][:8]):
            print(f"   Processing doc {i+1}/8 for executive summary...")
            prompt = EXECUTIVE_SUMMARY_PROMPT + "\n" + doc[:1000]
            summary = self.llm(prompt)
            partial_summaries.append(summary)
            print(f"   ✓ Doc {i+1} processed")

        print("🔄 Creating final executive summary...")
        executive_summary = self.llm(
            EXECUTIVE_SUMMARY_PROMPT + "\n" + " ".join(partial_summaries)
        )

        with open(self.exec_summary_path, "w", encoding="utf-8") as f:
            f.write(executive_summary)
        print(f"✅ Executive summary saved to: {self.exec_summary_path}")

        # -------- Section Summaries --------
        print("🔄 Generating section summaries...")

        # Load existing summaries if file exists (for resuming)
        if self.summaries_path.exists():
            with open(self.summaries_path, "r", encoding="utf-8") as f:
                section_summaries = json.load(f)
            print(f"📂 Loaded {len(section_summaries)} existing summaries")
        else:
            section_summaries = {}

        # Group documents by unique sections
        sections_data = {}
        for doc, meta in zip(docs["documents"], docs["metadatas"]):
            section = meta.get("source", "unknown")
            if section not in sections_data:
                sections_data[section] = []
            sections_data[section].append(doc)

        print(f"📊 Found {len(sections_data)} unique sections: {list(sections_data.keys())}")

        # Generate summary for each unique section (use first doc from each section)
        for i, (section, section_docs) in enumerate(sections_data.items(), 1):
            # Skip if already processed
            if section in section_summaries:
                print(f"   ⏭️  Section {i}/{len(sections_data)}: {section} (already exists, skipping)")
                continue

            print(f"   Processing section {i}/{len(sections_data)}: {section}...")

            try:
                # Use the first chunk from this section (or combine multiple if needed)
                doc_text = section_docs[0][:800]
                prompt = SECTION_SUMMARY_PROMPT + "\n" + doc_text
                summary = self.llm(prompt)
                section_summaries[section] = summary

                # Write to file immediately after each summary
                with open(self.summaries_path, "w", encoding="utf-8") as f:
                    json.dump(section_summaries, f, indent=2, ensure_ascii=False)

                print(f"   ✓ Section {section} processed and saved")
            except Exception as e:
                print(f"   ❌ Error processing {section}: {str(e)}")
                section_summaries[section] = f"Error generating summary: {str(e)}"

                # Save even on error so we don't retry failed sections
                with open(self.summaries_path, "w", encoding="utf-8") as f:
                    json.dump(section_summaries, f, indent=2, ensure_ascii=False)

        print(f"✅ Section summaries saved to: {self.summaries_path}")
        print(f"✅ Total sections: {len(section_summaries)}")

        print("✅ All summaries completed!")
