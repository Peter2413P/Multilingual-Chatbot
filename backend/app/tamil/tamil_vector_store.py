import os
from langchain_chroma import Chroma
from app.tamil.tamil_embedding import get_tamil_embeddings_model

TAMIL_COLLECTION_NAME = os.getenv("TAMIL_COLLECTION_NAME", "persona_forge_docs_ta")
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db_v2")

def get_tamil_vector_store():
    """
    Returns isolated Chroma vector store for Tamil language documents.
    English vector store (persona_forge_docs) is kept completely untouched.
    """
    embeddings = get_tamil_embeddings_model()
    return Chroma(
        collection_name=TAMIL_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR
    )
