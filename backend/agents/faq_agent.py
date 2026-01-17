import json
import os
import requests
from pathlib import Path
from typing import List, Dict, Any

from backend.core.llm import get_faq_llm
from backend.core.vectorstore import get_chroma_client
from backend.config.settings import CHROMA_DB_PATH


class FAQAgent:
    def __init__(self):
        self.persist_path = CHROMA_DB_PATH
        self.client = get_chroma_client(self.persist_path)
        self.collection = self.client.get_collection("fastapi_docs")
        self.llm = get_faq_llm()

        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.faqs_path = self.data_dir / "faqs.json"

        print(f"📁 FAQ output path: {self.faqs_path}")
        print(f"📚 Knowledge Base: Using ChromaDB collection 'fastapi_docs'")

    def extract_topics(self, custom_topics=None):
        """
        Step 1: Extract 3 topics from documentation or use custom topics
        """
        if custom_topics and len(custom_topics) == 3:
            print(f"✅ Using custom topics: {custom_topics}")
            return custom_topics

        print("🔍 Extracting topics from knowledge base...")

        # Get sample documents from knowledge base
        docs = self.collection.get(include=["documents", "metadatas"])

        # Use first 10 docs for topic extraction
        context = "\n\n".join(docs["documents"][:10])

        prompt = f"""Analyze the following FastAPI documentation from our knowledge base and identify the 3 most important topics that developers commonly ask questions about.

IMPORTANT: Base your analysis ONLY on the provided documentation below. Do not use external knowledge.

Return ONLY a JSON array with 3 topics, nothing else. Format:
["Topic 1", "Topic 2", "Topic 3"]

Examples of good topics:
- "Authentication and Security"
- "Database Integration"
- "Request Validation"
- "Path and Query Parameters"
- "Dependency Injection"

Documentation from Knowledge Base:
{context[:3000]}

JSON array of 3 topics:"""

        response = self.llm(prompt)

        try:
            # Extract JSON array from response
            topics = json.loads(response.strip())
            if len(topics) >= 3:
                topics = topics[:3]
                print(f"✅ Extracted topics from knowledge base: {topics}")
                return topics
        except Exception as e:
            print(f"⚠️  Topic extraction failed: {e}, using defaults")

        # Fallback topics
        return ["Authentication", "Request Validation", "Database Integration"]

    def fetch_stackoverflow_questions(self, topic: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch top questions from StackOverflow API for a given topic
        """
        print(f"   🌐 Fetching StackOverflow questions for: {topic}")

        url = "https://api.stackexchange.com/2.3/search/advanced"

        params = {
            "order": "desc",
            "sort": "votes",  # Most upvoted
            "q": f"FastAPI {topic}",
            "site": "stackoverflow",
            "pagesize": num_questions,
            "filter": "!9_bDDxJY5"  # Includes question body
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            questions = []
            for item in data.get("items", []):
                questions.append({
                    "title": item.get("title", ""),
                    "score": item.get("score", 0),
                    "view_count": item.get("view_count", 0),
                    "link": item.get("link", "")
                })

            print(f"   ✅ Found {len(questions)} StackOverflow questions")
            return questions

        except Exception as e:
            print(f"   ⚠️  StackOverflow API error: {e}")
            return []

    def retrieve_relevant_docs(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Retrieve relevant documents from knowledge base for a given query
        """
        print(f"   📚 Retrieving documents from knowledge base for: {query[:60]}...")

        # Query the vector store for relevant documents
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        print(f"   ✅ Retrieved {len(results['documents'][0])} relevant documents")
        return results

    def answer_question_from_kb(self, question: str, topic: str) -> Dict[str, Any]:
        """
        Answer a StackOverflow question using ONLY the knowledge base content with citations
        """
        print(f"      🔍 Answering from KB: {question[:60]}...")

        # Retrieve relevant documents for this specific question
        kb_results = self.retrieve_relevant_docs(f"FastAPI {topic} {question}", n_results=3)

        documents = kb_results["documents"][0]
        metadatas = kb_results["metadatas"][0]
        distances = kb_results["distances"][0]

        if not documents:
            return {
                "question": question,
                "answer": "Not found in knowledge base",
                "sources": [],
                "topic": topic,
                "retrieval_distance": None
            }

        # Build context with document sources
        context_parts = []
        source_mapping = {}  # Map document numbers to actual source URLs

        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            source = meta.get('source', 'Unknown')
            source_mapping[i+1] = source  # Store mapping for later replacement
            context_parts.append(f"[Document {i+1}] (Source: {source})\n{doc[:800]}\n")

        context = "\n---\n".join(context_parts)

        prompt = f"""You are a FastAPI documentation assistant. Answer the following question using ONLY the information from the knowledge base documents provided below.

CRITICAL RULES:
1. Use ONLY information from the provided documents - do not add external knowledge
2. Cite the document source in your answer using the exact source URL (e.g., [Source: dependencies] or [Source: path-params])
3. If the information is not in the documents, say "This information is not available in the knowledge base"
4. Keep the answer concise but complete
5. Be specific and technical
6. Use the actual source names shown in the documents, not "Document 1" or "Document 2"

Question: {question}

Knowledge Base Documents:
{context}

Answer (with citation using actual source names):"""

        try:
            answer = self.llm(prompt).strip()

            # Clean up the answer
            answer = answer.replace('Answer:', '').strip()

            # Extract actual source URLs from metadata
            sources = [meta.get('source', 'Unknown') for meta in metadatas]

            print(f"      ✅ Answer generated with {len(sources)} sources")

            return {
                "question": question,
                "answer": answer,
                "sources": sources,
                "topic": topic,
                "retrieval_distance": distances[0] if distances else None,
                "stackoverflow_origin": True
            }

        except Exception as e:
            print(f"      ❌ Failed to generate answer: {e}")
            return {
                "question": question,
                "answer": "Error generating answer from knowledge base",
                "sources": [meta.get('source', 'Unknown') for meta in metadatas[:1]],
                "topic": topic,
                "retrieval_distance": None
            }

    def generate_faqs_from_kb(self, topic: str, kb_results: Dict[str, Any], num_faqs: int = 3) -> List[Dict[str, Any]]:
        """
        Generate FAQ questions and answers using ONLY the knowledge base content
        """
        print(f"   🤖 Generating FAQs from knowledge base for: {topic}")

        # Prepare context from retrieved documents
        documents = kb_results["documents"][0]
        metadatas = kb_results["metadatas"][0]
        distances = kb_results["distances"][0]

        # Build context with document sources
        context_parts = []
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            source = meta.get('source', 'Unknown')
            context_parts.append(f"[Document {i+1}] (Source: {source})\n{doc}\n")

        context = "\n---\n".join(context_parts)

        prompt = f"""You are a FastAPI documentation assistant. Generate {num_faqs} frequently asked questions and their answers about "{topic}" using ONLY the information provided in the knowledge base below.

CRITICAL RULES:
1. Use ONLY information from the provided documents - do not add external knowledge
2. Each answer must cite the document source it came from (e.g., [Document 1])
3. If information is not in the documents, say "Not found in knowledge base"
4. Keep answers concise and accurate

Knowledge Base Documents:
{context[:4000]}

Generate {num_faqs} FAQs in the following JSON format:
[
  {{
    "question": "...",
    "answer": "... [Source: Document X]",
    "sources": ["Document X source URL"]
  }}
]

JSON output:"""

        try:
            response = self.llm(prompt).strip()

            # Try to parse JSON response
            # Handle cases where LLM might wrap JSON in markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            faqs = json.loads(response)

            # Add metadata to each FAQ
            for faq in faqs:
                if "sources" not in faq or not faq["sources"]:
                    # Extract source metadata from the documents used
                    faq["sources"] = [meta.get('source', 'Unknown') for meta in metadatas[:2]]
                faq["topic"] = topic
                faq["retrieval_distance"] = distances[0] if distances else None

            print(f"   ✅ Generated {len(faqs)} FAQs with citations")
            return faqs

        except json.JSONDecodeError as e:
            print(f"   ⚠️  Failed to parse JSON response: {e}")
            print(f"   📄 Raw response: {response[:200]}...")

            # Fallback: create simple FAQs with metadata
            return [{
                "question": f"What is {topic} in FastAPI?",
                "answer": f"Information about {topic} can be found in the knowledge base. [Source: {metadatas[0].get('source', 'Unknown')}]",
                "sources": [meta.get('source', 'Unknown') for meta in metadatas[:2]],
                "topic": topic,
                "retrieval_distance": distances[0] if distances else None
            }]
        except Exception as e:
            print(f"   ❌ FAQ generation failed: {e}")
            return []

    def run(self, custom_topics=None):
        """
        Main pipeline:
        1. Extract topics from KB
        2. Fetch real questions from StackOverflow
        3. Answer questions using KB content with citations
        """
        print("❓ FAQAgent: Generating FAQs (StackOverflow Questions + Knowledge Base Answers)...")
        print("=" * 70)

        # Step 1: Extract or use custom topics
        topics = self.extract_topics(custom_topics)

        faq_output = {
            "topics": [],
            "metadata": {
                "question_source": "StackOverflow API",
                "answer_source": "Knowledge Base (ChromaDB)",
                "model": "OpenRouter LLM",
                "total_topics": len(topics)
            }
        }

        # Step 2-3: For each topic, fetch SO questions and answer from KB
        for i, topic in enumerate(topics, 1):
            print(f"\n📌 Topic {i}/{len(topics)}: {topic}")

            # Fetch StackOverflow questions
            so_questions = self.fetch_stackoverflow_questions(topic, num_questions=5)

            if not so_questions:
                print(f"   ⚠️  No StackOverflow questions found, generating from KB directly")
                # Fallback: Generate FAQs directly from knowledge base
                kb_results = self.retrieve_relevant_docs(f"FastAPI {topic}", n_results=5)
                if kb_results["documents"][0]:
                    faqs = self.generate_faqs_from_kb(topic, kb_results, num_faqs=3)
                else:
                    faqs = []

                faq_output["topics"].append({
                    "topic": topic,
                    "faqs": faqs,
                    "question_source": "Generated from KB"
                })
                continue

            # Answer top 3 StackOverflow questions using knowledge base
            print(f"   💡 Answering top {min(3, len(so_questions))} questions from knowledge base...")
            faqs = []

            for so_question in so_questions[:3]:
                faq = self.answer_question_from_kb(so_question["title"], topic)
                if faq:
                    # Add StackOverflow metadata
                    faq["stackoverflow_score"] = so_question["score"]
                    faq["stackoverflow_views"] = so_question["view_count"]
                    faq["stackoverflow_link"] = so_question.get("link", "")
                    faqs.append(faq)

            faq_output["topics"].append({
                "topic": topic,
                "faqs": faqs,
                "question_source": "StackOverflow",
                "stackoverflow_questions_found": len(so_questions)
            })

            print(f"   ✅ Topic '{topic}' completed: {len(faqs)} FAQs generated")

        # Calculate total FAQs
        total_faqs = sum(len(t.get("faqs", [])) for t in faq_output["topics"])
        faq_output["metadata"]["total_faqs"] = total_faqs

        # Save to file
        with open(self.faqs_path, "w", encoding="utf-8") as f:
            json.dump(faq_output, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 70)
        print(f"✅ FAQ generation complete!")
        print(f"📊 Total: {len(faq_output['topics'])} topics, {total_faqs} FAQs")
        print(f"❓ Questions from: StackOverflow")
        print(f"📚 Answers from: Knowledge Base (with citations)")
        print(f"💾 Saved to: {self.faqs_path}")

        return faq_output
