import chromadb
from chromadb.config import Settings

def get_chroma_client(persist_path: str):
    client = chromadb.PersistentClient(
        path=persist_path
    )
    return client
