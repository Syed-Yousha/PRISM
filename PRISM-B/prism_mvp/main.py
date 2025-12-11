"""
PRISM - Personalized AI Study Mentor
God Mode: Generic Video Generator for ANY Topic + Voice

Flow: Topic → Groq API → Fresh Manim Code → Render → Voice → Merge → Play
"""

import os
import subprocess
import sys
import re
import time

from langchain_groq import ChatGroq
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

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


def generate_narration(topic: str) -> str:
    """Generate a narration script synced to the video structure."""
    
    print("🎙️ Generating narration script...")
    
    system_prompt = """You are PRISM's voice narrator. Generate a SPOKEN NARRATION script for an educational video.

RULES:
1. Write EXACTLY what should be spoken - no stage directions
2. Match the 7-section video structure
3. Use natural, conversational language
4. Pace: About 120-150 words per minute
5. Total narration: ~700-900 words for 60-second video

STRUCTURE TO FOLLOW:
[Section 1: Intro - 5 seconds, ~10 words]
Welcome to PRISM. Let's explore [topic] together.

[Section 2: Topic Introduction - 5 seconds, ~15 words]
Today we'll learn about [topic]. This is a fascinating subject that...

[Section 3: First Concept - 12 seconds, ~30 words]
Let's start with the basics. [Explain first key concept clearly]...

[Section 4: Second Concept - 12 seconds, ~30 words]  
Now let's look at [next concept]. [Explain with simple examples]...

[Section 5: Third Concept - 12 seconds, ~30 words]
Another important aspect is [concept]. [Explain clearly]...

[Section 6: Example/Formula - 10 seconds, ~25 words]
Here's a practical example. [Walk through the example]...

[Section 7: Summary - 8 seconds, ~20 words]
To summarize: [key points]. Thanks for learning with PRISM!

OUTPUT: Only the narration text. No section labels or timing notes. Just flowing spoken words with natural pauses (use ... for slight pauses)."""

    user_prompt = f"""Generate a spoken narration for a 60-second educational video about: {topic}

Write natural, engaging narration that explains {topic} clearly. The narration should flow smoothly from introduction to conclusion.

Topic: "{topic}"

Write the complete narration script:"""

    try:
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, max_tokens=1500)
        
        response = llm.invoke([
            ("system", system_prompt),
            ("human", user_prompt)
        ])
        
        narration = response.content.strip()
        
        # Clean any markdown or labels
        narration = re.sub(r"\[.*?\]", "", narration)
        narration = re.sub(r"\*\*.*?\*\*", "", narration)
        narration = re.sub(r"Section \d+:?", "", narration)
        narration = narration.strip()
        
        print(f"   ✅ Narration generated ({len(narration.split())} words)")
        return narration
        
    except Exception as e:
        print(f"   ⚠️ Narration error: {str(e)[:100]}")
        # Fallback narration
        return f"Welcome to PRISM. Today we're learning about {topic}. This is an important concept that has many applications. Let's explore the key ideas together. Thank you for watching."


def generate_voice(narration: str, output_path: str) -> bool:
    """Convert narration text to speech using gTTS."""
    
    print("🔊 Generating voice...")
    
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate speech with gTTS
        tts = gTTS(text=narration, lang='en', slow=False)
        tts.save(output_path)
        
        print(f"   ✅ Voice saved: {os.path.basename(output_path)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Voice generation error: {str(e)}")
        return False


def attach_voice_to_video(video_path: str, audio_path: str, output_path: str) -> str:
    """Merge audio narration with video using MoviePy."""
    
    print("🎬 Merging voice with video...")
    
    try:
        # Load video and audio
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        # Get durations
        video_duration = video.duration
        audio_duration = audio.duration
        
        print(f"   📹 Video: {video_duration:.1f}s | 🔊 Audio: {audio_duration:.1f}s")
        
        # If audio is longer than video, trim it
        if audio_duration > video_duration:
            audio = audio.with_duration(video_duration)
            print(f"   ✂️ Audio trimmed to match video")
        
        # If audio is shorter, it will just end early (that's fine)
        
        # Set the audio to the video
        final_video = video.with_audio(audio)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the final video
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            logger=None  # Suppress verbose output
        )
        
        # Clean up
        video.close()
        audio.close()
        final_video.close()
        
        print(f"   ✅ Final video: {os.path.basename(output_path)}")
        return output_path
        
    except Exception as e:
        print(f"   ❌ Merge error: {str(e)}")
        return video_path  # Return original video if merge fails


def render_video(topic: str) -> str:
    """Render the video and return its path."""
    
    print("🎬 Rendering video...")
    
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
            return video_path
        else:
            # List what's there for debugging
            if os.path.exists(video_dir):
                files = [f for f in os.listdir(video_dir) if f.endswith('.mp4') and safe_name in f]
                if files:
                    # Get the newest one with our topic name
                    newest = max(files, key=lambda x: os.path.getmtime(os.path.join(video_dir, x)))
                    video_path = os.path.join(video_dir, newest)
                    return video_path
            
            print(f"   ⚠️ Video not found. Check: {video_dir}")
            return ""
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Manim Error!")
        if e.stderr:
            # Show actual error
            print(f"   {e.stderr[-800:]}")
        return ""


def main():
    print("\n" + "="*50)
    print("   🔮 PRISM - AI Video Generator + Voice")
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
    
    # Step 4: Render video (silent)
    video_path = render_video(topic)
    if not video_path:
        print("\n💡 Check generated_scene.py for errors.")
        return
    
    # Step 5: Generate narration script
    narration = generate_narration(topic)
    
    # Step 6: Convert narration to speech
    audio_dir = os.path.join(SCRIPT_DIR, "media", "audio")
    safe_name = re.sub(r"[^\w\s-]", "", topic).replace(" ", "_")[:25]
    timestamp = int(time.time())
    audio_path = os.path.join(audio_dir, f"voice_{safe_name}_{timestamp}.mp3")
    
    if not generate_voice(narration, audio_path):
        print("   ⚠️ Voice generation failed, playing silent video...")
        if sys.platform == "win32":
            os.startfile(video_path)
        return
    
    # Step 7: Merge voice with video
    output_dir = os.path.dirname(video_path)
    final_path = os.path.join(output_dir, f"PRISM_{safe_name}_voiced_{timestamp}.mp4")
    
    final_video = attach_voice_to_video(video_path, audio_path, final_path)
    
    # Step 8: Play the final video
    print(f"\n🎥 Playing: {os.path.basename(final_video)}")
    if sys.platform == "win32":
        os.startfile(final_video)
    
    print("\n🎉 SUCCESS! Video with voice narration complete!")
    print(f"   📁 Video: {final_video}")
    print(f"   🔊 Audio: {audio_path}")


if __name__ == "__main__":
    main()