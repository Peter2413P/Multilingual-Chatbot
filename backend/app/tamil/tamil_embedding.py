import os
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings

@lru_cache(maxsize=1)
def get_tamil_embeddings_model():
    """
    Get configurable multilingual embedding model for Tamil vector storage & retrieval.
    English embeddings remain completely isolated in app.rag.embeddings.
    """
    model_name = os.getenv(
        "TAMIL_EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    model_kwargs = {'device': os.getenv("TAMIL_EMBEDDING_DEVICE", "cpu")}
    encode_kwargs = {'normalize_embeddings': True}
    
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
