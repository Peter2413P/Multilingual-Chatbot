import os
import sys

# Configure UTF-8 on stdout if supported
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.db.session import SessionLocal, engine, Base
import app.db.models
from app.db.models import Persona, KnowledgeSource, KnowledgeNode, KnowledgeEdge
from app.services.kg_adapter import get_kg_adapter

def test_kg_integration():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Create a test persona and test knowledge source
    persona = db.query(Persona).first()
    if not persona:
        persona = Persona(name="Test Author Persona")
        db.add(persona)
        db.commit()
        db.refresh(persona)
        
    doc = KnowledgeSource(
        persona_id=persona.id,
        name="jeyamohan_aram_sample.txt",
        source_type="UPLOAD",
        original_filename="jeyamohan_aram_sample.txt",
        status="PROCESSING"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    doc_id = doc.id
    db.close()
    
    print(f"Created test doc: {doc_id}")
    
    # 2. Simulate chunks
    sample_chunks = [
        {
            "chunk_id": f"chunk-{doc_id}-1",
            "page_number": 1,
            "text": "ஜெயமோகன் ஒரு புகழ்பெற்ற தமிழ் எழுத்தாளர். இவர் அறம் என்ற சிறுகதைத் தொகுப்பை எழுதியுள்ளார்.",
            "language": "ta"
        },
        {
            "chunk_id": f"chunk-{doc_id}-2",
            "page_number": 2,
            "text": "அறம் நூலில் பல தத்துவக் கருத்துக்கள் விளக்கப்பட்டுள்ளன. ஜெயமோகன் மகாபாரதம் கதையை அடிப்படையாகக் கொண்டு வெண்முரசு நாவலை எழுதினார். சென்னை மற்றும் மதுரையில் உள்ள இலக்கிய கூட்டங்களில் இவர் உரையாற்றியுள்ளார்.",
            "language": "ta"
        }
    ]
    
    adapter = get_kg_adapter()
    graph_res = adapter.build_graph_for_document(doc_id, sample_chunks, language="ta")
    
    print("\n=== GRAPH GENERATION RESULT ===")
    print(f"Nodes Count: {graph_res['node_count']}")
    print(f"Edges Count: {graph_res['edge_count']}")
    
    assert graph_res['node_count'] >= 2, "Expected at least 2 nodes"
    assert graph_res['edge_count'] >= 1, "Expected at least 1 edge"
    
    # Test Node Details
    first_node_id = graph_res['nodes'][0]['node_id']
    details = adapter.get_node_details(first_node_id)
    print(f"\nNode Details for '{details['node']['name']}':")
    print(f"  Type: {details['node']['type']}")
    print(f"  Description: {details['node']['description']}")
    print(f"  Connected Relations: {len(details['connected_relations'])}")
    print("\n>>> ALL KG INTEGRATION TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_kg_integration()
