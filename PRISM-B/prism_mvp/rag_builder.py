"""
PRISM RAG Builder - Manim Knowledge Base
Builds vector database from Manim syntax guides.
"""

import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# PATHS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "knowledge_base")
DB_PATH = os.path.join(BASE_DIR, "vector_db")


def build_database():
    """Build/rebuild the Manim knowledge vector database."""
    
    print("="*50)
    print("   🔧 PRISM RAG Builder")
    print("="*50)
    
    print(f"\n📚 Loading from: {KNOWLEDGE_PATH}")
    
    # Load all .txt files
    loader = DirectoryLoader(
        KNOWLEDGE_PATH, 
        glob="*.txt", 
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    docs = loader.load()
    
    if not docs:
        print("❌ No .txt files found in knowledge_base/")
        return False

    print(f"   Found {len(docs)} document(s)")
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n===", "\n\n", "\n", " "]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"   Split into {len(chunks)} chunks")

    # Create embeddings (local, free, unlimited)
    print("\n💾 Creating vector database...")
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Remove old DB if exists
    if os.path.exists(DB_PATH):
        import shutil
        shutil.rmtree(DB_PATH)
        print("   Removed old database")
    
    # Create new DB
    db = Chroma.from_documents(
        chunks, 
        embedding_model, 
        persist_directory=DB_PATH
    )
    
    print("\n✅ SUCCESS! Database ready at:", DB_PATH)
    print(f"   Total vectors: {db._collection.count()}")
    
    # Test query
    print("\n🔍 Test query: 'how to create shapes'")
    results = db.similarity_search("how to create shapes", k=2)
    for i, doc in enumerate(results, 1):
        preview = doc.page_content[:100].replace("\n", " ")
        print(f"   {i}. {preview}...")
    
    return True


if __name__ == "__main__":
    build_database()