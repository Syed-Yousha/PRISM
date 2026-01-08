"""
PRISM Manim Engine - Visual Core
================================
Production-ready rendering with RAG harmony and smart caching.

ARCHITECTURE:
1. RAG Integration: Injects knowledge base context into every LLM call
2. Audio-First: Animation timing driven by audio durations
3. 2D/3D Hybrid: Seamless switching between Scene types
4. Smart Caching: Re-uses unchanged scenes (huge speedup on re-renders)

PERFORMANCE:
- Default Quality: -qm (720p @ 30fps) for 3x faster rendering
- Caching: Enabled by default
- Single attempt + robust fallback (no retry spam)
"""

import os
import sys
import re
import time
import subprocess
from typing import Dict, Optional, List

from langchain_groq import ChatGroq
from data_models import Segment, VideoScript

# ============== CONFIGURATION ==============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "generated_scene.py")
BACKGROUND_COLOR = "#0a0a0a"  # Near-black for contrast

# Quality presets (flag, resolution, fps)
QUALITY_PRESETS = {
    "l": ("480p15", 15),    # Low - fastest, preview
    "m": ("720p30", 30),    # Medium - recommended default
    "h": ("1080p60", 60),   # High - final output
}
DEFAULT_QUALITY = "m"  # 720p @ 30fps - 3x faster than 1080p60

# Camera presets for 2D/3D modes
CAMERA_2D = {"phi": 0, "theta": -90}     # Flat, top-down view
CAMERA_3D = {"phi": 75, "theta": -45}    # Isometric 3D view

os.environ.setdefault(
    "GROQ_API_KEY",
    os.getenv("GROQ_API_KEY", "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")
)


# ============== RAG-ENHANCED SYSTEM PROMPT ==============
SYSTEM_PROMPT = """You are an expert Manim Community Edition animator. Generate ONLY Python code.

=== RAG CONTEXT (USE THESE EXAMPLES FOR CORRECT SYNTAX) ===
{rag_context}

=== LAYOUT RULES (MANDATORY) ===
- LEFT ZONE (x=-7 to -1.5): Text, formulas, notes - use add_fixed_in_frame_mobjects()
- RIGHT ZONE (x=-1.5 to +7): Visuals, shapes, animations

=== TEXT HANDLING (CRITICAL FOR 3D SCENES) ===
```python
# ALWAYS call add_fixed_in_frame_mobjects BEFORE positioning!
title = MathTex(r"Title", font_size=44, color=YELLOW)
self.add_fixed_in_frame_mobjects(title)  # MUST BE FIRST!
title.to_edge(UP)
self.play(Write(title), run_time=1.0)

# For formulas
formula = MathTex(r"E = mc^2", font_size=40, color=WHITE)
self.add_fixed_in_frame_mobjects(formula)
formula.move_to(LEFT * 4 + UP * 2)
self.play(Write(formula), run_time=1.5)
```

=== 2D SHAPES ===
Circle, Square, Rectangle, Polygon, Arrow, Line, Dot, Axes, NumberPlane

=== 3D SHAPES ===
Sphere, Cube, Cone, Cylinder, Arrow3D, ThreeDAxes, Surface

=== ANIMATIONS ===
Create(shape), Write(text), FadeIn(obj), FadeOut(obj), Transform(a, b)
obj.animate.shift(UP*2), obj.animate.scale(1.5), obj.animate.rotate(PI/2)

=== COLOR SCHEME ===
YELLOW = highlight/emphasis
BLUE = primary elements
TEAL = secondary elements
WHITE = text/neutral
GREEN = positive
RED = attention

=== OUTPUT FORMAT ===
Return ONLY executable Python code. 
NO imports (already handled).
NO class definition (already handled).
NO markdown code blocks.
NO explanations."""


