import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import os

from backend.config.settings import FASTAPI_DOC_URLS
from backend.core.vectorstore import get_chroma_client


class IngestionAgent:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.persist_path = "backend/data/chroma_db"

        os.makedirs(self.persist_path, exist_ok=True)

        self.client = get_chroma_client(self.persist_path)
        self.collection = self.client.get_or_create_collection(
            name="fastapi_docs"
        )

    def scrape_page(self, url: str) -> str:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove nav, footer, sidebar
        for tag in soup(["nav", "footer", "aside", "script", "style"]):
            tag.decompose()

        return soup.get_text(separator=" ", strip=True)

    def chunk_text(self, text: str, chunk_size: int = 1000):
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        return chunks

    def run(self):
        print("🚀 IngestionAgent: Scraping FastAPI documentation...")

        doc_id = 0
        total_chunks = 0

        for url in FASTAPI_DOC_URLS:
            page_name = url.split("/")[-2]
            text = self.scrape_page(url)
            chunks = self.chunk_text(text)

            embeddings = self.embedder.encode(chunks).tolist()

            ids = [f"{page_name}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": page_name, "url": url} for _ in chunks]

            self.collection.add(
                documents=chunks,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
            )

            total_chunks += len(chunks)
            print(f"✅ {page_name}: {len(chunks)} chunks")

            doc_id += 1

        print(f"🎉 Indexed {total_chunks} total chunks!")
