"""
PRISM RAG Engine - Knowledge Bridge
===================================
Connects to the Bespoke Curator database for intelligent code retrieval.

ARCHITECTURE:
- Database: ChromaDB (vector_db/prism_codebase)
- Source: bespokelabs/bespoke-manim dataset
- Purpose: Provide accurate Manim syntax to prevent LLM hallucinations

FEATURES:
1. Semantic search for topic-relevant examples
2. Returns top 3 diverse code snippets
3. Built-in fallback reference for guaranteed syntax
4. Caching for repeated queries
5. Bespoke Manim dataset integration for verified examples
"""

import os
import chromadb
from typing import List, Dict, Optional
from functools import lru_cache

from config import DB_PATH, KNOWLEDGE_BASE_PATH, COLLECTION_NAME, DEFAULT_N_RESULTS

# Import Bespoke curator for verified Manim examples
try:
    from bespoke_curator import get_bespoke_rag_context, get_bespoke_examples, initialize_bespoke_database
    BESPOKE_AVAILABLE = True
except ImportError:
    BESPOKE_AVAILABLE = False
    print("   ⚠️ Bespoke curator not available, using built-in reference only")


# ============== LOCAL KNOWLEDGE BASE LOADER ==============
def load_local_knowledge_base() -> str:
    """
    Load all .txt files from the knowledge_base folder.
    This provides PRISM-specific 3Blue1Brown style examples.
    
    Returns:
        Concatenated content from all knowledge base files
    """
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        return ""
    
    knowledge = []
    knowledge.append("\n" + "=" * 70)
    knowledge.append("🎨 PRISM STYLE GUIDE - 3Blue1Brown / Khan Academy Standards")
    knowledge.append("=" * 70 + "\n")
    
    # Priority order for loading
    priority_folders = [
        "00_style_guide",
        "01_basics",
        "02_3d_scenes",
        "03_animations",
        "04_graphs",
        "05_educational_visuals",  # Topic-specific visual examples (fractions, vectors, etc.)
        "06_igcse_number",         # IGCSE Number topics (integers, HCF/LCM, ratio, percentages, etc.)
        "07_igcse_algebra",        # IGCSE Algebra (expressions, equations, inequalities, sequences)
        "08_igcse_geometry",       # IGCSE Geometry (angles, polygons, circles, transformations)
        "09_igcse_trigonometry",   # IGCSE Trigonometry (SOH CAH TOA, sine/cosine rules, graphs)
        "10_igcse_statistics",     # IGCSE Statistics & Probability (averages, charts, probability)
        "11_igcse_mensuration",    # IGCSE Mensuration (area, perimeter, volume, surface area)
        "12_igcse_sets_matrices",  # IGCSE Sets & Matrices (Venn diagrams, matrix operations)
        "13_igcse_vectors",        # IGCSE Vectors (column vectors, magnitude, position vectors)
        "14_igcse_functions"       # IGCSE Functions (notation, composite, inverse functions)
    ]
    
    for folder in priority_folders:
        folder_path = os.path.join(KNOWLEDGE_BASE_PATH, folder)
        if os.path.exists(folder_path):
            for filename in sorted(os.listdir(folder_path)):
                if filename.endswith('.txt'):
                    filepath = os.path.join(folder_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            knowledge.append(f"\n{'─' * 60}")
                            knowledge.append(f"📚 {folder}/{filename}")
                            knowledge.append("─" * 60)
                            knowledge.append(content)
                    except Exception:
                        pass
    
    # Also scan root level if any loose files
    for filename in sorted(os.listdir(KNOWLEDGE_BASE_PATH)):
        filepath = os.path.join(KNOWLEDGE_BASE_PATH, filename)
        if os.path.isfile(filepath) and filename.endswith('.txt'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    knowledge.append(f"\n{'─' * 60}")
                    knowledge.append(f"📚 {filename}")
                    knowledge.append("─" * 60)
                    knowledge.append(content)
            except Exception:
                pass
    
    if len(knowledge) > 3:  # More than just headers
        knowledge.append("\n" + "=" * 70)
        knowledge.append("END PRISM STYLE GUIDE")
        knowledge.append("=" * 70 + "\n")
        return "\n".join(knowledge)
    
    return ""


# Cache the local knowledge base (loaded once)
_LOCAL_KB_CACHE = None

def get_local_knowledge_base() -> str:
    """Get cached local knowledge base content."""
    global _LOCAL_KB_CACHE
    if _LOCAL_KB_CACHE is None:
        _LOCAL_KB_CACHE = load_local_knowledge_base()
    return _LOCAL_KB_CACHE


# ============== BUILT-IN REFERENCE ==============
# Guaranteed valid Manim CE syntax (fallback & baseline)
MANIM_REFERENCE = """
=== MANIM COMMUNITY EDITION SYNTAX REFERENCE ===

### IMPORTS (REQUIRED AT TOP) ###
from manim import *
import numpy as np

### SCENE STRUCTURE ###
class GenScene(ThreeDScene):
    def construct(self):
        # 2D Camera Setup
        self.set_camera_orientation(phi=0*DEGREES, theta=-90*DEGREES)
        
        # 3D Camera Setup
        self.set_camera_orientation(phi=75*DEGREES, theta=-45*DEGREES)
        
        # Your animations here
        self.wait(0.5)

### TEXT HANDLING (CRITICAL FOR 3D SCENES) ###
# ALWAYS use add_fixed_in_frame_mobjects() BEFORE positioning text!

title = Tex(r"\\textbf{Title}", font_size=48, color=YELLOW)
self.add_fixed_in_frame_mobjects(title)  # MUST BE BEFORE to_edge/move_to!
title.to_edge(UP)
self.play(Write(title), run_time=1.0)

formula = MathTex(r"a^2 + b^2 = c^2", font_size=40, color=WHITE)
self.add_fixed_in_frame_mobjects(formula)
formula.move_to(LEFT * 4 + UP * 2)
self.play(Write(formula), run_time=1.5)

# Bullet points
bullet = Tex(r"\\bullet Point one", font_size=32)
self.add_fixed_in_frame_mobjects(bullet)
bullet.move_to(LEFT * 5)

### 2D SHAPES ###
circle = Circle(radius=1.5, color=BLUE, fill_opacity=0.3)
circle.move_to(RIGHT * 2.5)

square = Square(side_length=2, color=TEAL, stroke_width=3)
triangle = Polygon(ORIGIN, RIGHT*2, RIGHT+UP*1.5, color=YELLOW, fill_opacity=0.5)
rectangle = Rectangle(width=3, height=2, color=GREEN)
line = Line(start=LEFT*2, end=RIGHT*2, color=WHITE)
arrow = Arrow(start=ORIGIN, end=RIGHT*2+UP, color=TEAL, buff=0)
dot = Dot(point=ORIGIN, color=RED, radius=0.1)

# Axes (2D)
axes = Axes(
    x_range=[-3, 3, 1],
    y_range=[-2, 4, 1],
    x_length=6,
    y_length=4,
    axis_config={"color": BLUE}
).shift(RIGHT * 2)

# Function plotting
graph = axes.plot(lambda x: x**2, color=YELLOW)
graph_label = axes.get_graph_label(graph, label="y=x^2")

### 3D SHAPES ###
sphere = Sphere(radius=1, color=BLUE, fill_opacity=0.7)
sphere.move_to(RIGHT * 2.5)

cube = Cube(side_length=1.5, color=TEAL, fill_opacity=0.5)
cone = Cone(base_radius=1, height=2, color=YELLOW)
cylinder = Cylinder(radius=0.5, height=2, color=GREEN)

# 3D Axes
axes3d = ThreeDAxes(
    x_range=[-3, 3, 1],
    y_range=[-3, 3, 1],
    z_range=[-2, 2, 1]
)

# 3D Arrow
arrow3d = Arrow3D(start=ORIGIN, end=[2, 1, 1], color=YELLOW)

# Surface
surface = Surface(
    lambda u, v: np.array([u, v, u**2 + v**2]),
    u_range=[-2, 2],
    v_range=[-2, 2],
    fill_opacity=0.5
)

### ANIMATIONS ###
# Creation
self.play(Create(shape), run_time=1.5)
self.play(Write(text), run_time=1.0)
self.play(FadeIn(obj), run_time=0.5)
self.play(DrawBorderThenFill(shape), run_time=1.5)

# Transformation
self.play(Transform(obj_a, obj_b), run_time=1.5)
self.play(ReplacementTransform(obj_a, obj_b), run_time=1.0)
self.play(obj.animate.shift(UP * 2), run_time=1.0)
self.play(obj.animate.scale(1.5), run_time=0.8)
self.play(obj.animate.rotate(PI/2), run_time=1.0)
self.play(obj.animate.set_color(YELLOW), run_time=0.5)

# Removal
self.play(FadeOut(obj), run_time=0.5)
self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)  # Clear all

### CAMERA CONTROLS ###
# Initial setup
self.set_camera_orientation(phi=75*DEGREES, theta=-45*DEGREES)

# Animated transition
self.move_camera(phi=0*DEGREES, theta=-90*DEGREES, run_time=1.5)

# Ambient rotation
self.begin_ambient_camera_rotation(rate=0.1)
self.stop_ambient_camera_rotation()

### POSITIONING ###
# Absolute positioning
obj.move_to(RIGHT * 2 + UP * 1)
obj.move_to([2, 1, 0])  # [x, y, z]

# Relative positioning  
obj.shift(UP * 2)
obj.next_to(other_obj, RIGHT, buff=0.5)

# Edge positioning
obj.to_edge(UP)
obj.to_edge(LEFT, buff=0.5)
obj.to_corner(UL)

### COLOR SCHEME ###
YELLOW  # Highlight, emphasis
BLUE    # Primary elements
TEAL    # Secondary elements
WHITE   # Text, neutral
GREEN   # Positive, success
RED     # Attention, warning

### TIMING ###
self.wait(2.0)  # Pause for 2 seconds
self.play(Create(obj), run_time=1.5)  # Animation duration

=== END REFERENCE ===
"""


class RAGEngine:
    """
    Knowledge Bridge: Smart Code Retrieval Engine.
    
    Connects to ChromaDB (Bespoke Curator database) for topic-relevant
    Manim code examples. Ensures the LLM generates valid syntax by
    providing real, working code as context.
    
    Collection: prism_codebase (bespokelabs/bespoke-manim dataset)
    
    Attributes:
        db_path: Path to ChromaDB database
        collection_name: Name of the collection to query
        client: ChromaDB client
        collection: Active collection
    """
    
    def __init__(self, db_path: str = DB_PATH, collection_name: str = COLLECTION_NAME):
        """
        Initialize RAG Engine with ChromaDB connection.
        
        Args:
            db_path: Path to ChromaDB persistent storage
            collection_name: Name of collection (default: prism_codebase)
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._connected = self._connect()
        self._cache = {}  # Query cache
    
    def _connect(self) -> bool:
        """
        Connect to ChromaDB and get the prism_codebase collection.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            if not os.path.exists(self.db_path):
                print(f"   📚 RAG: Database not found at {self.db_path}")
                print("   📚 RAG: Using built-in reference (run rag_builder.py to populate)")
                return False
            
            # Connect to persistent ChromaDB
            self.client = chromadb.PersistentClient(path=self.db_path)
            
            # Get collection by name
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
            except Exception:
                # Try listing available collections
                collections = self.client.list_collections()
                print(f"   📚 RAG: Collection '{self.collection_name}' not found")
                if collections:
                    print(f"   📚 RAG: Available collections: {[c.name for c in collections]}")
                    # Use first available collection as fallback
                    self.collection = collections[0]
                    print(f"   📚 RAG: Using '{self.collection.name}' instead")
                else:
                    print("   📚 RAG: No collections available, using built-in reference")
                    return False
            
            count = self.collection.count()
            if count == 0:
                print("   📚 RAG: Collection empty, using built-in reference")
                return False
            
            print(f"   📚 RAG: Connected to '{self.collection.name}' ({count:,} examples)")
            return True
            
        except Exception as e:
            print(f"   📚 RAG: Connection failed ({e}), using built-in reference")
            return False
    
    def get_context(self, topic: str, n_results: int = DEFAULT_N_RESULTS) -> str:
        """
        Get relevant code context for a topic.
        
        This is the main method called by other engines. Returns:
        1. Bespoke Manim verified examples (HIGHEST PRIORITY - real working code)
        2. PRISM local knowledge base (3Blue1Brown style examples)
        3. Built-in Manim syntax reference (always)
        4. Top N relevant code examples from ChromaDB (if available)
        
        Args:
            topic: Educational topic (e.g., "Pythagorean Theorem", "3D vectors")
            n_results: Number of examples to retrieve (default: 3)
            
        Returns:
            String with syntax reference and code examples
        """
        # Check cache first
        cache_key = f"{topic}:{n_results}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        context = ""
        
        # === HIGHEST PRIORITY: Bespoke Manim verified examples ===
        if BESPOKE_AVAILABLE:
            try:
                bespoke_context = get_bespoke_rag_context(max_chars=10000)
                if bespoke_context:
                    context += "\n=== VERIFIED MANIM CODE FROM BESPOKE DATABASE ===\n"
                    context += "⚠️ USE THESE PATTERNS AS YOUR PRIMARY REFERENCE!\n"
                    context += "These are real, tested, working Manim CE examples.\n\n"
                    context += bespoke_context
                    context += "\n=== END BESPOKE EXAMPLES ===\n\n"
            except Exception as e:
                print(f"   ⚠️ Bespoke context failed: {e}")
        
        # Add LOCAL KNOWLEDGE BASE (PRISM style guide)
        context += get_local_knowledge_base()
        
        # Add built-in reference (guaranteed valid syntax)
        context += MANIM_REFERENCE
        
        # Add database examples if available
        if self._connected and self.collection:
            try:
                # Query ChromaDB for relevant examples
                results = self.collection.query(
                    query_texts=[topic],
                    n_results=n_results,
                    include=["metadatas", "documents"]
                )
                
                if results and results.get('ids') and results['ids'][0]:
                    context += "\n\n=== RELEVANT CODE EXAMPLES FROM KNOWLEDGE BASE ===\n"
                    context += f"Topic: {topic}\n"
                    context += f"Retrieved: {len(results['ids'][0])} examples\n"
                    
                    for i, metadata in enumerate(results.get('metadatas', [[]])[0]):
                        prompt = metadata.get('prompt', 'Unknown task')[:150]
                        code = metadata.get('code', '')
                        
                        if code:
                            context += f"\n{'─' * 50}\n"
                            context += f"Example {i+1}: {prompt}\n"
                            context += f"{'─' * 50}\n"
                            context += code[:4000] + "\n"  # Limit code length
                    
                    context += "\n=== END KNOWLEDGE BASE EXAMPLES ===\n"
                    
            except Exception as e:
                # Silently fall back to built-in reference
                pass
        
        # Limit total context size (prevent token overflow)
        context = context[:15000]
        
        # Cache result
        self._cache[cache_key] = context
        
        return context
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for specific code patterns in the knowledge base.
        
        More granular than get_context() - returns structured results.
        
        Args:
            query: Search query (e.g., "3D rotation animation", "graph plotting")
            n_results: Number of results to return
            
        Returns:
            List of dicts with: prompt, code, relevance score
        """
        if not self._connected or not self.collection:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["metadatas", "documents", "distances"]
            )
            
            snippets = []
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            
            for i, metadata in enumerate(metadatas):
                # Convert distance to relevance score (lower distance = higher relevance)
                distance = distances[i] if i < len(distances) else 1.0
                relevance = max(0, 1.0 - (distance / 2.0))  # Normalize to 0-1
                
                snippets.append({
                    'prompt': metadata.get('prompt', ''),
                    'code': metadata.get('code', ''),
                    'relevance': round(relevance, 3)
                })
            
            return snippets
            
        except Exception:
            return []
    
    def get_examples_for_mode(self, mode: str, n_results: int = 2) -> List[Dict]:
        """
        Get examples specific to 2D or 3D mode.
        
        Args:
            mode: "2D" or "3D"
            n_results: Number of examples
            
        Returns:
            List of relevant code examples
        """
        if mode.upper() == "3D":
            query = "3D scene ThreeDScene camera rotation sphere cube"
        else:
            query = "2D scene axes graph Circle Square formula"
        
        return self.search(query, n_results)
    
    def get_reference(self) -> str:
        """Get built-in Manim syntax reference."""
        return MANIM_REFERENCE
    
    def clear_cache(self):
        """Clear the query cache."""
        self._cache.clear()
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connected
    
    @property
    def document_count(self) -> int:
        """Get number of documents in collection."""
        if self._connected and self.collection:
            return self.collection.count()
        return 0


# ============== CONVENIENCE FUNCTIONS ==============
@lru_cache(maxsize=32)
def get_context(topic: str, n_results: int = DEFAULT_N_RESULTS) -> str:
    """
    Quick function to get RAG context (cached).
    
    Args:
        topic: Educational topic
        n_results: Number of examples to retrieve
        
    Returns:
        Code examples and reference material
    """
    return RAGEngine().get_context(topic, n_results)


def get_reference() -> str:
    """Get built-in Manim syntax reference."""
    return MANIM_REFERENCE


# ============== CLI TESTING ==============
if __name__ == "__main__":
    print("\n🔮 PRISM RAG Engine - Knowledge Bridge Test\n")
    print("=" * 60)
    
    engine = RAGEngine()
    
    print(f"\n📊 Status:")
    print(f"   Connected: {engine.is_connected}")
    print(f"   Database: {engine.db_path}")
    print(f"   Collection: {engine.collection_name}")
    
    if engine.is_connected:
        print(f"   Documents: {engine.document_count:,}")
    
    # Test queries
    test_topics = [
        "Pythagorean Theorem",
        "3D vectors and rotation",
        "sine wave graph plotting"
    ]
    
    for topic in test_topics:
        print(f"\n{'═' * 60}")
        print(f"🔍 Topic: {topic}")
        print("═" * 60)
        
        context = engine.get_context(topic, n_results=3)
        print(f"   Context length: {len(context):,} chars")
        
        # Show RAG examples if found
        if "RELEVANT CODE EXAMPLES" in context:
            start = context.find("=== RELEVANT")
            end = context.find("=== END KNOWLEDGE")
            if end > start:
                snippet = context[start:start+800]
                print(f"\n   Preview:\n{snippet}...")
        else:
            print("   (Using built-in reference only)")
        
        # Test search
        results = engine.search(topic, n_results=2)
        if results:
            print(f"\n   Search results: {len(results)} matches")
            for r in results:
                print(f"   - {r['prompt'][:60]}... (relevance: {r['relevance']})")
    
    print(f"\n{'═' * 60}")
    print("✅ RAG Engine test complete")
    print("═" * 60)
