import asyncio
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db.session import SessionLocal, engine, Base
import app.db.models
from app.db.models import Persona, KnowledgeSource, KnowledgeNode, KnowledgeEdge
from app.services.kg_adapter import get_kg_adapter
from app.api.endpoints import get_document_graph, get_node_details, get_persona_graph

async def run_direct_api_test():
    print("=== STARTING DIRECT API & ENDPOINT VERIFICATION ===", flush=True)
    Base.metadata.create_all(bind=engine)
    
    # 1. Create a Persona in DB
    db = SessionLocal()
    persona = Persona(name="Indic KG Direct API Persona")
    db.add(persona)
    db.commit()
    db.refresh(persona)
    persona_id = persona.id
    print(f"[✓] Persona created: {persona_id}", flush=True)
    
    # 2. Create Knowledge Source
    doc = KnowledgeSource(
        persona_id=persona_id,
        name="kambar_epic_sample.txt",
        source_type="UPLOAD",
        original_filename="kambar_epic_sample.txt",
        status="PROCESSING"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    doc_id = doc.id
    db.close()
    
    # 3. Simulate Extracted Chunks
    sample_chunks = [
        {
            "chunk_id": f"chunk-{doc_id}-1",
            "page_number": 1,
            "text": "கம்பராமாயணம் என்பது கம்பர் எழுதிய தலைசிறந்த காப்பியம் ஆகும். இது தமிழ் இலக்கியத்தின் பொக்கிஷம்.",
            "language": "ta"
        },
        {
            "chunk_id": f"chunk-{doc_id}-2",
            "page_number": 2,
            "text": "திருவள்ளுவர் எழுதிய திருக்குறள் மற்றும் பாரதியார் படைப்புகள் தமிழ்நாட்டில் மக்களிடையே மிகுந்த வரவேற்பைப் பெற்றன. சென்னை மற்றும் மதுரை இலக்கிய ஆய்வரங்குகளில் கம்பராமாயணம் ஆய்வு செய்யப்படுகிறது.",
            "language": "ta"
        }
    ]
    
    adapter = get_kg_adapter()
    build_res = adapter.build_graph_for_document(doc_id, sample_chunks, language="ta")
    print(f"[✓] Adapter built graph: {build_res['node_count']} nodes, {build_res['edge_count']} edges", flush=True)
    
    # 4. Call Endpoint: get_document_graph(document_id)
    graph_res = await get_document_graph(doc_id)
    assert graph_res["document_id"] == doc_id
    assert graph_res["node_count"] >= 4
    assert graph_res["edge_count"] >= 3
    print(f"[✓] GET /documents/{doc_id}/graph succeeded: {graph_res['node_count']} nodes, {graph_res['edge_count']} edges", flush=True)
    
    # 5. Call Endpoint: get_node_details(node_id)
    first_node_id = graph_res["nodes"][0]["node_id"]
    first_node_name = graph_res["nodes"][0]["name"]
    node_details = await get_node_details(first_node_id)
    assert node_details["node"]["node_id"] == first_node_id
    assert "connected_relations" in node_details
    assert "source_chunks" in node_details
    print(f"[✓] GET /graph/nodes/{first_node_id} succeeded for '{first_node_name}' ({len(node_details['connected_relations'])} relations)", flush=True)
    
    # 6. Call Endpoint: get_persona_graph(persona_id)
    persona_graph = await get_persona_graph(persona_id)
    assert persona_graph["persona_id"] == persona_id
    assert persona_graph["node_count"] >= 4
    print(f"[✓] GET /personas/{persona_id}/graph succeeded: {persona_graph['node_count']} aggregated nodes", flush=True)
    
    # Clean up test persona
    db = SessionLocal()
    p = db.query(Persona).filter(Persona.id == persona_id).first()
    if p:
        db.delete(p)
        db.commit()
    db.close()
    
    print("\n=======================================================", flush=True)
    print("ALL DIRECT API AND ENDPOINT TESTS COMPLETED SUCCESSFULLY!", flush=True)
    print("=======================================================", flush=True)

if __name__ == "__main__":
    asyncio.run(run_direct_api_test())
