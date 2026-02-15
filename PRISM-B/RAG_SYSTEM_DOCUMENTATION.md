# PRISM RAG System Documentation

## Overview

PRISM uses a dual-collection RAG (Retrieval-Augmented Generation) system that combines two knowledge sources:

1. **Bespoke Curator Collection** (`prism_codebase`): External Manim examples from bespokelabs/bespoke-manim dataset
2. **Local Knowledge Base Collection** (`prism_local_kb`): Curated IGCSE/O-Level math examples and PRISM style guides

This system ensures the LLM receives high-quality, relevant Manim code examples for generating educational videos.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRISM RAG Engine                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ Bespoke Curator │    │     Local Knowledge Base         │ │
│  │   Collection    │    │        Collection                │ │
│  │ (prism_codebase)│    │    (prism_local_kb)             │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│           │                           │                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Semantic Search & Retrieval                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Context Aggregation                         │ │
│  │  • Bespoke Examples (highest priority)                  │ │
│  │  • Local KB Examples (IGCSE topics)                     │ │
│  │  • Built-in Reference (fallback)                        │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │   LLM Prompt     │
                           │  Generation      │
                           └─────────────────┘
```

## Collection Details

### 1. Bespoke Curator Collection (`prism_codebase`)

**Source**: bespokelabs/bespoke-manim Hugging Face dataset  
**Purpose**: Verified, working Manim code examples  
**Metadata Fields**:
- `prompt`: User task description
- `code`: Manim code solution  
- `topic`: Mathematical topic
- `subject`: Subject area
- `source`: "bespoke-manim"
- `index`: Dataset index

**Ingestion Script**: `ingest_curator.py`

### 2. Local Knowledge Base Collection (`prism_local_kb`)

**Source**: `knowledge_base/` directory (48 .txt files)  
**Purpose**: IGCSE/O-Level curriculum examples and PRISM style guides  
**Metadata Fields**:
- `topic`: Folder path (e.g., "06_igcse_number")
- `filename`: File name without extension
- `category`: Auto-classified (igcse_curriculum, manim_features, style_guide, etc.)
- `section`: Section within file (extracted from headers)
- `type`: "code" or "text"
- `start_line`: Line number in source file
- `chunk_size`: Character count
- `relative_path`: Path relative to knowledge_base/
- `source`: "prism_local_kb"

**Ingestion Script**: `ingest_local_kb.py`

## Usage Workflow

### Initial Setup

1. **Ingest Bespoke Dataset** (optional but recommended):
```bash
cd prism_mvp
python ingest_curator.py --test  # Test with 10 samples
python ingest_curator.py         # Full ingestion
```

2. **Ingest Local Knowledge Base**:
```bash
cd prism_mvp
python ingest_local_kb.py --test  # Test with 5 files
python ingest_local_kb.py          # Full ingestion
```

3. **Verify Both Collections**:
```bash
python rag_engine.py  # Runs built-in test suite
```

### Query Processing

When a user requests a topic (e.g., "Pythagorean Theorem"):

1. **Semantic Search**: Both collections are queried simultaneously
2. **Context Assembly**: Results are combined with priority ordering:
   - Bespoke examples (verified external code)
   - Local KB examples (curriculum-specific)
   - Built-in reference (fallback syntax)
3. **LLM Prompt**: Combined context is sent to the LLM for code generation

### Search Capabilities

The RAG engine provides multiple search methods:

```python
from rag_engine import RAGEngine

engine = RAGEngine()

# Get combined context for LLM
context = engine.get_context("Pythagorean Theorem", n_results=3)

# Structured search results
results = engine.search("3D rotation animation", n_results=5)

# Mode-specific examples
examples_3d = engine.get_examples_for_mode("3D")
examples_2d = engine.get_examples_for_mode("2D")
```

## File Structure

### Knowledge Base Organization

```
knowledge_base/
├── 00_style_guide/           # PRISM visual standards
├── 01_basics/                # Basic Manim shapes/text
├── 02_3d_scenes/             # 3D scenes and camera
├── 03_animations/            # Animation techniques
├── 04_graphs/                # Plotting and graphs
├── 05_educational_visuals/   # General educational examples
├── 06_igcse_number/          # IGCSE Number topics
├── 07_igcse_algebra/         # IGCSE Algebra
├── 08_igcse_geometry/        # IGCSE Geometry
├── 09_igcse_trigonometry/    # IGCSE Trigonometry
├── 10_igcse_statistics/      # IGCSE Statistics
├── 11_igcse_mensuration/     # IGCSE Mensuration
├── 12_igcse_sets_matrices/   # IGCSE Sets & Matrices
├── 13_igcse_vectors/         # IGCSE Vectors
├── 14_igcse_functions/       # IGCSE Functions
├── 15_official_examples/     # Manim documentation examples
├── 16_advanced_features/     # Advanced Manim features
└── bespoke_manim_examples.txt # Additional examples
```

### Vector Database Structure

```
vector_db/
├── chroma.sqlite3           # Main database file
├── prism_codebase/          # Bespoke collection data
└── prism_local_kb/          # Local KB collection data
```

## Ingestion Scripts

### ingest_curator.py

**Purpose**: Download and ingest bespokelabs/bespoke-manim dataset  
**Key Features**:
- Batch processing (100 examples per batch)
- Automatic duplicate detection
- Metadata extraction from dataset fields
- Test mode for development

**Usage**:
```bash
python ingest_curator.py [--test] [--max N] [--query]
```

### ingest_local_kb.py

**Purpose**: Ingest local .txt files into vector database  
**Key Features**:
- Recursive directory scanning
- Intelligent chunking by code blocks and sections
- Rich metadata extraction
- Category auto-classification
- Test mode and statistics

**Usage**:
```bash
python ingest_local_kb.py [--test] [--max N] [--stats] [--query]
```

**Chunking Strategy**:
1. **Code Block Detection**: Splits on ```python blocks
2. **Section Headers**: Detects `## Section Name` patterns
3. **Size Limits**: Chunks limited to 2000 characters
4. **Metadata Preservation**: Tracks source file, line numbers, section

