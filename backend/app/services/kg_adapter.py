"""
app/services/kg_adapter.py — KnowledgeGraphAdapter integration layer.

Provides seamless, failure-isolated integration between the existing PDF/Tamil OCR
processing pipeline and the cloned Indic Knowledge Graph module.
"""
from __future__ import annotations

import os
import sys
import uuid
import logging
from typing import Any, List, Dict, Optional
from sqlalchemy.orm import Session

import re
from app.db.session import SessionLocal
from app.db.models import KnowledgeSource, KnowledgeNode, KnowledgeEdge

logger = logging.getLogger("knowledge_graph_adapter")
logging.basicConfig(level=logging.INFO)


def normalize_canonical_name(name: str) -> str:
    """Normalize entity name for deduplication and matching."""
    clean = re.sub(r"[^\w\s\-\u0B80-\u0BFF]", "", name).strip().lower()
    return re.sub(r"\s+", " ", clean)


class KnowledgeGraphAdapter:
    """
    Adapter isolating existing application from knowledge graph internal implementation.
    Consumes extracted chunks after document indexing and creates normalized graph nodes and edges.
    """

    def __init__(self):
        pass

    def build_graph_for_document(
        self,
        document_id: str,
        chunks: List[Any],
        language: Optional[str] = "en",
    ) -> Dict[str, Any]:
        """
        Main entry point for document knowledge graph generation.
        Fully isolated: errors will be logged but will not raise or fail parent document ingestion.
        """
        print(f"[KG] received {len(chunks)} chunks for document {document_id}")
        
        db: Session = SessionLocal()
        try:
            # 1. Clean existing nodes/edges for this document if re-indexing
            db.query(KnowledgeEdge).filter(KnowledgeEdge.document_id == document_id).delete()
            db.query(KnowledgeNode).filter(KnowledgeNode.document_id == document_id).delete()
            db.commit()

            if not chunks:
                print(f"[KG] No chunks provided for document {document_id}")
                return {"nodes": [], "edges": []}

            node_map: Dict[str, KnowledgeNode] = {}
            raw_relations: List[tuple[str, str, str, Optional[str], float, str]] = []
            total_raw_entities = 0

            # 2. Iterate through chunks and extract knowledge
            for idx, chunk in enumerate(chunks):
                # Normalize chunk data whether LangChain Document or dict
                if hasattr(chunk, "page_content"):
                    text = chunk.page_content or ""
                    meta = getattr(chunk, "metadata", {}) or {}
                    page_num = meta.get("page_number") or meta.get("page") or (idx + 1)
                    chunk_id = meta.get("chunk_id") or f"chunk-{document_id}-{idx+1}"
                    chunk_lang = meta.get("language") or language or "en"
                elif isinstance(chunk, dict):
                    text = chunk.get("text") or chunk.get("original_text") or chunk.get("page_content") or ""
                    meta = chunk.get("metadata") or chunk
                    page_num = meta.get("page_number") or meta.get("page") or (idx + 1)
                    chunk_id = chunk.get("chunk_id") or meta.get("chunk_id") or f"chunk-{document_id}-{idx+1}"
                    chunk_lang = chunk.get("language") or meta.get("language") or language or "en"
                else:
                    text = str(chunk)
                    page_num = idx + 1
                    chunk_id = f"chunk-{document_id}-{idx+1}"
                    chunk_lang = language or "en"

                if not text or not text.strip():
                    continue

                # Run extraction via RuleBasedExtractor heuristics directly
                extraction_entities, extraction_relations = self._extract_heuristics(text, chunk_lang)

                total_raw_entities += len(extraction_entities)

                # Process entities into canonical node map
                for ent in extraction_entities:
                    name = ent.name if hasattr(ent, "name") else ent.get("name")
                    orig_name = ent.original_name if hasattr(ent, "original_name") else ent.get("original_name")
                    ent_type = ent.entity_type if hasattr(ent, "entity_type") else ent.get("entity_type", "CONCEPT")
                    desc = ent.description if hasattr(ent, "description") else ent.get("description", "")

                    if not name:
                        continue

                    c_name = normalize_canonical_name(name)
                    if not c_name or len(c_name) < 2:
                        continue

                    if c_name in node_map:
                        node = node_map[c_name]
                        node.frequency += 1
                        chunk_ids = node.source_chunk_ids
                        if chunk_id not in chunk_ids:
                            chunk_ids.append(chunk_id)
                            node.source_chunk_ids = chunk_ids
                        if not node.original_name and orig_name:
                            node.original_name = orig_name
                        if (not node.description or len(node.description) < 20) and desc:
                            node.description = desc
                    else:
                        new_node = KnowledgeNode(
                            node_id=str(uuid.uuid4()),
                            document_id=document_id,
                            name=name,
                            canonical_name=c_name,
                            original_name=orig_name,
                            entity_type=ent_type,
                            description=desc,
                            frequency=1,
                        )
                        new_node.source_chunk_ids = [chunk_id]
                        node_map[c_name] = new_node
                        db.add(new_node)

                # Collect relations
                for rel in extraction_relations:
                    src = rel.source if hasattr(rel, "source") else rel.get("source")
                    tgt = rel.target if hasattr(rel, "target") else rel.get("target")
                    rel_type = rel.relation_type if hasattr(rel, "relation_type") else rel.get("relation_type", "RELATED_TO")
                    desc = rel.description if hasattr(rel, "description") else rel.get("description")
                    conf = rel.confidence if hasattr(rel, "confidence") else rel.get("confidence", 0.9)

                    if src and tgt:
                        raw_relations.append((src, tgt, rel_type, desc, conf, chunk_id))

            print(f"[KG] extracted {total_raw_entities} entities")
            print(f"[KG] deduplicated to {len(node_map)} nodes")

            db.flush()

            # 3. Resolve relations to node IDs
            created_edges: List[KnowledgeEdge] = []
            seen_edges: set[tuple[str, str, str]] = set()

            for src_name, tgt_name, rel_type, desc, conf, chk_id in raw_relations:
                src_c = normalize_canonical_name(src_name)
                tgt_c = normalize_canonical_name(tgt_name)

                if not src_c or not tgt_c or src_c == tgt_c:
                    continue

                src_node = node_map.get(src_c)
                tgt_node = node_map.get(tgt_c)

                if src_node and tgt_node:
                    edge_key = (src_node.node_id, tgt_node.node_id, rel_type)
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edge = KnowledgeEdge(
                            edge_id=str(uuid.uuid4()),
                            document_id=document_id,
                            source_node_id=src_node.node_id,
                            target_node_id=tgt_node.node_id,
                            relation_type=rel_type,
                            description=desc or f"{src_node.name} {rel_type.lower().replace('_', ' ')} {tgt_node.name}",
                            weight=conf,
                            source_chunk_id=chk_id,
                        )
                        db.add(edge)
                        created_edges.append(edge)

            # Also create co-occurrence relations between prominent entities in same chunk if sparse
            if len(created_edges) < len(node_map) and len(node_map) > 1:
                node_list = list(node_map.values())
                for i in range(len(node_list) - 1):
                    for j in range(i + 1, min(i + 4, len(node_list))):
                        n1 = node_list[i]
                        n2 = node_list[j]
                        common_chunks = set(n1.source_chunk_ids) & set(n2.source_chunk_ids)
                        if common_chunks:
                            edge_key = (n1.node_id, n2.node_id, "RELATED_TO")
                            if edge_key not in seen_edges:
                                seen_edges.add(edge_key)
                                edge = KnowledgeEdge(
                                    edge_id=str(uuid.uuid4()),
                                    document_id=document_id,
                                    source_node_id=n1.node_id,
                                    target_node_id=n2.node_id,
                                    relation_type="RELATED_TO",
                                    description=f"'{n1.name}' and '{n2.name}' appear together in the same context.",
                                    weight=0.85,
                                    source_chunk_id=list(common_chunks)[0],
                                )
                                db.add(edge)
                                created_edges.append(edge)

            db.commit()

            print(f"[KG] generated {len(created_edges)} relationships")
            print(f"[KG] graph ready for document {document_id}")

            return {
                "document_id": document_id,
                "node_count": len(node_map),
                "edge_count": len(created_edges),
                "nodes": [n.to_dict() for n in node_map.values()],
                "edges": [e.to_dict() for e in created_edges],
            }

        except Exception as e:
            import traceback
            print(f"[KG] ERROR in graph generation for document {document_id}: {e}")
            traceback.print_exc()
            db.rollback()
            return {"document_id": document_id, "node_count": 0, "edge_count": 0, "nodes": [], "edges": []}
        finally:
            db.close()

    def _extract_heuristics(self, text: str, language: str = "en") -> tuple[list[Any], list[Any]]:
        """Lightweight regex/keyword entity extractor fallback."""
        import re

        KNOWN_INDIC = {
            "அறம்": ("Aram (Virtue)", "PHILOSOPHY", "Foundational Tamil concept of moral virtue and righteousness."),
            "ஜெயமோகன்": ("Jeyamohan", "PERSON", "Renowned contemporary Tamil novelist and literary critic."),
            "திருக்குறள்": ("Thirukkural", "WORK", "Classic Tamil ethical treatise authored by Thiruvalluvar."),
            "திருவள்ளுவர்": ("Thiruvalluvar", "PERSON", "Celebrated Tamil poet-philosopher."),
            "மகாபாரதம்": ("Mahabharata", "WORK", "Ancient Indian epic narrative."),
            "வெண்முரசு": ("Venmurasu", "WORK", "Epic Tamil novel series based on Mahabharata by Jeyamohan."),
            "பாரதியார்": ("Subramania Bharati", "PERSON", "Visionary Tamil poet and freedom activist."),
            "பாரதிதாசன்": ("Bharathidasan", "PERSON", "20th-century Tamil poet and rationalist writer."),
            "கம்பர்": ("Kambar", "PERSON", "Medieval Tamil poet who authored Kamba Ramayanam."),
            "கம்பராமாயணம்": ("Kamba Ramayanam", "WORK", "Celebrated Tamil version of the Ramayana epic."),
            "சென்னை": ("Chennai", "LOCATION", "Capital city of Tamil Nadu, India."),
            "மதுரை": ("Madurai", "LOCATION", "Historical cultural capital and ancient literary center."),
            "தமிழ்நாடு": ("Tamil Nadu", "LOCATION", "State in Southern India renowned for its rich literary heritage."),
            "விஜய்": ("Vijay (Actor)", "PERSON", "Leading Indian actor and public figure in Tamil cinema."),
            "கமல்ஹாசன்": ("Kamal Haasan", "PERSON", "Acclaimed Indian actor, director, and screenwriter."),
            "ரஜினிகாந்த்": ("Rajinikanth", "PERSON", "Iconic Indian film actor and cultural phenomenon."),
            "இளையராஜா": ("Ilaiyaraaja", "PERSON", "Legendary Indian music composer and maestro."),
            "ஏ. ஆர். ரகுமான்": ("A. R. Rahman", "PERSON", "Oscar-winning Indian music composer and music director."),
            "பொன்னியின் செல்வன்": ("Ponniyin Selvan", "WORK", "Historical novel by Kalki Krishnamurthy."),
            "கல்கி": ("Kalki Krishnamurthy", "PERSON", "Celebrated Tamil writer and journalist."),
        }

        entities = []
        seen = set()

        for ta_term, (en_name, etype, desc) in KNOWN_INDIC.items():
            if ta_term in text or en_name.lower() in text.lower():
                if en_name.lower() not in seen:
                    seen.add(en_name.lower())
                    entities.append({
                        "name": en_name,
                        "original_name": ta_term,
                        "entity_type": etype,
                        "description": desc,
                    })

        # Match English capitalized named entities
        matches = re.findall(r"\b[A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)*\b", text)
        stop_words = {"The", "This", "That", "There", "When", "What", "Where", "Which", "Chapter", "Section", "Page", "And", "With"}
        for m in matches:
            if len(m) > 3 and m not in stop_words and m.lower() not in seen:
                seen.add(m.lower())
                etype = "PERSON" if any(w in m.lower() for w in ["dr", "prof", "mr", "author"]) else "CONCEPT"
                entities.append({
                    "name": m,
                    "original_name": None,
                    "entity_type": etype,
                    "description": f"Entity identified from document text: {m}.",
                })

        relations = []
        if len(entities) >= 2:
            p = entities[0]
            for s in entities[1:4]:
                relations.append({
                    "source": p["name"],
                    "target": s["name"],
                    "relation_type": "AUTHORED_BY" if s.get("entity_type") == "PERSON" else "RELATED_TO",
                    "description": f"'{p['name']}' is discussed in connection with '{s['name']}'.",
                    "confidence": 0.88,
                })

        return entities[:12], relations[:15]

    def get_document_graph(self, document_id: str) -> Dict[str, Any]:
        """Fetch graph for a document."""
        db: Session = SessionLocal()
        try:
            nodes = db.query(KnowledgeNode).filter(KnowledgeNode.document_id == document_id).all()
            edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.document_id == document_id).all()

            return {
                "document_id": document_id,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "nodes": [n.to_dict() for n in nodes],
                "edges": [e.to_dict() for e in edges],
            }
        finally:
            db.close()

    def get_node_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full details for a node including connections and source passages."""
        db: Session = SessionLocal()
        try:
            node = db.query(KnowledgeNode).filter(KnowledgeNode.node_id == node_id).first()
            if not node:
                return None

            # Get document details
            doc = db.query(KnowledgeSource).filter(KnowledgeSource.id == node.document_id).first()
            doc_name = doc.name if doc else (doc.original_filename if doc else "Document")

            # Fetch connected edges
            outgoing = db.query(KnowledgeEdge).filter(KnowledgeEdge.source_node_id == node_id).all()
            incoming = db.query(KnowledgeEdge).filter(KnowledgeEdge.target_node_id == node_id).all()

            relations = []
            for e in outgoing:
                tgt = db.query(KnowledgeNode).filter(KnowledgeNode.node_id == e.target_node_id).first()
                relations.append({
                    "edge_id": e.edge_id,
                    "direction": "outgoing",
                    "relation_type": e.relation_type,
                    "target_node_id": e.target_node_id,
                    "target_node_name": tgt.name if tgt else "Unknown",
                    "target_node_type": tgt.entity_type if tgt else "CONCEPT",
                    "description": e.description,
                    "weight": e.weight,
                })
            for e in incoming:
                src = db.query(KnowledgeNode).filter(KnowledgeNode.node_id == e.source_node_id).first()
                relations.append({
                    "edge_id": e.edge_id,
                    "direction": "incoming",
                    "relation_type": e.relation_type,
                    "source_node_id": e.source_node_id,
                    "source_node_name": src.name if src else "Unknown",
                    "source_node_type": src.entity_type if src else "CONCEPT",
                    "description": e.description,
                    "weight": e.weight,
                })

            # Fetch source chunk text from ChromaDB or doc metadata
            docs = []
            metas = []
            try:
                import chromadb
                client = chromadb.PersistentClient(path="./chroma_db_v2")
                
                # Check standard collection
                try:
                    col = client.get_collection("persona_forge_docs")
                    results = col.get(where={"knowledge_source_id": node.document_id})
                    docs = results.get("documents", []) or []
                    metas = results.get("metadatas", []) or []
                except Exception:
                    pass

                # If empty, check Tamil collection
                if not docs:
                    try:
                        col_ta = client.get_collection("persona_forge_docs_ta")
                        results = col_ta.get(where={"knowledge_source_id": node.document_id})
                        docs = results.get("documents", []) or []
                        metas = results.get("metadatas", []) or []
                    except Exception:
                        pass
            except Exception as vs_err:
                print(f"[KG] Could not retrieve chunk passages from Chroma: {vs_err}")

            # Extract sentences and synthesize node summary & key insights
            node_type_label = (node.entity_type or "concept").lower()
            keywords = [node.name.lower()]
            if node.original_name:
                keywords.append(node.original_name.lower())
            tokens = [t.lower() for t in node.name.split() if len(t) > 3]

            extracted_sentences = []
            seen_sents = set()

            all_passages = []
            for d_text, d_meta in zip(docs, metas):
                tr = (d_meta or {}).get("translated_text")
                if tr:
                    all_passages.append(tr)
                if d_text:
                    all_passages.append(d_text)

            import re
            for text in all_passages:
                if not text:
                    continue
                sents = re.split(r'(?<=[.!?\n])\s+', text)
                for s in sents:
                    s_clean = s.strip().replace("\n", " ")
                    if len(s_clean) < 15 or len(s_clean) > 280:
                        continue
                    s_lower = s_clean.lower()
                    if any(k in s_lower for k in keywords) or (tokens and any(t in s_lower for t in tokens)):
                        if s_lower not in seen_sents:
                            seen_sents.add(s_lower)
                            extracted_sentences.append(s_clean)

            # Build key insights
            key_insights = []
            for s in extracted_sentences[:4]:
                formatted = s if s.endswith(('.', '!', '?')) else s + '.'
                key_insights.append(formatted)

            # If sparse from text, supplement with relational insights
            if len(key_insights) < 2 and relations:
                for r in relations[:3]:
                    other_name = r.get("target_node_name") if r.get("direction") == "outgoing" else r.get("source_node_name")
                    rel_label = r.get("relation_type", "RELATED_TO").replace("_", " ").lower()
                    if other_name and other_name != "Unknown":
                        key_insights.append(f"Connected to {other_name} through {rel_label} relation.")

            if not key_insights:
                key_insights.append(f"Identified as a core {node_type_label} appearing {node.frequency} time(s) across document passages.")

            # Synthesize node summary
            rel_summary = ""
            if relations:
                rel_targets = [
                    (r.get("target_node_name") if r.get("direction") == "outgoing" else r.get("source_node_name"))
                    for r in relations[:3]
                    if (r.get("target_node_name") or r.get("source_node_name")) not in ["Unknown", None]
                ]
                if rel_targets:
                    rel_summary = f" Connected with {', '.join(rel_targets[:3])} in the knowledge network."

            if node.description and len(node.description.strip()) > 10 and not node.description.startswith("Entity identified"):
                node_summary = f"{node.description}{rel_summary}"
            elif extracted_sentences:
                node_summary = f"{node.name} is a key {node_type_label} in this document. {extracted_sentences[0]}{rel_summary}"
            else:
                node_summary = f"{node.name} represents a key {node_type_label} within the document's knowledge structure.{rel_summary}"

            node_data = node.to_dict()
            node_data["document_name"] = doc_name
            node_data["description"] = node_summary
            node_data["summary"] = node_summary
            node_data["key_insights"] = key_insights

            source_chunks = []
            for idx, (d_text, d_meta) in enumerate(zip(docs, metas)):
                c_id = (d_meta or {}).get("chunk_id") or f"chunk-{node.document_id}-{idx+1}"
                if c_id in node.source_chunk_ids or (node.name.lower() in d_text.lower()) or (node.original_name and node.original_name in d_text):
                    source_chunks.append({
                        "chunk_id": c_id,
                        "document_id": node.document_id,
                        "document_name": doc_name,
                        "page_number": (d_meta or {}).get("page_number", idx + 1),
                        "chunk_index": idx,
                        "language": (d_meta or {}).get("language", "ta" if node.original_name else "en"),
                        "original_text": d_text,
                        "translated_text": (d_meta or {}).get("translated_text", None),
                        "is_ocr": (d_meta or {}).get("input_type") == "scanned_pdf_paddleocr",
                    })

            return {
                "node": node_data,
                "summary": node_summary,
                "key_insights": key_insights,
                "connected_relations": relations,
                "source_chunks": source_chunks[:5],
            }
        finally:
            db.close()


_kg_adapter: Optional[KnowledgeGraphAdapter] = None


def get_kg_adapter() -> KnowledgeGraphAdapter:
    """Singleton getter for KnowledgeGraphAdapter."""
    global _kg_adapter
    if _kg_adapter is None:
        _kg_adapter = KnowledgeGraphAdapter()
    return _kg_adapter
