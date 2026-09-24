import os
from typing import List, Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session
from langchain_core.documents import Document

from app.db.session import SessionLocal
from app.db.models import KnowledgeSource, Persona
from app.tamil.tamil_extractor import extract_tamil_document
from app.tamil.tamil_chunker import chunk_tamil_document
from app.tamil.tamil_vector_store import get_tamil_vector_store
from app.tamil.tamil_generator import stream_tamil_chat_response

def ingest_tamil_document(file_path: str, filename: str, persona_id: str) -> str:
    """
    Ingests a Tamil document into the isolated Tamil Chroma collection (persona_forge_docs_ta).
    Existing English collection (persona_forge_docs) is completely untouched.
    """
    db: Session = SessionLocal()
    
    # 1. Create DB Record for tracking
    source = KnowledgeSource(
        persona_id=persona_id,
        name=filename,
        source_type="UPLOAD",
        original_filename=filename,
        status="PROCESSING"
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    source_id = source.id
    db.close()
    
    try:
        # 2. Extract Tamil text (direct text if available, or PaddleOCR if scanned PDF)
        page_results = extract_tamil_document(file_path)
        
        all_docs: List[Document] = []
        
        # 3. Chunk each page
        for page_data in page_results:
            page_text = page_data["text"]
            if not page_text or not page_text.strip():
                continue
                
            page_meta = {
                "persona_id": persona_id,
                "knowledge_source_id": source_id,
                "document_id": source_id,
                "source_name": filename,
                "source": filename,
                "original_filename": filename,
                "page_number": page_data["page_number"],
                "page": page_data["page_number"],
                "input_type": page_data["input_type"],
                "confidence_avg": float(page_data.get("confidence_avg", 1.0)),
                "language": "ta"
            }
            
            docs = chunk_tamil_document(
                text=page_text,
                metadata=page_meta,
                chunk_size=800,
                chunk_overlap=150
            )
            all_docs.extend(docs)
            
        # 4. Store in isolated Tamil Chroma collection
        if all_docs:
            vector_store = get_tamil_vector_store()
            vector_store.add_documents(all_docs)
            
        # 5. Update DB record status
        db = SessionLocal()
        src = db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id).first()
        if src:
            src.chunk_count = len(all_docs)
            src.status = "COMPLETED"
            db.commit()
        db.close()

        # 6. Generate Knowledge Graph via Adapter (Failure-Isolated)
        try:
            from app.services.kg_adapter import get_kg_adapter
            get_kg_adapter().build_graph_for_document(source_id, all_docs, language="ta")
        except Exception as kg_err:
            print(f"[KG] Non-fatal Tamil graph generation warning: {kg_err}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        db = SessionLocal()
        src = db.query(KnowledgeSource).filter(KnowledgeSource.id == source_id).first()
        if src:
            src.status = "FAILED"
            src.error_message = str(e)
            db.commit()
        db.close()
        raise
        
    return source_id

def delete_tamil_knowledge_source(source_id: str):
    """
    Deletes vectors associated with source_id from the Tamil Chroma collection.
    """
    try:
        vector_store = get_tamil_vector_store()
        vector_store._collection.delete(where={"knowledge_source_id": source_id})
    except Exception as e:
        print(f"[TAMIL DB] Error deleting document vectors: {e}")
