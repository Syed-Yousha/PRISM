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
    
    # Master prompt - generates clean, non-overlapping animations
    system_prompt = """You are PRISM, an expert Manim CE developer.
Generate a CLEAN, WELL-FORMATTED educational animation (1+ MINUTE).

CRITICAL RULES:
1. Start with EXACTLY: from manim import *
2. Class name MUST be EXACTLY: GenScene(Scene)
3. DO NOT import anything else - only 'from manim import *'

=== MOST IMPORTANT: CLEAN ANIMATIONS ===
EVERY SECTION MUST:
1. CLEAR the screen before showing new content (FadeOut previous objects)
2. Position elements with proper spacing (buff=0.5 minimum)
3. Never overlap text or shapes
4. Use VGroup to manage related objects together

PATTERN FOR EACH SECTION:
```
# Clear previous content
self.play(*[FadeOut(mob) for mob in self.mobjects])

# Create new content for this section
title = Text("Section Title", font_size=40).to_edge(UP)
content = Text("Content here", font_size=28).next_to(title, DOWN, buff=0.8)
visual = Circle().next_to(content, DOWN, buff=0.5)

# Animate
self.play(Write(title))
self.play(FadeIn(content))
self.play(Create(visual))
self.wait(2)
```

COLORS:
- Background: "#1e1e1e" (set with self.camera.background_color)
- Titles: WHITE
- Accents: BLUE, YELLOW
- Body: "#ece6e2"

=== VIDEO STRUCTURE (60+ seconds) ===

1. PRISM INTRO (5 sec):
   title = Text("PRISM", font_size=60, color=WHITE)
   subtitle = Text("AI Generated Education", font_size=30).next_to(title, DOWN, buff=0.5)
   - Write title, FadeIn subtitle
   - self.wait(2)
   - FadeOut ALL

2. TOPIC SLIDE (5 sec):
   - CLEAR screen first
   - Title at UP edge
   - Subtitle below with buff=0.5
   - self.wait(2)
   - FadeOut ALL

3. SECTION 1 (12 sec):
   - CLEAR screen
   - Section title at TOP
   - Explanation text CENTERED, max width 10 units
   - Simple visual BELOW text with buff=0.5
   - self.wait(3)
   - FadeOut ALL

4. SECTION 2 (12 sec):
   - CLEAR screen  
   - New section title
   - Different visual (diagram/shapes)
   - Proper spacing between elements
   - self.wait(3)
   - FadeOut ALL

5. SECTION 3 (12 sec):
   - CLEAR screen
   - Another concept
   - Visual demonstration
   - self.wait(3)
   - FadeOut ALL

6. SECTION 4 (10 sec):
   - CLEAR screen
   - Example or formula
   - MathTex if applicable
   - self.wait(2)
   - FadeOut ALL

7. SUMMARY (8 sec):
   - CLEAR screen
   - "Key Takeaways" title
   - 3 bullet points using VGroup().arrange(DOWN, buff=0.4)
   - "Thanks for watching!"
   - self.wait(3)
   - FadeOut ALL

=== FORMATTING RULES ===
- Text width: Use .scale_to_fit_width(10) for long text
- Spacing: Always use buff=0.5 or more between elements
- Positioning: Use .to_edge(UP), .to_edge(DOWN), ORIGIN
- Groups: Use VGroup() to keep related items together
- Clear screen: self.play(*[FadeOut(mob) for mob in self.mobjects])

=== MANIM PATTERNS ===
# Title at top
title = Text("Title", font_size=44, color=WHITE).to_edge(UP)

# Centered content with max width
content = Text("Long text here", font_size=26)
content.scale_to_fit_width(10)
content.next_to(title, DOWN, buff=0.8)

# Visual below content
diagram = Circle(radius=1, color=BLUE).next_to(content, DOWN, buff=0.5)

# Bullet points
bullets = VGroup(
    Text("• Point 1", font_size=24),
    Text("• Point 2", font_size=24),
    Text("• Point 3", font_size=24)
).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
bullets.next_to(title, DOWN, buff=0.8)

# Clear everything
self.play(*[FadeOut(mob) for mob in self.mobjects])

OUTPUT: ONLY Python code. No markdown. No explanations."""

    user_prompt = f"""Generate a CLEAN, 1-MINUTE Manim animation for: {topic}

REQUIREMENTS:
1. CLEAR screen between each section (FadeOut all mobjects)
2. Never overlap text or shapes
3. Use proper spacing (buff=0.5+)
4. 7 distinct sections as specified
5. Total duration: 60+ seconds

Topic: "{topic}"

RAG Context:
{rag_context[:1000]}

Write clean, non-overlapping code:"""

    for model in models:
        try:
            print(f"   🚀 Model: {model}")
            llm = ChatGroq(model=model, temperature=0.5, max_tokens=4000)
            
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