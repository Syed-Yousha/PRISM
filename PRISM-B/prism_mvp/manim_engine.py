"""
PRISM Manim Engine - LLM Step 2: Code Generator
================================================
Converts PromptMaker's animation script into executable Manim code.

TWO-STEP LLM ARCHITECTURE:
┌─────────────────┐     ┌─────────────────┐
│  STEP 1: PROMPT │────>│  STEP 2: CODE   │  <-- YOU ARE HERE
│     MAKER       │     │   GENERATOR     │
└─────────────────┘     └─────────────────┘
       │                        │
  Topic + RAG            Refined Prompt
  Examples               → Manim Code

This module handles Step 2:
- Receives AnimationScript from PromptMaker (Step 1)
- Generates precise Manim code for each section
- Handles audio duration matching
- Error-resilient with fallbacks
"""

import os
import sys
import re
import time
import subprocess
from typing import Dict, Optional, List, TYPE_CHECKING

import google.generativeai as genai
from groq import Groq

from data_models import VideoScript, Segment
from config import (
    SCRIPT_DIR, GENERATED_SCRIPT_PATH, GEMINI_API_KEY, GEMINI_MODEL,
    GROQ_API_KEY, GROQ_MODEL, QUALITY_PRESETS
)

# Type hint for AnimationScript without circular import
if TYPE_CHECKING:
    from prompt_maker import AnimationScript

genai.configure(api_key=GEMINI_API_KEY)

DEFAULT_QUALITY = "m"


