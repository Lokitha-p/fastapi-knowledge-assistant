from backend.core.llm import get_llm
from backend.core.vectorstore import get_chroma_client
from backend.config.settings import CHROMA_DB_PATH


RAG_PROMPT_TEMPLATE = """You are a helpful FastAPI expert assistant.
Based on the following FastAPI documentation excerpts, answer the user's question accurately and concisely.

Documentation Context:
{context}

Question: {question}

Answer:"""


class RAGAgent:
    def __init__(self):
        self.persist_path = CHROMA_DB_PATH
        self.client = get_chroma_client(self.persist_path)
        self.collection = self.client.get_collection("fastapi_docs")
        self.llm = get_llm()

    def retrieve_context(self, question: str, top_k: int = 3) -> str:
        """
        Retrieve relevant documentation chunks from ChromaDB based on the question.
        """
        results = self.collection.query(
            query_texts=[question],
            n_results=top_k,
            include=["documents", "metadatas"]
        )

        context_parts = []
        for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
            source = metadata.get("source", "unknown")
            context_parts.append(f"[{source}] {doc}")

        return "\n\n".join(context_parts)

    def run(self, question: str) -> dict:
        """
        Answer a question about FastAPI using RAG approach.
        """
        print(f"🔍 RAGAgent: Processing question: {question}")

        # Retrieve relevant context from ChromaDB
        context = self.retrieve_context(question)

        # Generate answer using Gemini
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)
        answer = self.llm(prompt)

        return {
            "question": question,
            "answer": answer.strip(),
            "context": context
        }
