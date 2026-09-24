from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from app.tamil.tamil_vector_store import get_tamil_vector_store

def retrieve_tamil_context(
    query: str,
    persona_id: str,
    top_k: int = 5
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Direct Tamil query retrieval from isolated Tamil vector store (persona_forge_docs_ta).
    Operates directly on Tamil text without translating query into English.
    """
    vector_store = get_tamil_vector_store()
    
    # Filter by persona_id
    filter_dict = {"persona_id": persona_id}
    
    try:
        results = vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=top_k,
            filter=filter_dict
        )
    except Exception as e:
        # Fallback if relevance scores not supported or empty collection
        try:
            raw_docs = vector_store.similarity_search(query=query, k=top_k, filter=filter_dict)
            results = [(doc, 1.0) for doc in raw_docs]
        except Exception:
            results = []
            
    sources = []
    seen_sources = set()
    context_chunks = []
    
    for doc, score in results:
        meta = doc.metadata or {}
        content = doc.page_content
        context_chunks.append(content)
        
        src_name = meta.get("source_name") or meta.get("source") or meta.get("original_filename") or "தமிழ் ஆவணம்"
        page = meta.get("page_number") or meta.get("page")
        src_key = f"{src_name}_p{page}"
        
        if src_key not in seen_sources:
            seen_sources.add(src_key)
            title = f"{src_name} (பக்கம் {page})" if page else src_name
            sources.append({
                "type": "document",
                "title": title,
                "content": content[:200] + "..." if len(content) > 200 else content,
                "url": None,
                "language": "ta"
            })
            
    formatted_context = "\n\n---\n\n".join(context_chunks)
    return formatted_context, sources