# ============== CODE GENERATOR SYSTEM PROMPT ==============
CODE_GENERATOR_PROMPT = '''You are an elite Manim Community Edition code generator creating CLEAN, EDUCATIONAL animations.

## 🎯 YOUR MISSION
Generate CLEAN, WELL-SPACED Manim code. Students must clearly see every element.
This is STEP 2 of a 2-step pipeline - Step 1 already planned the content.

## ⏱️ CRITICAL: AUDIO SYNC
- Target duration: {duration:.1f} seconds
- Your animations MUST fill this time EXACTLY
- End with self.wait(X) where X = remaining time
- NEVER exceed the duration!

## 🚨 CRITICAL: CLEAN SCREEN BETWEEN SECTIONS
**ALWAYS start EVERY section (except first) with:**
```python
# Clear previous content for clean slate
self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)
```

## 🖼️ SCREEN LAYOUT - PREVENT OVERLAP!
```
┌──────────────────────────────────────────────────────────┐
│    TITLE (font_size=40, YELLOW, to_edge(UP, buff=0.5))   │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│         MAIN CONTENT (font_size=44, CENTERED)            │
│              Use scale(0.8) if content is big            │
│                                                          │
│         Keep shapes SMALL: radius=1.5 max                │
│         Keep formulas readable: font_size=44             │
│                                                          │
├──────────────────────────────────────────────────────────┤
│    NOTES (font_size=24, TEAL, to_edge(DOWN, buff=0.5))   │
└──────────────────────────────────────────────────────────┘
```

## 📏 SPACING RULES (CRITICAL!)
- Title: `to_edge(UP, buff=0.5)` - NEVER overlap with content
- Main content: `move_to(ORIGIN)` or `move_to(UP*0.5)`
- Notes: `to_edge(DOWN, buff=0.5)` - NEVER overlap with content
- Between elements: Use `buff=0.5` minimum
- Shapes: Keep radius ≤ 1.5, use `.scale(0.7)` if needed

## 📝 NOTES DISPLAY

Blackboard Notes: {blackboard_notes}

**CORRECT way (small, at bottom, no overlap):**
```python
notes = VGroup()
for note in {blackboard_notes}:
    notes.add(Text(note, font_size=24, color=TEAL))
notes.arrange(RIGHT, buff=0.8)
notes.to_edge(DOWN, buff=0.5)
self.play(Write(notes), run_time=0.8)
```

## 🎨 TYPOGRAPHY RULES (SMALLER SIZES!)

### Math Formulas - ALWAYS use MathTex
```python
formula = MathTex(r"x = \\frac{{-b \\pm \\sqrt{{b^2-4ac}}}}{{2a}}", font_size=44)
formula.move_to(ORIGIN)  # Always center!
```

### Plain Text - use Text
```python
title = Text("Title Here", font_size=40, color=YELLOW)
title.to_edge(UP, buff=0.5)  # Always add buff!
```

### SIZING RULES:
- Title: font_size=40 (not bigger!)
- Main formula: font_size=44
- Labels: font_size=28
- Notes: font_size=24
- Shapes: radius ≤ 1.5, scale(0.7) if needed

### NEVER DO:
- `Tex(r"\\bullet")` → Use `Text("•")` instead!
- `MathTex(r"$x^2$")` → No $ signs in MathTex!
- `formula[5]` → Index errors! Use `formula` or `formula[0]`
- Large shapes that overlap other elements

## 🎬 ANIMATION PATTERNS

```python
# ALWAYS clear screen between sections (except first):
self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

self.play(Write(text), run_time=1.5)      # Text appearing
self.play(Create(shape), run_time=1.0)     # Shapes appearing  
self.play(Indicate(obj, color=YELLOW), run_time=0.5)  # Highlighting
self.wait(X)  # Fill remaining time
```

## 🎨 COLOR PALETTE
- YELLOW: titles, emphasis
- BLUE: primary elements
- TEAL: notes, secondary
- WHITE: text, formulas
- GREEN: success, answers

## � FORBIDDEN - NEVER DO THIS:
1. **NEVER use Text() to describe a visual - CREATE the visual instead!**
   - ❌ BAD: `Text("Here is a triangle showing the theorem")`
   - ✅ GOOD: `Polygon([0,0,0], [3,0,0], [0,4,0], color=BLUE)`

2. **NEVER write long sentences as main content**
   - ❌ BAD: `Text("To understand this concept we need to...", font_size=28)`
   - ✅ GOOD: Show formulas and shapes, keep text under 5 words

3. **ALWAYS create ACTUAL shapes for visualization sections**
   - Use Circle, Square, Triangle, Line, Arrow, Polygon, Axes, NumberLine
   - NEVER just describe what should be shown

## 📊 VISUAL CODE EXAMPLES:

### Fraction visualization (pie/sector):
```python
circle = Circle(radius=1.5, color=BLUE, stroke_width=3)
sector = Sector(outer_radius=1.5, angle=PI/2, color=YELLOW, fill_opacity=0.7)
self.play(Create(circle), Create(sector))
```

### Right triangle:
```python
triangle = Polygon([0,0,0], [3,0,0], [0,2,0], color=BLUE, stroke_width=3)
right_angle = Square(side_length=0.3).move_to([0.15, 0.15, 0])
```

### Graph/Plot:
```python
axes = Axes(x_range=[-3,3], y_range=[-2,5], x_length=6, y_length=4)
graph = axes.plot(lambda x: x**2, color=BLUE)
self.play(Create(axes), Create(graph))
```

### Number line:
```python
line = NumberLine(x_range=[0, 10, 1], length=10, include_numbers=True)
dot = Dot(line.n2p(5), color=RED)
```

## �📋 ANIMATION PLAN FROM STEP 1

Section: {title}
Type: {section_type}
Duration: {duration:.1f} seconds (MUST MATCH!)
Visual Mode: {visual_mode}
Clear Previous: {clear_previous}

**What the viewer hears (narration):**
"{narration}"

**Animation Plan:**
- Main Elements: {main_elements}
- Animations: {animations}
- Layout: {layout}
- Colors: {color_scheme}

**Blackboard Notes:** {blackboard_notes}

## 📤 OUTPUT RULES (CRITICAL!)
1. Return ONLY executable Python code
2. NO imports, NO class definition, NO markdown
3. **ALWAYS clear screen first** (except section 1): `self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)`
4. Keep elements SMALL and WELL-SPACED
5. Title at TOP with buff=0.5, Notes at BOTTOM with buff=0.5
6. Main content CENTERED with proper spacing
7. End with self.wait() to fill remaining time

Generate the Manim code now:'''


