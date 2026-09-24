import os
import sys
import io
import unittest

# Configure UTF-8 encoding for Windows consoles
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure app is in python path
sys.path.insert(0, os.path.dirname(__file__))

from app.tamil.tamil_cleaner import clean_tamil_text
from app.tamil.tamil_chunker import split_tamil_text, chunk_tamil_document
from app.tamil.tamil_vector_store import get_tamil_vector_store
from app.tamil.tamil_retriever import retrieve_tamil_context
from app.rag.database import get_vector_store as get_english_vector_store

class TestTamilPipeline(unittest.TestCase):

    def test_01_tamil_cleaner(self):
        print("\n--- Testing Tamil Cleaner ---")
        raw_text = "  சிலப்பதிகாரம்   தமிழின் ஐம்பெரும் காப்பியங்களில் ஒன்றாகும்.\x00\ufffd\n\n\nஇதனை இளங்கோவடிகள் இயற்றினார்.  "
        cleaned = clean_tamil_text(raw_text)
        print("Cleaned text:", cleaned)
        
        # Verify Unicode Tamil characters preserved
        self.assertIn("சிலப்பதிகாரம்", cleaned)
        self.assertIn("இளங்கோவடிகள்", cleaned)
        # Verify null bytes and replacement chars removed
        self.assertNotIn("\x00", cleaned)
        self.assertNotIn("\ufffd", cleaned)
        # Verify paragraph boundary preserved
        self.assertIn("\n\n", cleaned)
        print("✓ Tamil Cleaner test passed.")

    def test_02_tamil_chunker(self):
        print("\n--- Testing Tamil Chunker ---")
        sample_doc = (
            "திருக்குறள் (Thirukkural) தமிழ் மொழியில் எழுதப்பட்ட உலகப் பொதுமறை நூலாகும்.\n\n"
            "அகர முதல எழுத்தெல்லாம் ஆதி\nபகவன் முதற்றே உலகு.\n\n"
            "கற்றதனால் ஆய பயன்கொல் வாலறிவன்\nநற்றாள் தொழாஅர் எனின்."
        )
        meta = {
            "source_name": "thirukkural.txt",
            "page_number": 1,
            "persona_id": "test_persona_ta"
        }
        chunks = chunk_tamil_document(sample_doc, meta, chunk_size=300)
        print(f"Generated {len(chunks)} chunks.")
        for idx, c in enumerate(chunks):
            print(f"Chunk {idx}: {c.page_content[:60]}... (Metadata: {c.metadata})")
            self.assertEqual(c.metadata["language"], "ta")
            self.assertEqual(c.metadata["persona_id"], "test_persona_ta")
            self.assertEqual(c.metadata["page_number"], 1)
        self.assertTrue(len(chunks) >= 1)
        print("✓ Tamil Chunker test passed.")

    def test_03_tamil_embeddings_and_vector_store_isolation(self):
        print("\n--- Testing Tamil Vector Store & Isolation from English ---")
        tamil_vs = get_tamil_vector_store()
        english_vs = get_english_vector_store()
        
        # Verify collection names are distinct
        self.assertEqual(tamil_vs._collection.name, "persona_forge_docs_ta")
        self.assertEqual(english_vs._collection.name, "persona_forge_docs")
        print(f"Tamil collection: {tamil_vs._collection.name}")
        print(f"English collection: {english_vs._collection.name}")
        print("✓ Collection isolation verified.")

    def test_04_tamil_ingest_and_retrieval(self):
        print("\n--- Testing Tamil Ingestion & Direct Retrieval ---")
        persona_id = "test_persona_silappathikaram"
        tamil_text = (
            "சிலப்பதிகாரம் தமிழின் ஐம்பெரும் காப்பியங்களில் ஒன்றாகும். "
            "இதனை இளங்கோவடிகள் இயற்றினார். "
            "இதில் கோவலன் மற்றும் கண்ணகி முதன்மைக் கதாபாத்திரங்கள் ஆவர்."
        )
        meta = {
            "persona_id": persona_id,
            "knowledge_source_id": "doc_silappathikaram_001",
            "source_name": "silappathikaram.txt",
            "page_number": 1,
            "input_type": "text"
        }
        docs = chunk_tamil_document(tamil_text, meta)
        
        tamil_vs = get_tamil_vector_store()
        tamil_vs.add_documents(docs)
        
        # Query in direct Tamil
        query = "சிலப்பதிகாரத்தை இயற்றியவர் யார்?"
        context, sources = retrieve_tamil_context(query=query, persona_id=persona_id, top_k=3)
        
        print(f"Query: {query}")
        print(f"Retrieved Context: {context}")
        print(f"Retrieved Sources: {sources}")
        
        self.assertIn("இளங்கோவடிகள்", context)
        self.assertTrue(len(sources) > 0)
        self.assertEqual(sources[0]["language"], "ta")
        
        # Cleanup test vectors
        tamil_vs._collection.delete(where={"persona_id": persona_id})
        print("✓ Direct Tamil retrieval test passed.")

    def test_05_english_regression_untouched(self):
        print("\n--- Testing English Regression (English Pipeline Untouched) ---")
        english_vs = get_english_vector_store()
        from langchain_core.documents import Document
        
        persona_id = "test_persona_en_regression"
        en_doc = Document(
            page_content="The sun rises in the east and sets in the west.",
            metadata={"persona_id": persona_id, "source_name": "astronomy.txt"}
        )
        english_vs.add_documents([en_doc])
        
        results = english_vs.similarity_search("Where does the sun rise?", k=1, filter={"persona_id": persona_id})
        self.assertTrue(len(results) > 0)
        self.assertIn("east", results[0].page_content)
        
        # Cleanup
        english_vs._collection.delete(where={"persona_id": persona_id})
        print("✓ English regression test passed.")

if __name__ == "__main__":
    unittest.main()
