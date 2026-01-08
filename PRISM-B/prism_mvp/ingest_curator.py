"""
PRISM Curator Ingestion - Knowledge Base Builder
================================================
Downloads verified Manim code from Bespoke Labs and stores in ChromaDB.

Dataset: bespokelabs/bespoke-manim (Hugging Face)
Storage: ChromaDB with batch processing

Usage:
    python ingest_curator.py          # Full ingestion
    python ingest_curator.py --test   # Test with 10 samples
"""

import os
import sys
import argparse
import hashlib
from typing import List, Dict

import chromadb
from datasets import load_dataset

# ============== CONFIGURATION ==============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(BASE_DIR, "vector_db")

DATASET_NAME = "bespokelabs/bespoke-manim"
COLLECTION_NAME = "prism_codebase"
BATCH_SIZE = 100  # Process in batches to prevent memory issues


def create_document(prompt: str, code: str) -> str:
    """
    Format a dataset row into a searchable document.
    
    Args:
        prompt: User request/task description
        code: Manim code solution
        
    Returns:
        Formatted document string for embedding
    """
    return f"""Task: {prompt}

Code:
{code}"""


def generate_id(text: str) -> str:
    """Generate unique ID from text content."""
    return hashlib.md5(text.encode()).hexdigest()[:16]


def ingest_dataset(test_mode: bool = False, max_samples: int = None):
    """
    Download and ingest Bespoke Manim dataset into ChromaDB.
    
    Args:
        test_mode: If True, only process 10 samples
        max_samples: Optional limit on number of samples
    """
    print("\n" + "═" * 60)
    print("   🔮 PRISM Knowledge Base Builder")
    print("   Dataset: bespokelabs/bespoke-manim")
    print("═" * 60)
    
    # ═══ STEP 1: Load Dataset ═══
    print("\n📥 Loading dataset from Hugging Face...")
    
    try:
        dataset = load_dataset(DATASET_NAME, split="train")
        total_rows = len(dataset)
        print(f"   ✅ Loaded {total_rows:,} examples")
    except Exception as e:
        print(f"   ❌ Failed to load dataset: {e}")
        print("   💡 Run: pip install datasets")
        return
    
    # Limit samples if requested
    if test_mode:
        max_samples = 10
        print(f"   🧪 TEST MODE: Processing only {max_samples} samples")
    
    if max_samples:
        dataset = dataset.select(range(min(max_samples, total_rows)))
        total_rows = len(dataset)
    
    # ═══ STEP 2: Connect to ChromaDB ═══
    print(f"\n📦 Connecting to ChromaDB at: {DB_PATH}")
    os.makedirs(DB_PATH, exist_ok=True)
    
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Delete existing collection if it exists (fresh start)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"   🗑️  Deleted existing collection: {COLLECTION_NAME}")
    except Exception:
        pass
    
    # Create new collection
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Bespoke Manim code examples for PRISM"}
    )
    print(f"   ✅ Created collection: {COLLECTION_NAME}")
    
    # ═══ STEP 3: Batch Processing ═══
    print(f"\n⚙️  Processing {total_rows:,} examples in batches of {BATCH_SIZE}...")
    
    documents: List[str] = []
    metadatas: List[Dict] = []
    ids: List[str] = []
    
    processed = 0
    skipped = 0
    
    for i, row in enumerate(dataset):
        # Extract fields from bespokelabs/bespoke-manim dataset
        # Dataset columns: subject, topic, question, title, narration, python_code, etc.
        prompt = row.get("question") or row.get("title") or ""
        code = row.get("python_code") or ""
        topic = row.get("topic") or ""
        subject = row.get("subject") or ""
        
        if not prompt or not code:
            skipped += 1
            continue
        
        # Create document
        doc = create_document(prompt, code)
        doc_id = generate_id(doc)
        
        # Metadata for filtering and retrieval
        metadata = {
            "prompt": prompt[:500],  # Truncate for storage
            "code": code[:5000],     # Keep full code (up to 5k chars)
            "topic": topic[:100],
            "subject": subject[:100],
            "source": "bespoke-manim",
            "index": i
        }
        
        documents.append(doc)
        metadatas.append(metadata)
        ids.append(doc_id)
        
        # Batch insert when we hit BATCH_SIZE
        if len(documents) >= BATCH_SIZE:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            processed += len(documents)
            print(f"   📊 Processed: {processed:,}/{total_rows:,} ({100*processed/total_rows:.1f}%)")
            
            # Clear batch
            documents = []
            metadatas = []
            ids = []
    
    # Insert remaining documents
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        processed += len(documents)
    
    # ═══ STEP 4: Summary ═══
    print("\n" + "═" * 60)
    print("   ✅ INGESTION COMPLETE")
    print("═" * 60)
    print(f"   📊 Total processed: {processed:,}")
    print(f"   ⏭️  Skipped (empty): {skipped:,}")
    print(f"   📦 Collection: {COLLECTION_NAME}")
    print(f"   📁 Database: {DB_PATH}")
    print("═" * 60)
    
    # Verify
    print(f"\n🔍 Verification: Collection has {collection.count():,} documents")


def test_query():
    """Test querying the ingested database."""
    print("\n🧪 Testing query functionality...")
    
    client = chromadb.PersistentClient(path=DB_PATH)
    
    try:
        collection = client.get_collection(COLLECTION_NAME)
        print(f"   ✅ Connected to collection: {COLLECTION_NAME}")
        print(f"   📊 Document count: {collection.count():,}")
    except Exception as e:
        print(f"   ❌ Collection not found: {e}")
        print("   💡 Run ingestion first: python ingest_curator.py")
        return
    
    # Test queries
    test_queries = [
        "Pythagorean theorem triangle",
        "3D sphere rotation",
        "mathematical graph plotting"
    ]
    
    for query in test_queries:
        print(f"\n   🔍 Query: '{query}'")
        
        results = collection.query(
            query_texts=[query],
            n_results=2
        )
        
        if results['ids'][0]:
            for i, (doc_id, metadata) in enumerate(zip(results['ids'][0], results['metadatas'][0])):
                prompt = metadata.get('prompt', '')[:80]
                print(f"      [{i+1}] {prompt}...")
        else:
            print("      No results found")


# ============== CLI ==============
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PRISM Knowledge Base Ingestion")
    parser.add_argument("--test", action="store_true", help="Test mode: process only 10 samples")
    parser.add_argument("--max", type=int, help="Maximum samples to process")
    parser.add_argument("--query", action="store_true", help="Test query functionality")
    
    args = parser.parse_args()
    
    if args.query:
        test_query()
    else:
        ingest_dataset(test_mode=args.test, max_samples=args.max)
        
        # Run test query after ingestion
        print("\n" + "─" * 60)
        test_query()