class ManimEngine:
    """
    LLM Step 2: Code Generator
    
    Converts PromptMaker's AnimationScript into executable Manim code.
    Uses Groq (primary) with Gemini fallback.
    """
    
    def __init__(self, quality: str = DEFAULT_QUALITY):
        """Initialize Code Generator."""
        self.quality = quality
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        print(f"   🔧 Code Generator initialized (Groq primary, quality={quality})")
    
    def generate_from_script(self, animation_script: 'AnimationScript', video_script: VideoScript) -> str:
        """
        Generate Manim code from AnimationScript (Step 1 output).
        
        This is the main entry point for the 2-step pipeline.
        
        Args:
            animation_script: AnimationScript from PromptMaker (Step 1)
            video_script: VideoScript with audio durations
            
        Returns:
            Complete Python code as string
        """
        topic = animation_script.topic
        sections = animation_script.sections
        segments = video_script.segments
        
        print(f"   🔧 Code Generator processing {len(sections)} sections...")
        
        # Build header
        header = self._generate_header(topic, len(sections))
        
        # Generate code for each section
        section_codes = []
        for i, section in enumerate(sections):
            # Match section with audio segment for duration
            segment = segments[i] if i < len(segments) else None
            duration = segment.duration if segment else section.get("duration_estimate", 8.0)
            
            print(f"      Section {i+1}/{len(sections)}: {section.get('title', 'Unknown')} ({duration:.1f}s)")
            
            code = self._generate_section_code_from_plan(
                section=section,
                duration=duration,
                is_first=(i == 0)
            )
            
            if not code:
                print(f"         ⚠️ Using fallback for section {i+1}")
                segment_for_fallback = segment or Segment(
                    id=section.get("id", i+1),
                    title=section.get("title", f"Section {i+1}"),
                    section_type=section.get("type", "content"),
                    duration=duration
                )
                code = self._fallback_code(segment_for_fallback, is_first=(i == 0), topic=topic)
            
            section_codes.append(code)
            time.sleep(0.5)  # Rate limiting
        
        # Combine and post-process
        footer = self._generate_footer()
        full_code = header + "\n".join(section_codes) + footer
        full_code = self._post_process(full_code)
        
        print(f"   ✅ Generated {len(full_code):,} chars of Manim code")
        return full_code
    
    def _generate_section_code_from_plan(self, section: Dict, duration: float, is_first: bool) -> Optional[str]:
        """Generate Manim code from a section's animation plan."""
        # Extract animation plan
        anim_plan = section.get("animation_plan", {})
        bb_notes = section.get("blackboard_notes", [])
        
        # Build prompt with all the plan details
        prompt = CODE_GENERATOR_PROMPT.format(
            duration=duration,
            title=section.get("title", "Section"),
            section_type=section.get("type", "content"),
            visual_mode=section.get("visual_mode", "2D"),
            clear_previous="NO (first section)" if is_first else "YES",
            narration=section.get("narration", ""),
            blackboard_notes=str(bb_notes) if bb_notes else "[]",
            main_elements=", ".join(anim_plan.get("main_elements", ["No specific elements"])),
            animations=", ".join(anim_plan.get("animations", ["Standard animations"])),
            layout=anim_plan.get("layout", "Centered layout"),
            color_scheme=str(anim_plan.get("color_scheme", {}))
        )
        
        # Try Groq first
        code = None
        try:
            groq_response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2500,
            )
            code = groq_response.choices[0].message.content.strip()
            print(f"         ✅ Groq success")
        except Exception as e:
            print(f"         ⚠️ Groq failed: {str(e)[:60]}...")
            
            # Gemini fallback
            try:
                print(f"         🔄 Trying Gemini fallback...")
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=2500,
                    )
                )
                code = response.text.strip()
                print(f"         ✅ Gemini fallback success")
            except Exception as gemini_e:
                print(f"         ⚠️ Gemini failed: {str(gemini_e)[:60]}...")
                return None
        
        if code:
            code = self._clean_code(code)
            indented = self._indent_code(code)
            
            section_id = section.get("id", "?")
            title = section.get("title", "Section").upper()
            
            return f"""
        # {'═'*60}
        # SECTION {section_id}: {title} ({duration:.1f}s)
        # Type: {section.get('type', 'content')}
        # {'═'*60}
{indented}
"""
        return None
    
    # Legacy method for backward compatibility
    def generate_code(self, video_script: VideoScript, rag_context: str = "", max_retries: int = 2) -> str:
        """
        Generate complete Manim scene from VideoScript.
        
        Args:
            video_script: VideoScript with segments and REAL audio durations
            rag_context: RAG context with working code examples
            max_retries: Retries per section on LLM failure
            
        Returns:
            Complete Python code as string
        """
        topic = video_script.topic
        segments = video_script.segments
        
        print(f"   🔧 Engineer generating code for {len(segments)} sections...")
        
        if rag_context:
            print(f"   📚 RAG context: {len(rag_context):,} chars")
        
        # Build header
        header = self._generate_header(topic, len(segments))
        
        # Generate code for each section with retry
        section_codes = []
        for i, segment in enumerate(segments):
            print(f"      Section {i+1}/{len(segments)}: {segment.title} ({segment.duration:.1f}s)")
            
            code = None
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    code = self._generate_section_code(
                        segment=segment,
                        is_first=(i == 0),
                        rag_context=rag_context,
                        topic=topic
                    )
                    if code:
                        break
                except Exception as e:
                    last_error = str(e)
                    if attempt < max_retries:
                        print(f"         ⚠️ Retry {attempt + 1}/{max_retries}: {last_error[:50]}...")
                        time.sleep(1)
            
            if not code:
                print(f"         ⚠️ Using fallback for section {segment.id}")
                code = self._fallback_code(segment, is_first=(i == 0), topic=topic)
            
            section_codes.append(code)
            time.sleep(1)  # Rate limiting
        
        # Combine and post-process
        footer = self._generate_footer()
        full_code = header + "\n".join(section_codes) + footer
        full_code = self._post_process(full_code)
        
        print(f"   ✅ Generated {len(full_code):,} chars of Manim code")
        return full_code
    
    def _generate_header(self, topic: str, num_sections: int) -> str:
        """Generate scene file header."""
        return f'''"""
PRISM Generated Scene - Audio-Synced
=====================================
Topic: {topic}
Sections: {num_sections}
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}
Style: Khan Academy / 3Blue1Brown
"""

from manim import *
import numpy as np

config.background_color = "#1e1e1e"


class GenScene(Scene):
    """Auto-generated educational animation with clean 2D layout."""
    
    def construct(self):
'''
    
    def _generate_section_code(self, segment: Segment, is_first: bool, rag_context: str, topic: str) -> str:
        """Generate Manim code for a single section (legacy segment-based)."""
        # Get blackboard notes as list
        bb_notes = segment.get_blackboard_notes_list()
        bb_notes_str = str(bb_notes) if bb_notes else "[]"
        
        # Build prompt using the new CODE_GENERATOR_PROMPT format
        prompt = CODE_GENERATOR_PROMPT.format(
            duration=segment.duration,
            title=segment.title,
            section_type=segment.section_type,
            visual_mode=segment.visual_mode,
            clear_previous="NO (first section)" if is_first else "YES",
            narration=segment.narration or "No narration",
            blackboard_notes=bb_notes_str,
            main_elements=", ".join(segment.visual_instructions[:3]) if segment.visual_instructions else "Standard visual elements",
            animations="Standard animations for " + segment.section_type,
            layout="Centered layout",
            color_scheme="{}"
        )
        
        # Try Groq first
        code = None
        try:
            groq_response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2500,
            )
            code = groq_response.choices[0].message.content.strip()
            print(f"         ✅ Groq success")
        except Exception as e:
            print(f"         ⚠️ Groq failed: {str(e)[:60]}...")
            
            # Gemini fallback
            try:
                print(f"         🔄 Trying Gemini fallback...")
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=2500,
                    )
                )
                code = response.text.strip()
                print(f"         ✅ Gemini fallback success")
            except Exception as gemini_e:
                print(f"         ⚠️ Gemini failed: {str(gemini_e)[:60]}...")
                return None
        
        if code:
            code = self._clean_code(code)
            indented = self._indent_code(code)
            
            return f"""
        # {'═'*60}
        # SECTION {segment.id}: {segment.title.upper()} ({segment.duration:.1f}s)
        # Type: {segment.section_type}
        # {'═'*60}
{indented}
"""
        return None
    
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
    
    def _fallback_code(self, segment: Segment, is_first: bool, topic: str) -> str:
        """Generate reliable fallback code when LLM fails."""
        title = segment.title[:25].replace('"', "'").replace("\\", "")
        title = ''.join(c for c in title if ord(c) < 128)
        
        clean_topic = topic[:20].replace('"', "'").replace("\\", "")
        clean_topic = ''.join(c for c in clean_topic if ord(c) < 128)
        
        wait_time = max(segment.duration - 4.0, 1.0)
        
        # Get blackboard notes
        bb_notes = segment.get_blackboard_notes_list()[:3]  # Max 3 notes
        
        clear = "" if is_first else """
        # Clear previous
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)
"""
        
        # Build VGroup code for notes (centered at bottom)
        if bb_notes:
            notes_code = f'''
        # Notes (centered at bottom)
        notes = VGroup()
        note_texts = {bb_notes}
        for note in note_texts:
            notes.add(Text(note, font_size=24, color=TEAL))
        notes.arrange(RIGHT, buff=0.8)
        notes.to_edge(DOWN, buff=0.5)
        self.play(Write(notes), run_time=0.8)
'''
        else:
            notes_code = ""
        
        # Section type specific visual (CENTERED, CLEAN)
        if segment.section_type == "hook":
            visual = f'''
        # Hook visual (centered)
        main_text = Text("{clean_topic}", font_size=44, color=BLUE)
        main_text.move_to(ORIGIN)
        self.play(Write(main_text), run_time=1.5)
'''
        elif segment.section_type == "formula":
            visual = f'''
        # Formula display (centered)
        formula = MathTex(r"f(x) = ax^2 + bx + c", font_size=44, color=WHITE)
        formula.move_to(ORIGIN)
        self.play(Write(formula), run_time=2.0)
'''
        elif segment.section_type == "example":
            visual = f'''
        # Worked example (centered)
        step1 = Text("Step 1: Setup", font_size=32, color=WHITE)
        step2 = Text("Step 2: Solve", font_size=32, color=YELLOW)
        step3 = Text("Step 3: Answer", font_size=32, color=GREEN)
        steps = VGroup(step1, step2, step3).arrange(DOWN, buff=0.4)
        steps.move_to(ORIGIN)
        self.play(Write(step1), run_time=0.6)
        self.play(Write(step2), run_time=0.6)
        self.play(Write(step3), run_time=0.6)
'''
        elif segment.section_type == "summary":
            visual = f'''
        # Summary (centered)
        summary = Text("Key Takeaways", font_size=40, color=YELLOW)
        summary.move_to(UP * 0.3)
        check = Text("Remember the formula!", font_size=28, color=GREEN)
        check.next_to(summary, DOWN, buff=0.4)
        self.play(Write(summary), run_time=0.8)
        self.play(Write(check), run_time=0.5)
'''
        else:
            visual = f'''
        # Content display (centered)
        content = Text("{clean_topic}", font_size=40, color=BLUE)
        content.move_to(ORIGIN)
        self.play(Write(content), run_time=1.5)
'''
        
        return f"""
        # {'═'*60}
        # SECTION {segment.id}: {title.upper()} ({segment.duration:.1f}s) [FALLBACK]
        # {'═'*60}
{clear}
        # Title
        title = Text("{title}", font_size=40, color=YELLOW)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)
{notes_code}{visual}
        self.wait({wait_time:.2f})
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
        
        # REMOVE add_fixed_in_frame_mobjects (only for 3D scenes, we use 2D Scene now)
        code = re.sub(r'\s*self\.add_fixed_in_frame_mobjects\([^)]*\)\s*\n?', '\n', code)
        
        # REMOVE set_camera_orientation (only for 3D scenes)
        code = re.sub(r'\s*self\.set_camera_orientation\([^)]*\)\s*\n?', '\n', code)
        
        # LaTeX bullet fix
        code = code.replace(r'\\bullet', '•')
        code = code.replace(r'\bullet', '•')
        
        # Remove $ from MathTex
        code = re.sub(r'MathTex\s*\(\s*r?"\\?\$', 'MathTex(r"', code)
        code = re.sub(r'\\?\$"\s*\)', '")', code)
        
        # Ensure raw strings
        code = re.sub(r'(MathTex|Tex)\s*\(\s*"\\\\', r'\1(r"\\', code)
        
        # FIX: Dot with 2D point → 3D point (CRITICAL!)
        # Dot(point=(-2, 0), ...) → Dot(point=np.array([-2, 0, 0]), ...)
        code = re.sub(
            r'Dot\s*\(\s*point\s*=\s*\(\s*([^,]+)\s*,\s*([^,)]+)\s*\)',
            r'Dot(point=np.array([\1, \2, 0]))',
            code
        )
        # Also handle Dot((-2, 0)) without point= keyword
        code = re.sub(
            r'Dot\s*\(\s*\(\s*([^,]+)\s*,\s*([^,)]+)\s*\)\s*\)',
            r'Dot(point=np.array([\1, \2, 0]))',
            code
        )
        
        # FIX: 3D object syntax
        code = re.sub(r'Sphere\s*\(\s*color\s*=\s*([^,)]+)\s*,\s*radius\s*=\s*([^,)]+)\s*\)', 
                      r'Sphere(radius=\2).set_color(\1)', code)
        code = re.sub(r'Sphere\s*\(\s*radius\s*=\s*([^,)]+)\s*,\s*color\s*=\s*([^,)]+)\s*\)',
                      r'Sphere(radius=\1).set_color(\2)', code)
        
        code = re.sub(r'Cone\s*\(\s*color\s*=\s*([^,)]+)\s*,\s*radius\s*=\s*([^,)]+)\s*,\s*height\s*=\s*([^,)]+)\s*\)',
                      r'Cone(base_radius=\2, height=\3).set_color(\1)', code)
        code = re.sub(r'Cone\s*\(\s*radius\s*=\s*([^,)]+)\s*,\s*height\s*=\s*([^,)]+)\s*\)',
                      r'Cone(base_radius=\1, height=\2)', code)
        
        # FIX: MathTex indexing issues - high indices cause IndexError
        code = re.sub(r'Indicate\s*\(\s*(\w+)\s*\[\s*([3-9]|\d{2,})\s*\]', r'Indicate(\1', code)
        code = re.sub(r'(\w+)\s*\[\s*([4-9]|\d{2,})\s*\]', r'\1[0]', code)
        
        # FIX: ParametricFunction needs 3D output
        code = re.sub(
            r'ParametricFunction\s*\(\s*lambda\s+(\w+)\s*:\s*\(\s*([^,]+)\s*,\s*([^,)]+)\s*\)',
            r'ParametricFunction(lambda \1: np.array([\2, \3, 0])',
            code
        )
        
        # FIX: Remove problematic pipe characters in Text
        code = re.sub(r'Text\s*\(\s*["\']([^"\']*\|[^"\']*)["\']', 
                      lambda m: f'Text("{m.group(1).split("|")[0].strip()}"', code)
        
        # FIX: Polygon with 2D points → 3D points
        # Polygon([(-1, -1), (1, -1), (0, 1)], ...) → use proper 3D coords
        def fix_polygon_2d(match):
            """Convert 2D polygon points to 3D."""
            points_str = match.group(1)
            rest = match.group(2) if match.group(2) else ""
            # Parse the 2D points and add z=0
            # Simple fix: replace (x, y) with [x, y, 0]
            fixed = re.sub(r'\(\s*([^,]+)\s*,\s*([^)]+)\s*\)', r'[\1, \2, 0]', points_str)
            return f'Polygon({fixed}{rest})'
        
        code = re.sub(
            r'Polygon\s*\(\s*\[((?:\s*\([^)]+\)\s*,?\s*)+)\](\s*,\s*[^)]+)?\)',
            fix_polygon_2d,
            code
        )
        
        return code
    
    def render(self, code: str, topic: str, max_retries: int = 2) -> str:
        """
        Render the generated Manim code to video with retry on error.
        
        Args:
            code: Complete Manim Python code
            topic: Topic for filename
            max_retries: Number of retries on render failure
            
        Returns:
            Path to rendered video, or empty string on failure
        """
        print(f"   🎬 Rendering video (quality: {self.quality})...")
        
        safe_name = re.sub(r"[^\w\s-]", "", topic).replace(" ", "_")[:20]
        timestamp = int(time.time())
        output_name = f"PRISM_{safe_name}_{timestamp}"
        
        # Save code
        with open(GENERATED_SCRIPT_PATH, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"   📝 Code saved: {GENERATED_SCRIPT_PATH}")
        
        for attempt in range(max_retries + 1):
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
                
                # Find output video
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
                
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr[-500:] if e.stderr else "Unknown error"
                print(f"   ⚠️ Render error (attempt {attempt + 1}/{max_retries + 1}):\n{error_msg}")
                
                if attempt < max_retries:
                    # Try to fix common errors and retry
                    code = self._fix_render_error(code, error_msg)
                    with open(GENERATED_SCRIPT_PATH, "w", encoding="utf-8") as f:
                        f.write(code)
                    print(f"   🔄 Applied fixes, retrying...")
                else:
                    print(f"   ❌ Render failed after {max_retries + 1} attempts")
                    print(f"   📝 Debug code at: {GENERATED_SCRIPT_PATH}")
                    return ""
                    
            except subprocess.TimeoutExpired:
                print("   ❌ Render timeout")
                return ""
            except Exception as e:
                print(f"   ❌ Error: {e}")
                return ""
        
        return ""
    
    def _fix_render_error(self, code: str, error_msg: str) -> str:
        """Attempt to fix code based on render error."""
        # Index out of range - remove problematic indexing
        if "IndexError" in error_msg or "list index out of range" in error_msg:
            code = re.sub(r'(\w+)\s*\[\s*\d+\s*\]', r'\1', code)
        
        # ValueError with arrays - fix ParametricFunction
        if "ValueError" in error_msg and "array" in error_msg:
            code = re.sub(
                r'ParametricFunction\s*\(\s*lambda\s+(\w+)\s*:\s*\(\s*([^,]+)\s*,\s*([^,)]+)\s*\)',
                r'ParametricFunction(lambda \1: np.array([\2, \3, 0])',
                code
            )
        
        # Undefined name - comment out problematic lines
        if "NameError" in error_msg:
            match = re.search(r"name '(\w+)' is not defined", error_msg)
            if match:
                undefined = match.group(1)
                code = re.sub(rf'.*{undefined}.*\n', '# REMOVED: undefined variable\n', code)
        
        return code
    
    # Legacy compatibility
    def generate_full_scene(self, plan: Dict, video_script: VideoScript, rag_context: str) -> str:
        """Legacy method for backward compatibility."""
        return self.generate_code(video_script, rag_context)


# ============== EXPORTS ==============
__all__ = ['ManimEngine', 'GENERATED_SCRIPT_PATH', 'DEFAULT_QUALITY']


# ============== TESTING ==============
if __name__ == "__main__":
    print("=" * 60)
    print("🔧 PRISM Manim Engine (Engineer) Test")
    print("=" * 60)
    
    # Create test VideoScript
    from data_models import VideoScript, Segment
    
    script = VideoScript(topic="Test Topic")
    script.add_segment(Segment(
        id=1,
        title="Test Section",
        narration="This is a test.",
        blackboard_notes=["Note 1", "Note 2"],
        visual_instructions=["Show title", "Display content"],
        section_type="hook",
        duration=10.0
    ))
    
    engine = ManimEngine(quality="l")
    code = engine.generate_code(script, rag_context="")
    
    print(f"\nGenerated code preview ({len(code)} chars):")
    print(code[:1000])
    
    print("\n✅ Engineer test complete")
