"""
PRISM Manim Engine - The "Cinematographer" Stage
=================================================
Uses Gemini (smart) to convert Director's detailed plan into perfect Manim code.

ROLE: Execute the Director's vision with flawless code
- Convert detailed instructions → valid Manim CE syntax
- Apply Khan Academy / 3Blue1Brown aesthetic
- Handle timing synchronization with audio
- Ensure zero LaTeX errors through post-processing

ARCHITECTURE:
Director's Plan JSON → Cinematographer (Gemini) → generated_scene.py → Render → Video

STYLE RULES:
- Background: BLACK (#000000)
- Split-screen: Notes LEFT (30%), Animation RIGHT (70%)
- Colors: BLUE (main), YELLOW (highlight), TEAL (secondary), GREEN (success)
- Typography: MathTex for math, Text for labels
- Animations: Write(), Create(), Transform(), Indicate(), FadeOut()
"""

import os
import sys
import re
import time
import subprocess
from typing import Dict, Optional, List

import google.generativeai as genai

from data_models import VideoScript, Segment


# ============== CONFIGURATION ==============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "generated_scene.py")

# Gemini API
GEMINI_API_KEY = "AIzaSyBZoIVx4TF852_TBe-qB9ASfUKUaadkpe8"
GEMINI_MODEL = "gemini-2.0-flash-exp"

genai.configure(api_key=GEMINI_API_KEY)

# Quality presets
QUALITY_PRESETS = {
    "l": ("480p15", 15),
    "m": ("720p30", 30),
    "h": ("1080p60", 60),
}
DEFAULT_QUALITY = "m"


# ============== CINEMATOGRAPHER SYSTEM PROMPT ==============
CINEMATOGRAPHER_PROMPT = '''You are an elite Manim Community Edition programmer creating Khan Academy / 3Blue1Brown style educational videos.

## 🎨 MANDATORY VISUAL STYLE

### Screen Layout (CRITICAL - Follow Exactly)
```
┌──────────────────────────────────────────────────────────┐
│              TITLE - YELLOW, font_size=44                │
│                     to_edge(UP)                          │
├─────────────────┬────────────────────────────────────────┤
│                 │                                        │
│   LEFT PANEL    │         MAIN ANIMATION                 │
│   (OPTIONAL)    │         CENTER or RIGHT * 2            │
│   LEFT * 5      │                                        │
│                 │         This is where ALL the          │
│   Small label   │         important visuals go:          │
│   only if       │         formulas, graphs, shapes       │
│   needed        │                                        │
│                 │                                        │
└─────────────────┴────────────────────────────────────────┘
```

### LEFT PANEL RULES (IMPORTANT!)
- The LEFT panel should contain ONLY a SHORT label (max 20 chars)
- Use font_size=20 or smaller
- Position at LEFT * 5 + UP * 2
- Do NOT put long text, code, or formulas on the left
- If blackboard_text is long, just show the FIRST WORD or skip it entirely
- Main content goes on the RIGHT side (RIGHT * 2 or CENTER)

### Color Palette (USE EXACTLY)
- YELLOW = titles, highlights, emphasis
- BLUE = primary shapes, main elements
- TEAL = secondary elements, labels
- WHITE = text, formulas
- GREEN = correct answers, success
- RED = warnings, errors

### Typography Rules (CRITICAL)
```python
# Math formulas - ALWAYS use MathTex with raw strings
MathTex(r"a^2 + b^2 = c^2", font_size=48, color=WHITE)
MathTex(r"x = \\frac{{-b \\pm \\sqrt{{b^2-4ac}}}}{{2a}}")

# Plain text - use Text
Text("Key Points", font_size=36, color=BLUE)
Text("• Bullet point", font_size=28, color=WHITE)

# NEVER DO THESE (will crash):
# Tex(r"\\bullet")     - Use Text("•") instead!
# MathTex(r"$x^2$")    - No $ signs inside MathTex!
```

### Animation Patterns
```python
# Text appearing (handwriting effect)
self.play(Write(text), run_time=1.5)

# Shapes appearing
self.play(Create(shape), run_time=1.0)

# Highlighting (sync with speech)
self.play(Indicate(term, color=YELLOW), run_time=0.5)

# Equation transforms
self.play(TransformMatchingTex(eq1, eq2), run_time=1.5)

# Movement
self.play(obj.animate.shift(RIGHT * 2), run_time=0.8)

# Clear screen between sections
self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)
```

### 3D Text Rule (IMPORTANT)
```python
# For ThreeDScene, always add text to fixed frame first:
title = Text("Title", font_size=44, color=YELLOW)
self.add_fixed_in_frame_mobjects(title)  # REQUIRED!
title.to_edge(UP)
self.play(Write(title))
```

## 📋 RAG EXAMPLES (Working Code)
{rag_context}

## 🎬 SECTION TO ANIMATE
{section_details}

## ⏱️ TIMING REQUIREMENT
Duration: {duration} seconds
- Your animations must fill this time
- End with self.wait() for remaining time

## 📝 OUTPUT RULES
1. Return ONLY executable Python code
2. NO imports, NO class definition
3. NO markdown code fences (```)
4. Start with a section comment
5. Put ALL main visuals on RIGHT side (RIGHT * 2) or CENTER
6. LEFT side: only tiny label or nothing
7. End with self.wait(X) where X fills remaining time

Generate the Manim code:'''


