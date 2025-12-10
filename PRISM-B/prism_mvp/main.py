"""
PRISM - Personalized AI Study Mentor
God Mode: Generalist Code Generation Pipeline

Flow: Topic → Groq (LLaMA) → Fresh Manim Code → Video
"""

import os
import subprocess
import sys
import re

from langchain_groq import ChatGroq

# ============== CONFIGURATION ==============
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "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")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
GENERATED_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "generated_scene.py")
KNOWLEDGE_PATH = os.path.join(BASE_DIR, "knowledge_base")


def load_manim_knowledge() -> str:
    """Load Manim syntax guide from file (simple & reliable)."""
    
    guide_path = os.path.join(KNOWLEDGE_PATH, "manim_guide.txt")
    if os.path.exists(guide_path):
        try:
            with open(guide_path, "r", encoding="utf-8") as f:
                print("   📖 Loaded Manim guide")
                return f.read()
        except Exception as e:
            print(f"   ⚠️ Could not load guide: {e}")
    
    return ""


def generate_manim_code(topic: str) -> str:
    """Generate complete Manim code using Groq's fast LLaMA models."""
    
    print(f"\n🧠 Generating visualization for: {topic}")
    
    manim_reference = load_manim_knowledge()
    
    # Groq models - fast and free
    models = ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"]
    
    system_prompt = """You are an expert Manim Community Edition developer.
Write a COMPLETE, RUNNABLE Python script to visualize the given topic.

STRICT REQUIREMENTS:
1. Start with: from manim import *
2. Class name MUST be: GenScene(Scene)
3. Use ONLY these proven patterns:
   - Text("string") for labels (NOT TextMobject)
   - MathTex(r"\\frac{a}{b}") for math
   - Axes() for graphs
   - Create() for shapes (NOT ShowCreation)
   - FadeIn(), FadeOut(), Write() for text
   - self.play(...) for animations
   - self.wait(1) between steps

4. Keep it SIMPLE - max 25 lines in construct()
5. Use basic shapes: Circle, Square, Line, Arrow, Dot, Rectangle
6. Always center important objects with .move_to(ORIGIN)

COMMON MISTAKES TO AVOID:
- ShowCreation → Use Create instead
- TextMobject → Use Text instead  
- TexMobject → Use Tex or MathTex instead
- Don't use external imports besides manim
- Don't forget self.wait() between animations

OUTPUT: Return ONLY valid Python code. No markdown code blocks, no explanations, no comments about the code."""

    user_prompt = f"""MANIM REFERENCE:
{manim_reference[:2000] if manim_reference else "Use standard Manim CE syntax."}

TOPIC TO VISUALIZE: {topic}

Write the complete Python code now:"""

    for model in models:
        try:
            print(f"   🚀 Using: {model}")
            llm = ChatGroq(model=model, temperature=0.2, max_tokens=2000)
            
            response = llm.invoke([
                ("system", system_prompt),
                ("human", user_prompt)
            ])
            code = response.content
            
            # Clean markdown artifacts
            code = re.sub(r"```python\s*", "", code)
            code = re.sub(r"```\s*", "", code)
            code = code.strip()
            
            # Ensure import exists
            if "from manim import" not in code:
                code = "from manim import *\n\n" + code
            
            print(f"   ✅ Code generated successfully!")
            return code
            
        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                print(f"   ⚠️ {model}: Rate limited, trying next...")
                continue
            else:
                print(f"   ⚠️ {model}: {e}")
                continue
    
    print("   ❌ All models failed.")
    return ""


def validate_and_fix_code(code: str) -> str:
    """Apply common fixes to generated code."""
    fixes = [
        (r"ShowCreation\(", "Create("),
        (r"TextMobject\(", "Text("),
        (r"TexMobject\(", "Tex("),
    ]
    for pattern, replacement in fixes:
        code = re.sub(pattern, replacement, code)
    return code


def render_video(topic: str) -> bool:
    """Render the generated scene with Manim."""
    
    print("🎬 Rendering with Manim...")
    
    safe_name = re.sub(r"[^\w\s-]", "", topic).replace(" ", "_")[:30]
    output_name = f"PRISM_{safe_name}"
    
    env = os.environ.copy()
    env["PYTHONPATH"] = BASE_DIR
    
    cmd = [
        sys.executable, "-m", "manim",
        "-pql",
        GENERATED_SCRIPT_PATH,
        "GenScene",
        "-o", output_name
    ]
    
    try:
        result = subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)
        print("   ✅ Render complete!")
        
        video_dir = os.path.join(SCRIPT_DIR, "media", "videos", "generated_scene", "480p15")
        video_path = os.path.join(video_dir, f"{output_name}.mp4")
        
        if os.path.exists(video_path):
            print(f"   🎥 Video: {video_path}")
            if sys.platform == "win32":
                os.startfile(video_path)
            return True
        elif os.path.exists(video_dir):
            videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
            if videos:
                latest = max(videos, key=lambda x: os.path.getmtime(os.path.join(video_dir, x)))
                print(f"   🎥 Found: {latest}")
                if sys.platform == "win32":
                    os.startfile(os.path.join(video_dir, latest))
                return True
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Manim Error!")
        if e.stderr:
            print(f"   {e.stderr[:500]}")
        return False


def main():
    print("\n" + "="*50)
    print("   🔮 PRISM - AI Video Generator (God Mode)")
    print("="*50)
    
    topic = input("\n📝 Enter topic (e.g., 'Pythagorean Theorem'): ").strip()
    if not topic:
        topic = "Introduction to Circles"
        print(f"   Using default: {topic}")
    
    # Generate
    code = generate_manim_code(topic)
    if not code:
        print("❌ Failed to generate code. Check API key.")
        return
    
    # Fix & Save
    code = validate_and_fix_code(code)
    with open(GENERATED_SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"   💾 Saved to: generated_scene.py")
    
    # Preview
    print("\n--- Code Preview ---")
    for line in code.split("\n")[:12]:
        print(f"   {line}")
    print("   ..." if len(code.split("\n")) > 12 else "")
    print("---\n")
    
    # Render
    if render_video(topic):
        print("\n🎉 SUCCESS!")
    else:
        print("\n💡 Check generated_scene.py for errors.")


if __name__ == "__main__":
    main()