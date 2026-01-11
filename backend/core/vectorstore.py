import chromadb
from chromadb.config import Settings

def get_chroma_client(persist_path: str):
    client = chromadb.Client(
        Settings(
            persist_directory=persist_path,
            anonymized_telemetry=False
        )
    )
    return client
