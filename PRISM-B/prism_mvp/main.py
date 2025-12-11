"""
PRISM - Personalized AI Study Mentor
God Mode: Generic Video Generator for ANY Topic

Flow: Topic → Groq API → Fresh Manim Code → Render → Play
"""

import os
import subprocess
import sys
import re
import time

from langchain_groq import ChatGroq

# ============== CONFIGURATION ==============
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "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")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
GENERATED_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "generated_scene.py")
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "knowledge_base")


def load_knowledge_base() -> str:
    """Load knowledge base for RAG context."""
    knowledge = []
    
    for filename in ["manim_guide.txt", "prism_manual.txt"]:
        filepath = os.path.join(KNOWLEDGE_PATH, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()[:2000]
                knowledge.append(content)
    
    if knowledge:
        print(f"   📚 Loaded knowledge base")
        return "\n\n".join(knowledge)
    return ""


def generate_manim_code(topic: str) -> str:
    """Generate FRESH Manim code for ANY topic."""
    
    print(f"\n🧠 PRISM Processing: {topic}")
    
    rag_context = load_knowledge_base()
    
    models = ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"]
    
    # Master prompt - generates PURE Manim code (no prism_lib imports)
    system_prompt = """You are PRISM, an expert Manim CE developer.
Generate a COMPLETE educational animation for the given topic.

CRITICAL RULES:
1. Start with EXACTLY: from manim import *
2. Class name MUST be EXACTLY: GenScene(Scene)
3. DO NOT import anything else - only 'from manim import *'
4. DO NOT use prism_lib, prism_theme, or any custom imports

COLORS TO USE (define as strings):
- Background: "#1e1e1e"
- Titles: WHITE or "#ffffff"  
- Accents: "#2496ED" or BLUE
- Body text: "#ece6e2"

VIDEO STRUCTURE:
1. PRISM Branding (2 sec):
   - Show "PRISM" text, then "AI Generated", FadeOut

2. Title (2 sec):
   - Show topic title at center/top

3. Content (15-20 sec):
   - VISUAL explanations with shapes/diagrams
   - Not just text - use Circle, Square, Arrow, Line
   - Animate step by step

4. Summary (2 sec):
   - Key takeaway, FadeOut all

TOPIC-SPECIFIC VISUALS:
- NETWORKS: nodes (Dot/Circle) + connections (Line/Arrow)
- PHYSICS: forces (Arrow), motion (shift animations)
- MATH: MathTex equations, geometric shapes
- BIOLOGY: labeled diagrams with circles/rectangles
- CS/PROGRAMMING: flowcharts with boxes and arrows
- GENERAL: bullet points, simple icons

MANIM PATTERNS:
- Text("text", font_size=48) - for titles
- Text("text", font_size=28) - for body
- MathTex(r"x^2") - for equations
- Circle(radius=1, color=BLUE)
- Square(side_length=2)
- Arrow(start=LEFT, end=RIGHT)
- Line(start, end)
- self.play(Create(shape)) - for shapes
- self.play(Write(text)) - for text
- self.play(FadeIn(obj)), FadeOut(obj)
- self.wait(1) - pause between animations
- obj.next_to(other, DOWN)
- obj.to_edge(UP)
- obj.shift(LEFT * 2)

Keep code under 60 lines. Make it VISUAL and EDUCATIONAL.

OUTPUT: ONLY Python code. No markdown. No explanations. No ```python blocks."""

    user_prompt = f"""Generate Manim animation for: {topic}

The video MUST be specifically about "{topic}".
Include relevant diagrams and visuals.
Start with 'from manim import *' and use class GenScene(Scene).

RAG Context:
{rag_context[:1500]}

Write the code:"""

    for model in models:
        try:
            print(f"   🚀 Model: {model}")
            llm = ChatGroq(model=model, temperature=0.5, max_tokens=2500)
            
            response = llm.invoke([
                ("system", system_prompt),
                ("human", user_prompt)
            ])
            
            code = response.content.strip()
            
            # Clean markdown
            code = re.sub(r"```python\s*", "", code)
            code = re.sub(r"```\s*", "", code)
            code = re.sub(r"^```\s*", "", code)
            code = code.strip()
            
            # Remove any prism_lib imports (bug fix!)
            code = re.sub(r"from prism_lib.*\n", "", code)
            code = re.sub(r"import prism_lib.*\n", "", code)
            
            # Ensure proper import
            if not code.startswith("from manim import"):
                code = "from manim import *\n\n" + code
            
            # Verify GenScene exists
            if "class GenScene" not in code:
                print(f"   ⚠️ Invalid code structure, retrying...")
                continue
            
            print(f"   ✅ Code generated for: {topic}")
            return code
            
        except Exception as e:
            print(f"   ⚠️ {model} error: {str(e)[:100]}")
            continue
    
    return ""


def validate_code(code: str) -> str:
    """Fix common Manim issues."""
    fixes = [
        (r"ShowCreation\(", "Create("),
        (r"TextMobject\(", "Text("),
        (r"TexMobject\(", "Tex("),
    ]
    for pattern, replacement in fixes:
        code = re.sub(pattern, replacement, code)
    return code


def render_video(topic: str) -> bool:
    """Render and play the video."""
    
    print("🎬 Rendering...")
    
    # Clean filename
    safe_name = re.sub(r"[^\w\s-]", "", topic).replace(" ", "_")[:25]
    timestamp = int(time.time())  # Unique timestamp to avoid cache
    output_name = f"PRISM_{safe_name}_{timestamp}"
    
    env = os.environ.copy()
    env["PYTHONPATH"] = SCRIPT_DIR  # Point to prism_mvp so imports work if needed
    
    cmd = [
        sys.executable, "-m", "manim",
        "-ql",
        "--disable_caching",  # Completely disable caching
        GENERATED_SCRIPT_PATH,
        "GenScene",
        "-o", output_name
    ]
    
    try:
        result = subprocess.run(
            cmd, 
            check=True, 
            env=env, 
            capture_output=True, 
            text=True,
            cwd=SCRIPT_DIR  # Run from prism_mvp directory
        )
        print("   ✅ Render complete!")
        
        # Find the exact video we just created
        video_dir = os.path.join(SCRIPT_DIR, "media", "videos", "generated_scene", "480p15")
        
        # Also check base dir
        if not os.path.exists(video_dir):
            video_dir = os.path.join(BASE_DIR, "media", "videos", "generated_scene", "480p15")
        
        video_path = os.path.join(video_dir, f"{output_name}.mp4")
        
        if os.path.exists(video_path):
            print(f"   🎥 Playing: {output_name}.mp4")
            if sys.platform == "win32":
                os.startfile(video_path)
            return True
        else:
            # List what's there for debugging
            if os.path.exists(video_dir):
                files = [f for f in os.listdir(video_dir) if f.endswith('.mp4') and safe_name in f]
                if files:
                    # Get the newest one with our topic name
                    newest = max(files, key=lambda x: os.path.getmtime(os.path.join(video_dir, x)))
                    video_path = os.path.join(video_dir, newest)
                    print(f"   🎥 Playing: {newest}")
                    if sys.platform == "win32":
                        os.startfile(video_path)
                    return True
            
            print(f"   ⚠️ Video not found. Check: {video_dir}")
            return False
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Manim Error!")
        if e.stderr:
            # Show actual error
            print(f"   {e.stderr[-800:]}")
        return False


def main():
    print("\n" + "="*50)
    print("   🔮 PRISM - AI Video Generator")
    print("="*50)
    
    topic = input("\n📝 Enter ANY topic: ").strip()
    if not topic:
        print("   No topic entered. Exiting.")
        return
    
    # Step 1: Generate fresh code
    code = generate_manim_code(topic)
    if not code:
        print("❌ Code generation failed.")
        return
    
    # Step 2: Validate and save
    code = validate_code(code)
    with open(GENERATED_SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"   💾 Saved: generated_scene.py")
    
    # Step 3: Show preview
    print("\n--- Generated Code ---")
    lines = code.split("\n")
    for line in lines[:15]:
        print(f"   {line}")
    if len(lines) > 15:
        print(f"   ... ({len(lines)} total lines)")
    print("---\n")
    
    # Step 4: Render and play
    if render_video(topic):
        print("\n🎉 SUCCESS!")
    else:
        print("\n💡 Check generated_scene.py for errors.")


if __name__ == "__main__":
    main()