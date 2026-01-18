"""
Bespoke Manim Dataset Curator
==============================
Downloads and integrates the bespokelabs/bespoke-manim dataset from HuggingFace
into PRISM's knowledge base and RAG pipeline.

Dataset: https://huggingface.co/datasets/bespokelabs/bespoke-manim
"""

import os
import json
import requests
import time
from typing import List, Dict, Optional
from pathlib import Path

# Configuration
DATASET_API_URL = "https://datasets-server.huggingface.co/rows"
DATASET_NAME = "bespokelabs/bespoke-manim"
CONFIG = "default"
SPLIT = "train"

# Local storage paths
SCRIPT_DIR = Path(__file__).parent
CACHE_DIR = SCRIPT_DIR / "bespoke_cache"
KNOWLEDGE_DIR = SCRIPT_DIR.parent / "knowledge_base"


def fetch_dataset_rows(offset: int = 0, length: int = 100) -> Dict:
    """Fetch rows from the HuggingFace dataset API."""
    params = {
        "dataset": DATASET_NAME,
        "config": CONFIG,
        "split": SPLIT,
        "offset": offset,
        "length": length
    }
    
    try:
        response = requests.get(DATASET_API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"   ⚠️ Failed to fetch rows at offset {offset}: {e}")
        return {"rows": []}


def extract_manim_examples(data: Dict) -> List[Dict]:
    """Extract clean Manim code examples from dataset response."""
    examples = []
    
    for row_data in data.get("rows", []):
        row = row_data.get("row", {})
        
        # Extract key fields
        python_code = row.get("python_code", "")
        if not python_code or len(python_code) < 100:
            continue
            
        example = {
            "topic": row.get("topic", ""),
            "title": row.get("title", ""),
            "subject": row.get("subject", ""),
            "visual_style": row.get("visual_style", ""),
            "narration": row.get("narration", ""),
            "python_code": python_code,
            "scene_class_name": row.get("scene_class_name", ""),
            "equations": row.get("equations", []),
        }
        examples.append(example)
    
    return examples


def download_full_dataset(max_examples: int = 500) -> List[Dict]:
    """Download examples from the dataset."""
    print(f"📥 Downloading Bespoke Manim dataset (up to {max_examples} examples)...")
    
    all_examples = []
    offset = 0
    batch_size = 100
    
    while len(all_examples) < max_examples:
        print(f"   Fetching rows {offset} to {offset + batch_size}...")
        data = fetch_dataset_rows(offset=offset, length=batch_size)
        
        rows = data.get("rows", [])
        if not rows:
            print(f"   No more rows available.")
            break
            
        examples = extract_manim_examples(data)
        all_examples.extend(examples)
        print(f"   Got {len(examples)} valid examples (total: {len(all_examples)})")
        
        offset += batch_size
        time.sleep(0.5)  # Be nice to the API
        
        if len(rows) < batch_size:
            break
    
    return all_examples[:max_examples]


def save_to_cache(examples: List[Dict]) -> Path:
    """Save examples to local cache."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / "bespoke_manim_examples.json"
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2)
    
    print(f"   💾 Saved {len(examples)} examples to {cache_file}")
    return cache_file


def load_from_cache() -> Optional[List[Dict]]:
    """Load examples from local cache if available."""
    cache_file = CACHE_DIR / "bespoke_manim_examples.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                examples = json.load(f)
            print(f"   📂 Loaded {len(examples)} examples from cache")
            return examples
        except Exception as e:
            print(f"   ⚠️ Cache load failed: {e}")
    
    return None


def format_for_rag(examples: List[Dict]) -> str:
    """Format examples for RAG context injection."""
    rag_text = """
# BESPOKE MANIM EXAMPLES DATABASE
# ================================
# These are VERIFIED, WORKING Manim Community Edition code examples.
# Use these patterns as your primary reference for generating Manim code.

"""
    
    for i, ex in enumerate(examples[:50], 1):  # Limit to 50 for RAG context
        topic = ex.get("topic", "Unknown")
        title = ex.get("title", "")
        code = ex.get("python_code", "")
        style = ex.get("visual_style", "")
        
        # Clean up the code - remove very long examples
        if len(code) > 3000:
            code = code[:3000] + "\n# ... (truncated)"
        
        rag_text += f"""
## Example {i}: {topic} - {title}
Visual Style: {style[:200] if style else "Standard educational"}

```python
{code}
```

---
"""
    
    return rag_text


def create_knowledge_base_file(examples: List[Dict]) -> Path:
    """Create a knowledge base file from examples."""
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    kb_file = KNOWLEDGE_DIR / "bespoke_manim_examples.txt"
    
    content = format_for_rag(examples)
    
    with open(kb_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"   📚 Created knowledge base file: {kb_file} ({len(content):,} chars)")
    return kb_file


def get_bespoke_examples(force_refresh: bool = False) -> List[Dict]:
    """Get Bespoke Manim examples (from cache or download)."""
    if not force_refresh:
        cached = load_from_cache()
        if cached:
            return cached
    
    # Download fresh
    examples = download_full_dataset(max_examples=300)
    if examples:
        save_to_cache(examples)
        create_knowledge_base_file(examples)
    
    return examples


def get_bespoke_rag_context(max_chars: int = 15000) -> str:
    """Get formatted RAG context from Bespoke examples."""
    examples = get_bespoke_examples()
    
    if not examples:
        return ""
    
    rag_text = format_for_rag(examples)
    
    # Truncate to max chars
    if len(rag_text) > max_chars:
        rag_text = rag_text[:max_chars] + "\n\n# ... (more examples available)"
    
    return rag_text


def initialize_bespoke_database():
    """Initialize the Bespoke database on first run."""
    print("\n🎬 Initializing Bespoke Manim Database...")
    
    examples = get_bespoke_examples(force_refresh=False)
    
    if examples:
        print(f"   ✅ Bespoke database ready: {len(examples)} verified Manim examples")
        
        # Create knowledge base file
        kb_file = create_knowledge_base_file(examples)
        
        # Show sample topics
        topics = set(ex.get("subject", "")[:30] for ex in examples[:20])
        print(f"   📚 Topics: {', '.join(t for t in topics if t)[:100]}...")
        
        return True
    else:
        print("   ⚠️ Failed to initialize Bespoke database")
        return False


if __name__ == "__main__":
    # Test the curator
    print("=" * 60)
    print("Bespoke Manim Dataset Curator")
    print("=" * 60)
    
    # Initialize
    success = initialize_bespoke_database()
    
    if success:
        # Get RAG context sample
        context = get_bespoke_rag_context(max_chars=5000)
        print(f"\n📝 Sample RAG context ({len(context):,} chars):")
        print("-" * 40)
        print(context[:2000])
        print("-" * 40)
