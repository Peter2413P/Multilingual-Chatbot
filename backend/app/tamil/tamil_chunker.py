from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
import re

def split_tamil_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> List[str]:
    """
    Splits Tamil text respecting paragraph and sentence boundaries.
    Avoids breaking Tamil syllables or sentences mid-phrase where possible.
    """
    if not text or not text.strip():
        return []
    
    # First split by paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    # Sentence splitting regex (Tamil/English sentence endings)
    sentence_splitter = re.compile(r'(?<=[.!?|])\s+|\n+')
    
    for para in paragraphs:
        if len(para) <= chunk_size:
            # Paragraph fits in chunk limit
            if current_length + len(para) + 2 <= chunk_size:
                current_chunk.append(para)
                current_length += len(para) + 2
            else:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_length = len(para)
        else:
            # Paragraph is longer than chunk_size, split by sentences
            sentences = [s.strip() for s in sentence_splitter.split(para) if s.strip()]
            for sentence in sentences:
                if current_length + len(sentence) + 1 <= chunk_size:
                    current_chunk.append(sentence)
                    current_length += len(sentence) + 1
                else:
                    if current_chunk:
                        chunks.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                    current_length = len(sentence)
                    
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks

def chunk_tamil_document(
    text: str,
    metadata: Dict[str, Any],
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> List[Document]:
    """
    Chunks Tamil text and attaches standardized Tamil RAG metadata.
    """
    text_chunks = split_tamil_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    documents = []
    total_chunks = len(text_chunks)
    
    for idx, chunk in enumerate(text_chunks):
        doc_meta = dict(metadata or {})
        doc_meta.update({
            "language": "ta",
            "chunk_index": idx,
            "total_chunks": total_chunks,
        })
        # Standardize mandatory metadata fields
        if "knowledge_source_id" in doc_meta and "document_id" not in doc_meta:
            doc_meta["document_id"] = doc_meta["knowledge_source_id"]
            
        # Ensure Chroma metadata values are simple types (str, int, float, bool)
        clean_meta = {k: v for k, v in doc_meta.items() if isinstance(v, (str, int, float, bool))}
        documents.append(Document(page_content=chunk, metadata=clean_meta))
        
    return documents
