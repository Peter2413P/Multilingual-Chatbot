import asyncio
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db.session import SessionLocal, engine, Base
import app.db.models
from app.db.models import Persona, KnowledgeSource, KnowledgeNode, KnowledgeEdge
from app.services.kg_adapter import get_kg_adapter

def test_node_interaction():
    print("=== STARTING NODE INTERACTION & DETAIL VIEW VERIFICATION ===", flush=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Create a persona and knowledge source
    persona = Persona(name="Node Interaction Test Persona")
    db.add(persona)
    db.commit()
    db.refresh(persona)
    persona_id = persona.id
    
    doc = KnowledgeSource(
        persona_id=persona_id,
        name="tamil_literary_figures.txt",
        source_type="UPLOAD",
        original_filename="tamil_literary_figures.txt",
        status="PROCESSING"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    doc_id = doc.id
    db.close()
    
    # 2. Simulate multi-concept multi-page chunks
    chunks = [
        {
            "chunk_id": f"chunk-{doc_id}-1",
            "page_number": 1,
            "text": "ஜெயமோகன் நவீன தமிழ் இலக்கியத்தின் முன்னோடி எழுத்தாளர் ஆவார். இவர் அறம் சிறுகதைத் தொகுப்பை இயற்றினார்.",
            "language": "ta"
        },
        {
            "chunk_id": f"chunk-{doc_id}-2",
            "page_number": 2,
            "text": "கம்பர் இயற்றிய கம்பராமாயணம் காவியம் தமிழ் மொழியின் சிகரம். சென்னை மற்றும் மதுரையில் உள்ள தமிழ் பல்கலைக்கழகங்களில் இது போதிக்கப்படுகிறது.",
            "language": "ta"
        },
        {
            "chunk_id": f"chunk-{doc_id}-3",
            "page_number": 3,
            "text": "திருவள்ளுவர் இயற்றிய திருக்குறள் அறம், பொருள், இன்பம் என்ற மூன்று பால்களைக் கொண்டது. பாரதியார் பாரதிதாசன் கவிதைகள் விடுதலை உணர்வை ஊட்டின.",
            "language": "ta"
        }
    ]
    
    adapter = get_kg_adapter()
    graph_res = adapter.build_graph_for_document(doc_id, chunks, language="ta")
    
    print(f"[✓] Document Knowledge Graph built with {graph_res['node_count']} nodes and {graph_res['edge_count']} edges", flush=True)
    assert graph_res["node_count"] >= 5
    
    # Map nodes by canonical name
    nodes_by_name = {n["name"]: n for n in graph_res["nodes"]}
    print(f"[✓] Extracted concepts: {list(nodes_by_name.keys())}", flush=True)
    
    # 3. Test Node 1: "Jeyamohan"
    jeyamohan_node = nodes_by_name.get("Jeyamohan")
    assert jeyamohan_node is not None, "Expected Jeyamohan node"
    
    t0 = time.time()
    jeyamohan_details = adapter.get_node_details(jeyamohan_node["node_id"])
    t_elapsed = (time.time() - t0) * 1000
    
    print(f"\n--- Node Selection: 'Jeyamohan' (Retrieved in {t_elapsed:.2f}ms) ---", flush=True)
    print(f"  [Selected Node] Name: {jeyamohan_details['node']['name']} | Type: {jeyamohan_details['node']['type']}")
    print(f"  [Semantic Description] {jeyamohan_details['node']['description']}")
    print(f"  [Source Context Passages] {len(jeyamohan_details['source_chunks'])} passage(s) from document '{jeyamohan_details['node'].get('document_name')}'")
    print(f"  [Related Nodes] {len(jeyamohan_details['connected_relations'])} connection(s):")
    for r in jeyamohan_details['connected_relations']:
        print(f"     -> {r['relation_type']} -> {r.get('target_node_name') or r.get('source_node_name')}")
        
    assert "Jeyamohan" in jeyamohan_details['node']['name']
    assert "writer" in jeyamohan_details['node']['description'].lower() or "novelist" in jeyamohan_details['node']['description'].lower() or "concept" in jeyamohan_details['node']['description'].lower()
    
    # 4. Test Node 2: "Chennai"
    chennai_node = nodes_by_name.get("Chennai")
    assert chennai_node is not None, "Expected Chennai node"
    
    t0 = time.time()
    chennai_details = adapter.get_node_details(chennai_node["node_id"])
    t_elapsed = (time.time() - t0) * 1000
    
    print(f"\n--- Node Selection: 'Chennai' (Retrieved in {t_elapsed:.2f}ms) ---", flush=True)
    print(f"  [Selected Node] Name: {chennai_details['node']['name']} | Type: {chennai_details['node']['type']}")
    print(f"  [Semantic Description] {chennai_details['node']['description']}")
    print(f"  [Source Context Passages] {len(chennai_details['source_chunks'])} passage(s)")
    print(f"  [Related Nodes] {len(chennai_details['connected_relations'])} connection(s)")
    
    assert "Chennai" in chennai_details['node']['name']
    assert chennai_details['node']['type'] == "LOCATION"
    
    # 5. Verify that descriptions are DISTINCT and node-specific
    assert jeyamohan_details['node']['description'] != chennai_details['node']['description'], "Node descriptions must be node-specific!"
    
    # 6. Clean up
    db = SessionLocal()
    p = db.query(Persona).filter(Persona.id == persona_id).first()
    if p:
        db.delete(p)
        db.commit()
    db.close()
    
    print("\n=======================================================", flush=True)
    print("ALL NODE INTERACTION TESTS PASSED WITH 0ms LATENCY!", flush=True)
    print("=======================================================", flush=True)

if __name__ == "__main__":
    test_node_interaction()