## RAG Engine API

### RAGEngine Class

**Constructor**:
```python
RAGEngine(db_path: str = DB_PATH)
```

**Key Methods**:
- `get_context(topic: str, n_results: int = 3) -> str`
- `search(query: str, n_results: int = 5) -> List[Dict]`
- `get_examples_for_mode(mode: str, n_results: int = 2) -> List[Dict]`
- `get_reference() -> str`
- `clear_cache()`

**Properties**:
- `is_connected`: Any database connected
- `curator_connected`: Bespoke collection status
- `local_kb_connected`: Local KB collection status
- `document_count`: Dict with counts per collection

### Search Result Format

```python
{
    'prompt': 'Task description or topic/section',
    'code': 'Manim code (if available)',
    'relevance': 0.85,  # 0-1 score
    'source': 'bespoke_curator' | 'prism_local_kb',
    'topic': 'Topic name',
    'section': 'Section name',  # Local KB only
    'filename': 'source_file',   # Local KB only
    'type': 'code' | 'text'      # Local KB only
}
```

## Configuration

### config.py Settings

```python
# Paths
DB_PATH = os.path.join(BASE_DIR, "vector_db")
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "knowledge_base")

# RAG Settings
COLLECTION_NAME = "prism_codebase"           # Bespoke collection
DEFAULT_N_RESULTS = 3                         # Results per collection

# Local KB Collection (defined in rag_engine.py)
LOCAL_KB_COLLECTION_NAME = "prism_local_kb"
```

## Maintenance and Troubleshooting

### Common Issues

1. **Collection Not Found**:
   - Run ingestion scripts first
   - Check `vector_db/` directory exists
   - Verify ChromaDB installation

2. **Poor Search Results**:
   - Check query terms match content
   - Verify embeddings are using same model
   - Consider re-ingestion with updated content

3. **Memory Issues**:
   - Reduce batch size in ingestion scripts
   - Use `--max` parameter to limit processing
   - Monitor system resources during ingestion

### Performance Optimization

1. **Caching**: RAG engine caches query results automatically
2. **Batch Processing**: Ingestion uses configurable batch sizes
3. **Chunk Size**: Local KB chunks limited to prevent token overflow
4. **Connection Pooling**: ChromaDB client reused across queries

### Updating Content

1. **Add New Files**: Place .txt files in appropriate `knowledge_base/` subfolder
2. **Re-ingest**: Run `python ingest_local_kb.py` to update vector DB
3. **Update Bespoke**: Run `python ingest_curator.py` for latest dataset

### Backup and Recovery

```bash
# Backup vector database
cp -r vector_db/ vector_db_backup/

# Restore from backup
cp -r vector_db_backup/ vector_db/

# Clear specific collection (if needed)
python -c "
import chromadb
client = chromadb.PersistentClient('vector_db')
client.delete_collection('prism_local_kb')
"
```

## Development Guidelines

### Adding New Knowledge Base Categories

1. Create new folder in `knowledge_base/` with descriptive name
2. Follow naming convention: `XX_category_description`
3. Use `.txt` files with clear section headers (`## Section Name`)
4. Include code blocks with ```python fencing
5. Re-run ingestion script

### Extending Metadata

1. Modify `extract_metadata_from_path()` in `ingest_local_kb.py`
2. Update chunking logic if needed
3. Re-ingest to apply changes
4. Update search result processing in `rag_engine.py`

### Testing New Features

1. Use `--test` flags on ingestion scripts
2. Run `python rag_engine.py` for comprehensive testing
3. Test specific queries with search methods
4. Verify context assembly with `get_context()`

## Best Practices

1. **Content Quality**:
   - Ensure code examples are tested and working
   - Use clear, descriptive section headers
   - Include both code and explanatory text

2. **Query Design**:
   - Use specific, relevant terms
   - Include mathematical concepts when appropriate
   - Test multiple query variations

3. **Performance**:
   - Monitor database size and query times
   - Use appropriate batch sizes for ingestion
   - Clear cache if memory becomes an issue

4. **Maintenance**:
   - Regularly update both collections
   - Monitor search result quality
   - Backup vector database regularly

This documentation provides a comprehensive guide for understanding, maintaining, and extending the PRISM RAG system. The dual-collection approach ensures both breadth (external examples) and depth (curriculum-specific content) for optimal educational video generation.
