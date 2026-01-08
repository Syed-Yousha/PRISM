import os
import chromadb
from datasets import load_dataset
from chromadb.utils import embedding_functions

# CONFIGURATION
DB_PATH = os.path.join(os.path.dirname(__file__), "../vector_db")
COLLECTION_NAME = "prism_codebase"

def build_knowledge_base():
    print("📥 Downloading Bespoke-Manim dataset from Hugging Face...")
    # Load the high-quality Manim dataset
    dataset = load_dataset("bespokelabs/bespoke-manim", split="train")
    
    print(f"    ✅ Downloaded {len(dataset)} examples. Initializing Database...")

    # Setup ChromaDB (Persistent Storage)
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Reset/Create Collection
    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass
    
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"} # Optimized for semantic search
    )

    print("    💾 Ingesting data into Vector DB (this may take a minute)...")
    
    ids = []
    documents = []
    metadatas = []

    for i, row in enumerate(dataset):
        # We want to match based on Topic and Question
        search_content = f"Topic: {row['topic']}. Question: {row['question']}"
        
        # We want to retrieve the high-quality code
        code_snippet = row['python_code']
        style_desc = row['visual_style']
        
        ids.append(f"bespoke_{i}")
        documents.append(search_content)
        metadatas.append({
            "code": code_snippet[:6000], # Store code (limit size just in case)
            "style": style_desc[:1000]
        })

        # Batch add every 100 items to prevent memory spikes
        if (i + 1) % 100 == 0:
            collection.add(ids=ids, documents=documents, metadatas=metadatas)
            print(f"       Processed {i+1}/{len(dataset)}...")
            ids, documents, metadatas = [], [], []

    # Add remaining
    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    print(f"🎉 SUCCESS! Knowledge Base built at: {DB_PATH}")

if __name__ == "__main__":
    build_knowledge_base()