class ManimEngine:
    """
    The Cinematographer: Converts Director's plan into perfect Manim code.
    
    Uses Gemini for smart code generation with RAG context.
    Applies strict Khan Academy / 3Blue1Brown aesthetic.
    """
    
    def __init__(self, quality: str = DEFAULT_QUALITY):
        """Initialize Manim Engine with Gemini."""
        self.quality = quality
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        print(f"   🎥 Cinematographer initialized (Gemini, quality={quality})")
    
    def generate_full_scene(self, plan: Dict, video_script: VideoScript, rag_context: str = "") -> str:
        """
        Generate complete Manim scene from Director's production plan.
        
        Args:
            plan: Director's production plan with sections
            video_script: VideoScript with audio durations
            rag_context: RAG context with working code examples
            
        Returns:
            Complete Python code as string
        """
        print(f"   🎥 Generating Manim code for {len(plan.get('sections', []))} sections...")
        
        topic = plan.get("topic", "Educational Topic")
        sections = plan.get("sections", [])
        
        # Build the complete scene file
        header = self._generate_header(topic, len(sections))
        
        # Generate code for each section
        section_codes = []
        for i, section in enumerate(sections):
            # Get audio duration from video_script if available
            duration = section.get("duration", 10)
            if i < len(video_script.segments):
                duration = video_script.segments[i].duration or duration
            
            print(f"      Section {i+1}/{len(sections)}: {section.get('title', 'Unknown')} ({duration:.1f}s)")
            
            # Generate section code
            code = self._generate_section_code(
                section=section,
                duration=duration,
                is_first=(i == 0),
                rag_context=rag_context
            )
            
            section_codes.append(code)
            
            # Brief pause between API calls
            time.sleep(0.3)
        
        # Combine all parts
        footer = self._generate_footer()
        full_code = header + "\n".join(section_codes) + footer
        
        # Post-process to fix common issues
        full_code = self._post_process(full_code)
        
        print(f"   ✅ Generated {len(full_code):,} chars of Manim code")
        return full_code
    
    def _generate_header(self, topic: str, num_sections: int) -> str:
        """Generate the scene file header."""
        return f'''"""
PRISM Generated Scene
=====================
Topic: {topic}
Sections: {num_sections}
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
Style: Khan Academy / 3Blue1Brown
"""

from manim import *
import numpy as np

config.background_color = "#000000"


class GenScene(ThreeDScene):
    """Auto-generated educational animation."""
    
    def construct(self):
        # 2D camera setup
        self.set_camera_orientation(phi=0*DEGREES, theta=-90*DEGREES)
        
'''
    
    def _generate_section_code(self, section: Dict, duration: float, is_first: bool, rag_context: str) -> str:
        """Generate Manim code for a single section using Gemini."""
        section_id = section.get("id", 1)
        section_type = section.get("type", "concept")
        title = section.get("title", f"Section {section_id}")
        
        # Build section details for prompt
        section_details = f"""
Section ID: {section_id}
Type: {section_type}
Title: {title}
Duration: {duration:.1f} seconds

Narration (viewer hears):
"{section.get('narration', '')}"

Blackboard Text (LEFT side - use add_fixed_in_frame_mobjects):
{section.get('blackboard_text', '')}

Director's Animation Instructions:
{chr(10).join('- ' + str(instr) for instr in section.get('manim_instructions', []))}

Visual Mode: {section.get('visual_mode', '2D')}
Clear Previous: {"NO (first section)" if is_first else "YES - start with FadeOut all mobjects"}
"""
        
        prompt = CINEMATOGRAPHER_PROMPT.format(
            rag_context=rag_context[:3000] if rag_context else "No RAG context.",
            section_details=section_details,
            duration=duration
        )
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2500,
                )
            )
            
            code = response.text.strip()
            code = self._clean_code(code)
            indented = self._indent_code(code)
            
            return f"""
        # {'═'*60}
        # SECTION {section_id}: {title.upper()} ({duration:.1f}s)
        # Type: {section_type}
        # {'═'*60}
{indented}
"""
        except Exception as e:
            print(f"      ⚠️ LLM failed for section {section_id}: {e}")
            return self._fallback_code(section, duration, is_first)
    
    def _clean_code(self, code: str) -> str:
        """Clean LLM-generated code."""
        code = re.sub(r'```python\s*', '', code)
        code = re.sub(r'```\s*', '', code)
        code = re.sub(r'^from manim import.*?\n', '', code, flags=re.MULTILINE)
        code = re.sub(r'^import.*?\n', '', code, flags=re.MULTILINE)
        code = re.sub(r'^class\s+\w+.*?:\s*\n', '', code, flags=re.MULTILINE)
        code = re.sub(r'^\s*def construct\(self\):\s*\n', '', code, flags=re.MULTILINE)
        return code.strip()
    
    def _indent_code(self, code: str, spaces: int = 8) -> str:
        """Indent code block."""
        indent = " " * spaces
        return '\n'.join(
            indent + line if line.strip() else ""
            for line in code.split('\n')
        )
    
    def _fallback_code(self, section: Dict, duration: float, is_first: bool) -> str:
        """Generate fallback code when LLM fails."""
        section_id = section.get("id", 1)
        
        # Clean title - remove special chars that break Python strings
        title = section.get("title", f"Section {section_id}")[:30]
        title = title.replace('"', "'").replace("\\", "").replace("\n", " ").replace("\r", "")
        title = ''.join(c for c in title if ord(c) < 128)
        
        # Clean blackboard text - remove special chars that break Python strings
        blackboard = section.get("blackboard_text", title)
        # CRITICAL: Replace newlines FIRST before truncating
        blackboard = blackboard.replace("\n", " | ").replace("\r", "")
        blackboard = blackboard[:50]  # Truncate after newline replacement
        blackboard = blackboard.replace('"', "'").replace("\\", "")
        # Replace special math chars with ASCII equivalents
        blackboard = blackboard.replace("²", "^2").replace("³", "^3")
        blackboard = blackboard.replace("÷", "/").replace("×", "*")
        blackboard = blackboard.replace("≤", "<=").replace("≥", ">=")
        blackboard = blackboard.replace("≠", "!=").replace("±", "+/-")
        # Remove any remaining non-ASCII
        blackboard = ''.join(c for c in blackboard if ord(c) < 128)
        
        section_type = section.get("type", "concept")
        wait_time = max(duration - 4.5, 1.0)
        
        clear = "" if is_first else """
        # Clear previous
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)
"""
        
        # Visual based on section type - ALL visuals centered or slightly right
        if section_type == "hook":
            visual = '''
        # Hook visual - engaging question mark
        hook_text = Text("?", font_size=144, color=YELLOW)
        hook_text.move_to(ORIGIN)
        self.play(Write(hook_text), run_time=1.0)
        self.play(hook_text.animate.scale(1.3), run_time=0.5)
        self.play(hook_text.animate.scale(1/1.3), run_time=0.3)
        self.play(FadeOut(hook_text), run_time=0.5)'''
        elif section_type == "formula":
            visual = '''
        # Main formula - centered and prominent
        formula = MathTex(r"f(x) = ax^2 + bx + c", font_size=56, color=WHITE)
        formula.move_to(ORIGIN)
        box = SurroundingRectangle(formula, color=BLUE, buff=0.3)
        self.play(Write(formula), run_time=2.0)
        self.play(Create(box), run_time=0.5)
        self.play(Indicate(formula, color=YELLOW), run_time=0.8)'''
        elif section_type == "breakdown":
            visual = '''
        # Breakdown - color-coded parts
        eq = MathTex(r"a", r"x^2", r"+", r"b", r"x", r"+", r"c", font_size=56)
        eq[0].set_color(BLUE)
        eq[3].set_color(YELLOW)
        eq[6].set_color(TEAL)
        eq.move_to(ORIGIN)
        self.play(Write(eq), run_time=1.5)
        self.play(Indicate(eq[0], color=BLUE, scale_factor=1.3), run_time=0.5)
        self.play(Indicate(eq[3], color=YELLOW, scale_factor=1.3), run_time=0.5)
        self.play(Indicate(eq[6], color=TEAL, scale_factor=1.3), run_time=0.5)'''
        elif section_type == "example":
            visual = '''
        # Worked example - step by step
        step1 = MathTex(r"x^2 + 5x + 6 = 0", font_size=44, color=WHITE)
        step1.move_to(UP * 0.5)
        self.play(Write(step1), run_time=1.2)
        
        step2 = MathTex(r"x = -2", font_size=48, color=GREEN)
        step3 = MathTex(r"x = -3", font_size=48, color=GREEN)
        answers = VGroup(step2, step3).arrange(RIGHT, buff=1.5)
        answers.move_to(DOWN * 1)
        self.play(Write(step2), run_time=0.8)
        self.play(Write(step3), run_time=0.8)
        
        box = SurroundingRectangle(answers, color=GREEN, buff=0.3)
        self.play(Create(box), run_time=0.5)'''
        elif section_type == "visualization":
            visual = '''
        # Graph - centered axes with curve
        axes = Axes(
            x_range=[-4, 4, 1], y_range=[-2, 8, 2],
            x_length=6, y_length=4,
            axis_config={"color": WHITE, "include_tip": True}
        ).move_to(ORIGIN)
        curve = axes.plot(lambda x: x**2, color=BLUE, x_range=[-2.5, 2.5])
        label = MathTex(r"y = x^2", font_size=32, color=BLUE).next_to(curve, UR)
        self.add_fixed_in_frame_mobjects(label)
        self.play(Create(axes), run_time=1.0)
        self.play(Create(curve), run_time=1.5)
        self.play(Write(label), run_time=0.5)'''
        elif section_type == "summary":
            visual = '''
        # Summary - clean bullet points centered
        p1 = Text("• Key concept learned", font_size=28, color=WHITE)
        p2 = Text("• Formula applied", font_size=28, color=WHITE)
        p3 = Text("• Example solved", font_size=28, color=WHITE)
        points = VGroup(p1, p2, p3).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        points.move_to(ORIGIN)
        self.add_fixed_in_frame_mobjects(p1, p2, p3)
        self.play(Write(p1), run_time=0.7)
        self.play(Write(p2), run_time=0.7)
        self.play(Write(p3), run_time=0.7)'''
        else:
            visual = '''
        # Default - simple centered visual
        shape = Circle(radius=1.5, color=BLUE, fill_opacity=0.3)
        shape.move_to(ORIGIN)
        self.play(Create(shape), run_time=1.5)
        self.play(Indicate(shape, color=YELLOW), run_time=0.5)'''
        
        return f"""
        # {'═'*60}
        # SECTION {section_id}: {title.upper()} ({duration:.1f}s) [FALLBACK]
        # {'═'*60}
{clear}
        # Title
        title = Text("{title}", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)
{visual}
        
        self.wait({wait_time:.1f})
"""
    
    def _generate_footer(self) -> str:
        """Generate scene footer."""
        return '''
        # ═══════════════════════════════════════════════════════════
        # END - Cleanup
        # ═══════════════════════════════════════════════════════════
        self.wait(0.5)
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=1.0)
'''
    
    def _post_process(self, code: str) -> str:
        """Fix common Manim syntax issues."""
        # Deprecated methods
        code = re.sub(r"ShowCreation\(", "Create(", code)
        code = re.sub(r"TextMobject\(", "Text(", code)
        code = re.sub(r"TexMobject\(", "MathTex(", code)
        
        # LaTeX bullet fix (CRITICAL)
        code = code.replace(r'\\bullet', '•')
        code = code.replace(r'\bullet', '•')
        
        # Remove $ from MathTex
        code = re.sub(r'MathTex\s*\(\s*r?"\\?\$', 'MathTex(r"', code)
        code = re.sub(r'\\?\$"\s*\)', '")', code)
        
        # Ensure raw strings
        code = re.sub(r'(MathTex|Tex)\s*\(\s*"\\\\', r'\1(r"\\', code)
        
        return code
    
    def render(self, code: str, topic: str) -> str:
        """Render the generated Manim code to video."""
        print(f"   🎬 Rendering video (quality: {self.quality})...")
        
        safe_name = re.sub(r"[^\w\s-]", "", topic).replace(" ", "_")[:20]
        timestamp = int(time.time())
        output_name = f"PRISM_{safe_name}_{timestamp}"
        
        with open(GENERATED_SCRIPT_PATH, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"   📝 Code saved: {GENERATED_SCRIPT_PATH}")
        
        try:
            cmd = [
                sys.executable, "-m", "manim",
                f"-q{self.quality}",
                GENERATED_SCRIPT_PATH,
                "GenScene",
                "-o", output_name
            ]
            
            result = subprocess.run(
                cmd, check=True, capture_output=True, text=True,
                cwd=SCRIPT_DIR, timeout=600
            )
            
            quality_dirs = {"l": "480p15", "m": "720p30", "h": "1080p60"}
            video_dir = os.path.join(
                SCRIPT_DIR, "media", "videos", "generated_scene",
                quality_dirs.get(self.quality, "720p30")
            )
            video_path = os.path.join(video_dir, f"{output_name}.mp4")
            
            if os.path.exists(video_path):
                size_mb = os.path.getsize(video_path) / (1024 * 1024)
                print(f"   ✅ Rendered: {output_name}.mp4 ({size_mb:.1f} MB)")
                return video_path
            
            # Search for video
            if os.path.exists(video_dir):
                files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
                if files:
                    newest = max(files, key=lambda x: os.path.getmtime(os.path.join(video_dir, x)))
                    return os.path.join(video_dir, newest)
            
            return ""
            
        except subprocess.TimeoutExpired:
            print("   ❌ Render timeout")
            return ""
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Render failed:\n{e.stderr[-1000:] if e.stderr else 'Unknown'}")
            return ""
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return ""


# ============== EXPORTS ==============
__all__ = ['ManimEngine', 'GENERATED_SCRIPT_PATH', 'DEFAULT_QUALITY']