class ManimEngine:
    """
    Visual Core: Manim Scene Generator and Renderer.
    
    Features:
    - RAG Harmony: Injects knowledge base context into prompts
    - Audio-First: Timing driven by audio durations
    - 2D/3D Hybrid: Handles ThreeDScene with camera switching
    - Smart Caching: Enabled by default for fast re-renders
    
    Attributes:
        quality: Render quality ('l', 'm', 'h')
        llm: LangChain ChatGroq instance
    """
    
    def __init__(self, quality: str = DEFAULT_QUALITY):
        """
        Initialize Manim Engine.
        
        Args:
            quality: 'l'=480p15, 'm'=720p30 (recommended), 'h'=1080p60
        """
        self.quality = quality
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.2,  # Lower for more consistent code
            max_tokens=4500
        )
    
    def _build_segment_prompt(self, segment: Dict, is_first: bool, total_segments: int) -> str:
        """
        Build detailed prompt for a single segment.
        
        The prompt includes:
        - Segment metadata (duration, mode, position)
        - Narration and visual instructions
        - Clear/camera instructions based on mode
        
        Args:
            segment: Segment dictionary with all metadata
            is_first: Whether this is the first segment
            total_segments: Total number of segments for context
            
        Returns:
            Formatted prompt string
        """
        duration = segment.get('duration', 5.0)
        mode = segment.get('visual_mode', '2D').upper()
        seg_id = segment.get('id', 1)
        
        # Calculate wait time (total duration - animation time)
        # Leave ~3-4 seconds for animations, rest is wait
        animation_time = min(duration * 0.6, 4.0)
        wait_time = max(duration - animation_time, 0.5)
        
        narration = segment.get('narration', segment.get('text', ''))[:300]
        notes = segment.get('blackboard_notes', '')[:200]
        visual = segment.get('visual_instruction', segment.get('visual_plan', ''))[:250]
        title = segment.get('title', f'Section {seg_id}')
        section_type = segment.get('section_type', 'concept')
        
        # Build clear instruction
        clear_code = "" if is_first else """
# Clear previous content
self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.3)"""
        
        # Camera mode description
        if mode == "3D":
            camera_desc = "3D perspective (phi=75°, theta=-45°)"
        else:
            camera_desc = "2D flat view (phi=0°)"
        
        return f"""
=== SEGMENT {seg_id}/{total_segments}: {title} ({section_type}) ===
Duration: {duration:.1f}s | Mode: {mode} | Camera: {camera_desc}

{clear_code}

NARRATION (what viewer hears):
"{narration}"

LEFT SIDE (blackboard notes, use add_fixed_in_frame_mobjects):
{notes if notes else 'Display title and key formula'}

RIGHT SIDE (visual animation):
{visual if visual else 'Animate relevant shape or diagram'}

TIMING:
- Animations: ~{animation_time:.1f}s
- Final wait: self.wait({wait_time:.1f})

Generate the code:"""
    
    def generate_segment_code(self, segment: Dict, is_first: bool, rag_context: str, total_segments: int) -> str:
        """
        Generate Manim code for ONE segment using RAG-enhanced LLM.
        
        Args:
            segment: Segment dictionary
            is_first: Whether this is the first segment
            rag_context: RAG context with code examples
            total_segments: Total segments for context
            
        Returns:
            Generated Python code string
        """
        prompt = self._build_segment_prompt(segment, is_first, total_segments)
        
        # Format system prompt with RAG context
        system = SYSTEM_PROMPT.format(rag_context=rag_context[:6000])
        
        try:
            response = self.llm.invoke([
                ("system", system),
                ("human", prompt)
            ])
            
            code = response.content.strip()
            
            # Clean up code
            code = re.sub(r"```python\s*|```\s*", "", code)
            code = re.sub(r"^from manim.*?\n|^import.*?\n", "", code, flags=re.MULTILINE)
            code = re.sub(r"^class\s+\w+.*?:\s*\n\s*def construct.*?:\s*\n", "", code, flags=re.MULTILINE)
            code = self._post_process(code)
            
            return code
            
        except Exception as e:
            print(f"   ⚠️ Code generation failed for segment {segment.get('id', '?')}: {e}")
            return self._fallback_code(segment, is_first)
    
    def _post_process(self, code: str) -> str:
        """
        Fix common Manim syntax issues.
        
        Handles deprecated methods, incorrect class names, LaTeX issues, etc.
        """
        # Fix deprecated/renamed methods
        replacements = [
            (r"ShowCreation\(", "Create("),
            (r"TextMobject\(", "Tex("),
            (r"TexMobject\(", "MathTex("),
            (r'Text\("([^"]+)"', r'Tex(r"\1"'),
            (r"\.rotate\(degrees=", ".rotate(angle="),
            (r"self\.camera\.frame\.move_to", "# self.camera.frame.move_to"),
        ]
        
        for pattern, replacement in replacements:
            code = re.sub(pattern, replacement, code)
        
        # Fix LaTeX bullet points - use proper escaping or replace with dash
        # \bullet needs double backslash in raw strings, or use $\bullet$
        code = re.sub(r'Tex\(r?"\\\\bullet', r'Tex(r"$\\bullet$', code)
        code = re.sub(r'Tex\(r?"\\bullet', r'Tex(r"$\\bullet$', code)
        
        # Fix unescaped backslashes in Tex (common issue)
        # Replace single backslash commands that should be in math mode
        code = re.sub(r'Tex\(r?"([^"]*?)\\sqrt', r'Tex(r"\1$\\sqrt', code)
        
        return code
    
    def _fallback_code(self, segment: Dict, is_first: bool) -> str:
        """
        Generate reliable fallback code when LLM fails.
        
        Produces valid, working Manim code that displays:
        - Title text
        - A simple shape
        - Proper timing
        """
        title = segment.get('title', f"Section {segment.get('id', 1)}")[:30]
        duration = segment.get('duration', 5.0)
        wait_time = max(duration - 3.5, 1.0)
        mode = segment.get('visual_mode', '2D').upper()
        
        clear = "" if is_first else """
# Clear previous
self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.3)
"""
        
        # Different shapes based on mode
        if mode == "3D":
            shape_code = """
shape = Sphere(radius=1.2, color=BLUE, fill_opacity=0.7)
shape.move_to(RIGHT * 2.5)
self.play(Create(shape), run_time=1.5)"""
        else:
            shape_code = """
shape = Circle(radius=1.5, color=BLUE, fill_opacity=0.3)
shape.move_to(RIGHT * 2.5)
self.play(Create(shape), run_time=1.5)"""
        
        return f"""{clear}
# Title
title = Tex(r"\\textbf{{{title}}}", font_size=44, color=YELLOW)
self.add_fixed_in_frame_mobjects(title)
title.to_edge(UP)
self.play(Write(title), run_time=1.0)
{shape_code}

self.wait({wait_time:.1f})
"""
    
    def _get_camera_code(self, mode: str, is_first: bool, changed: bool) -> str:
        """
        Generate camera setup code for 2D/3D modes.
        
        Args:
            mode: "2D" or "3D"
            is_first: Whether this is the first segment
            changed: Whether mode changed from previous segment
            
        Returns:
            Camera setup Python code
        """
        if mode == "3D":
            phi, theta = CAMERA_3D["phi"], CAMERA_3D["theta"]
            if is_first:
                return f"        self.set_camera_orientation(phi={phi}*DEGREES, theta={theta}*DEGREES)\n"
            elif changed:
                return f"        self.move_camera(phi={phi}*DEGREES, theta={theta}*DEGREES, run_time=1.0)\n"
        else:  # 2D
            phi, theta = CAMERA_2D["phi"], CAMERA_2D["theta"]
            if is_first:
                return f"        self.set_camera_orientation(phi={phi}*DEGREES, theta={theta}*DEGREES)\n"
            elif changed:
                return f"        self.move_camera(phi={phi}*DEGREES, theta={theta}*DEGREES, run_time=0.8)\n"
        return ""
    
    def generate_full_code(self, video_script: VideoScript, rag_context: str = "") -> str:
        """
        Generate complete Manim scene from VideoScript.
        
        This is the main code generation method. Creates a full
        ThreeDScene class with all segments, proper camera handling,
        and correct timing based on audio durations.
        
        Args:
            video_script: VideoScript with all segments
            rag_context: RAG context with code examples
            
        Returns:
            Complete, executable Python code
        """
        print(f"   💻 Generating Manim code ({len(video_script.segments)} segments)...")
        
        # File header with imports and config
        header = f'''"""
PRISM Generated Scene
Topic: {video_script.topic}
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
Segments: {len(video_script.segments)}
Total Duration: {video_script.total_duration:.1f}s
"""

from manim import *
import numpy as np

# Scene configuration
config.background_color = "{BACKGROUND_COLOR}"


class GenScene(ThreeDScene):
    """Auto-generated educational animation."""
    
    def construct(self):
'''
        
        segments_code = []
        prev_mode = None
        total_segments = len(video_script.segments)
        
        for i, seg in enumerate(video_script.segments):
            is_first = (i == 0)
            mode = (seg.visual_mode or "2D").upper()
            changed = prev_mode is not None and prev_mode != mode
            
            # Camera setup
            camera_code = self._get_camera_code(mode, is_first, changed)
            
            # Generate segment code via LLM with RAG context
            seg_code = self.generate_segment_code(
                seg.to_dict(), 
                is_first, 
                rag_context,
                total_segments
            )
            
            # Indent code properly
            indented = "\n".join(
                "        " + line if line.strip() else "" 
                for line in seg_code.strip().split("\n")
            )
            
            # Build segment block with comments
            block = f"""
        # ═══════════════════════════════════════════════════════════
        # SEGMENT {seg.id}: {seg.title} ({seg.duration:.1f}s, {mode})
        # Type: {seg.section_type}
        # ═══════════════════════════════════════════════════════════
{camera_code}{indented}
"""
            segments_code.append(block)
            prev_mode = mode
            
            # Brief pause between LLM calls to avoid rate limits
            if i < len(video_script.segments) - 1:
                time.sleep(0.3)
        
        # Footer with cleanup
        footer = """
        # ═══════════════════════════════════════════════════════════
        # END - Cleanup
        # ═══════════════════════════════════════════════════════════
        self.wait(0.3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)
"""
        
        full_code = header + "".join(segments_code) + footer
        print(f"   ✅ Code generated ({len(full_code):,} chars, {len(segments_code)} segments)")
        return full_code
    
    def render(self, code: str, topic: str) -> str:
        """
        Render video using Manim with optimized settings.
        
        Settings:
        - Quality: Configured via self.quality (default -qm = 720p30)
        - Caching: ENABLED for faster re-renders
        - Output: Named with topic and timestamp
        
        Args:
            code: Complete Python code to render
            topic: Topic name for output filename
            
        Returns:
            Path to rendered video file, or empty string on failure
        """
        print(f"   🎬 Rendering video (quality: {self.quality})...")
        
        safe_name = re.sub(r"[^\w\s-]", "", topic).replace(" ", "_")[:20]
        timestamp = int(time.time())
        output_name = f"PRISM_{safe_name}_{timestamp}"
        
        # Save generated code
        with open(GENERATED_SCRIPT_PATH, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"   📝 Saved: {GENERATED_SCRIPT_PATH}")
        
        try:
            # Build Manim command
            cmd = [
                sys.executable, "-m", "manim",
                f"-q{self.quality}",      # Quality setting
                # Caching is ENABLED (no --disable_caching flag)
                GENERATED_SCRIPT_PATH,
                "GenScene",
                "-o", output_name
            ]
            
            # Run Manim
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                cwd=SCRIPT_DIR,
                timeout=600  # 10 minute timeout
            )
            
            # Locate output file
            quality_dirs = {
                "l": "480p15",
                "m": "720p30", 
                "h": "1080p60"
            }
            video_dir = os.path.join(
                SCRIPT_DIR, "media", "videos", "generated_scene",
                quality_dirs.get(self.quality, "720p30")
            )
            video_path = os.path.join(video_dir, f"{output_name}.mp4")
            
            if os.path.exists(video_path):
                size_mb = os.path.getsize(video_path) / (1024 * 1024)
                print(f"   ✅ Rendered: {output_name}.mp4 ({size_mb:.1f} MB)")
                return video_path
            
            # Search for output if not at expected path
            if os.path.exists(video_dir):
                files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
                if files:
                    # Get newest file
                    newest = max(files, key=lambda x: os.path.getmtime(os.path.join(video_dir, x)))
                    found_path = os.path.join(video_dir, newest)
                    print(f"   ✅ Found: {newest}")
                    return found_path
            
            print(f"   ⚠️ Video not found at expected path: {video_path}")
            return video_path
            
        except subprocess.TimeoutExpired:
            print("   ❌ Render timeout (>10 minutes)")
            return ""
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr[-1000:] if e.stderr else "Unknown error"
            print(f"   ❌ Render failed:\n{error_msg}")
            return ""
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return ""


# ============== EXPORTS ==============
GENERATED_SCRIPT_PATH = GENERATED_SCRIPT_PATH  # For main.py


def generate_and_render(video_script: VideoScript, rag_context: str = "", quality: str = DEFAULT_QUALITY) -> str:
    """
    Convenience function: Generate code and render video.
    
    Args:
        video_script: VideoScript with all segments
        rag_context: RAG context for LLM prompting
        quality: Render quality ('l', 'm', 'h')
        
    Returns:
        Path to rendered video file
    """
    engine = ManimEngine(quality=quality)
    code = engine.generate_full_code(video_script, rag_context)
    return engine.render(code, video_script.topic)
