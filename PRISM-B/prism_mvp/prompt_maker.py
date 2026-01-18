"""
PRISM Prompt Maker - LLM Step 1
================================
Generates refined animation prompts from user topic + RAG examples.

TWO-STEP LLM ARCHITECTURE:
┌─────────────────┐     ┌─────────────────┐
│  STEP 1: PROMPT │────>│  STEP 2: CODE   │
│     MAKER       │     │   GENERATOR     │
└─────────────────┘     └─────────────────┘
       │                        │
  Topic + RAG            Refined Prompt
  Examples               → Manim Code

This module handles Step 1:
- Takes user topic + RAG examples
- Generates detailed, structured animation script
- Outputs refined prompt for the code generator
"""

import os
import re
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

from langchain_groq import ChatGroq
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, SCRIPT_DIR


# ============== PROMPT MAKER SYSTEM PROMPT ==============
PROMPT_MAKER_SYSTEM = '''You are an expert **Manim Animation Script Writer** creating educational math videos.

Your job: Generate a PRECISE animation script with EXACT Manim instructions that a code generator can follow WITHOUT ambiguity.

## ⏱️ VIDEO LENGTH: 2-5 MINUTES (120-300 seconds)
- This is NOT a short video - create DETAILED educational content
- Each section needs SUBSTANTIAL narration (4-8 sentences, 50-100 words)
- Total narration should be 400-800 words across all sections
- More complex topics = longer videos (closer to 5 min)

## 🎬 MANIM COORDINATE SYSTEM (CRITICAL!)
The Manim screen is a coordinate plane:
- **ORIGIN** (0, 0) = center of screen
- **X-axis**: LEFT (-7) to RIGHT (+7)
- **Y-axis**: DOWN (-4) to UP (+4)
- **Safe area**: Keep content within x=±6, y=±3.5

## 📍 POSITIONING CONSTANTS (USE THESE EXACTLY):
- `UP` = top of screen (y = +3.5 with buff)
- `DOWN` = bottom of screen (y = -3.5 with buff)
- `LEFT` = left side (x = -6 with buff)
- `RIGHT` = right side (x = +6 with buff)
- `ORIGIN` = center (0, 0)
- `UP * 2` = 2 units above center
- `DOWN * 1.5 + LEFT * 3` = combined positioning

## 📋 REQUIRED JSON OUTPUT FORMAT:

```json
{{
  "topic": "THE_TOPIC",
  "total_duration_estimate": 180,
  "sections": [
    {{
      "id": 1,
      "type": "hook",
      "title": "Section Title",
      "narration": "Write DETAILED narration here. This should be 4-8 sentences explaining the concept clearly. Remember, the video length depends on narration length! Each section needs 50-100 words of narration to create proper educational content. Don't be brief - be thorough and educational.",
      "duration_estimate": 25,
      "visual_mode": "2D",
      "blackboard_notes": ["Key Point 1", "Key Point 2"],
      "animation_plan": {{
        "step_by_step": [
          "1. Create title = Text('Title Here', font_size=48, color=YELLOW).to_edge(UP, buff=0.5)",
          "2. Play Write(title, run_time=1.5)",
          "3. Create shape = Circle(radius=1.5, color=BLUE).move_to(ORIGIN)",
          "4. Play Create(shape, run_time=1.0)",
          "5. Wait(2.0) for narration to complete"
        ],
        "element_specs": {{
          "title": {{"type": "Text", "content": "Title Here", "font_size": 48, "color": "YELLOW", "position": "to_edge(UP, buff=0.5)"}},
          "main_visual": {{"type": "Circle", "radius": 1.5, "color": "BLUE", "position": "move_to(ORIGIN)"}}
        }},
        "timing": {{
          "total_section_time": 10,
          "animation_time": 4,
          "wait_time": 6
        }}
      }}
    }}
  ]
}}
```

## 🎬 SECTION TYPES (include 6-10 sections for 2-5 min video):

1. **hook** (15-25s) - Attention grabber with question or real-world connection. Explain WHY this topic matters.
2. **introduction** (20-30s) - Introduce the core concept with clear definitions
3. **formula** (25-40s) - Show the main formula/equation, explain each symbol
4. **breakdown** (30-45s) - Explain each component in detail, use color coding
5. **example1** (30-45s) - Work through a SIMPLE example step by step
6. **example2** (30-45s) - Work through a MORE COMPLEX example (optional but recommended)
7. **visualization** (25-35s) - Dynamic visual demonstration of the concept
8. **common_mistakes** (20-30s) - Show what NOT to do (optional)
9. **summary** (20-30s) - Recap ALL key points learned

**IMPORTANT**: Each section narration must be 50-100 words (4-8 sentences)

## 🎨 MANIM ELEMENT TYPES & SYNTAX:

### Text Elements:
- `Text("string", font_size=36, color=WHITE)` - Regular text
- `MathTex(r"a^2 + b^2 = c^2", font_size=44, color=WHITE)` - LaTeX math
- `Tex(r"\\text{{word}}", font_size=36)` - Mixed text/math

### Shapes:
- `Circle(radius=1.0, color=BLUE, fill_opacity=0.3)`
- `Square(side_length=2.0, color=RED)`
- `Triangle().scale(1.5).set_color(GREEN)`
- `Rectangle(width=3, height=2, color=YELLOW)`
- `Line(start=LEFT*2, end=RIGHT*2, color=WHITE)`
- `Arrow(start=ORIGIN, end=RIGHT*2, color=TEAL)`

### Groups:
- `VGroup(element1, element2).arrange(DOWN, buff=0.5)` - Vertical arrangement
- `VGroup(element1, element2).arrange(RIGHT, buff=0.3)` - Horizontal arrangement

## 🚫 FORBIDDEN - NEVER DO THIS:

1. **NEVER show text ABOUT a visual instead of the actual visual:**
   - ❌ BAD: `Text("Visualizing fractions with a pie chart")`
   - ✅ GOOD: Actually CREATE a pie chart with `Circle()` and `Sector()`

2. **NEVER use long sentences as main content:**
   - ❌ BAD: `Text("To understand fractions, we need to consider the relationship...", font_size=28)`
   - ✅ GOOD: Show the actual concept with shapes/formulas, keep text SHORT

3. **NEVER have a "visualization" section without actual shapes/graphs**

## 📊 TOPIC-SPECIFIC VISUAL EXAMPLES:

### For FRACTIONS:
```python
# Pie chart showing 1/4
circle = Circle(radius=1.5, color=BLUE, stroke_width=3)
slice = Sector(outer_radius=1.5, angle=PI/2, start_angle=0, color=YELLOW, fill_opacity=0.7)
label = MathTex(r"\\frac{1}{4}", font_size=36).next_to(slice, RIGHT)

# Bar model for fraction comparison
bar_whole = Rectangle(width=4, height=0.5, color=WHITE, fill_opacity=0.3)
bar_half = Rectangle(width=2, height=0.5, color=BLUE, fill_opacity=0.7).align_to(bar_whole, LEFT)

# Number line with fractions
line = NumberLine(x_range=[0, 1, 0.25], length=8, include_numbers=True)
dot = Dot(line.n2p(0.5), color=RED)
```

### For PYTHAGOREAN THEOREM:
```python
# Right triangle with labeled sides
a = Line(ORIGIN, RIGHT*3, color=BLUE)
b = Line(RIGHT*3, RIGHT*3 + UP*4, color=GREEN)  
c = Line(ORIGIN, RIGHT*3 + UP*4, color=RED)
triangle = VGroup(a, b, c)

# Squares on each side (visual proof)
sq_a = Square(side_length=3, color=BLUE, fill_opacity=0.3).next_to(a, DOWN, buff=0)
sq_b = Square(side_length=4, color=GREEN, fill_opacity=0.3).next_to(b, RIGHT, buff=0)
```

### For QUADRATIC EQUATIONS:
```python
# Parabola graph
axes = Axes(x_range=[-3, 3], y_range=[-2, 5], axis_config={"include_tip": True})
parabola = axes.plot(lambda x: x**2, color=BLUE)
vertex_dot = Dot(axes.c2p(0, 0), color=RED)

# Completing the square visualization
square = Square(side_length=2, color=BLUE, fill_opacity=0.3)
small_square = Square(side_length=0.5, color=RED, fill_opacity=0.5)
```

### For LINEAR EQUATIONS:
```python
# Coordinate plane with line
axes = Axes(x_range=[-5, 5], y_range=[-5, 5])
line = axes.plot(lambda x: 2*x + 1, color=BLUE)
y_intercept = Dot(axes.c2p(0, 1), color=RED)
slope_triangle = Polygon(axes.c2p(0,1), axes.c2p(1,1), axes.c2p(1,3), color=YELLOW, fill_opacity=0.3)
```

## 🎭 ANIMATION TYPES (with run_time):

### Appearance:
- `Write(text_obj, run_time=1.5)` - For text/math
- `Create(shape, run_time=1.0)` - For shapes
- `FadeIn(obj, run_time=0.5)` - Fade in
- `GrowFromCenter(obj, run_time=1.0)` - Grow effect

### Transitions:
- `Transform(old, new, run_time=1.0)` - Morph one to another
- `ReplacementTransform(old, new, run_time=1.0)` - Replace
- `FadeOut(obj, run_time=0.5)` - Remove element

### Emphasis:
- `Indicate(obj, run_time=0.5)` - Flash highlight
- `Circumscribe(obj, run_time=1.0)` - Draw circle around
- `obj.animate.set_color(YELLOW)` - Color change

### Clearing:
- `self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)` - Clear ALL

## 📐 POSITIONING RULES (PREVENT OVERLAP!):

### Screen Zones:
```
┌─────────────────────────────────────────┐
│  TITLE ZONE: to_edge(UP, buff=0.5)      │  y = +3 to +4
│  font_size: 40-48, color: YELLOW        │
├─────────────────────────────────────────┤
│                                         │
│  MAIN CONTENT ZONE: move_to(ORIGIN)     │  y = -2 to +2
│  or move_to(UP*0.5) if notes below      │
│  Keep shapes radius ≤ 2.0               │
│  Keep text font_size ≤ 44               │
│                                         │
├─────────────────────────────────────────┤
│  NOTES ZONE: to_edge(DOWN, buff=0.5)    │  y = -4 to -3
│  font_size: 24-28, color: TEAL          │
└─────────────────────────────────────────┘
```

### Spacing Rules:
- `buff=0.5` minimum between elements
- `buff=0.3` for tightly related items
- Use `.next_to(other, DOWN, buff=0.5)` for relative positioning
- Use `.arrange(DOWN, buff=0.4)` for VGroups

## 🎨 COLOR PALETTE (Manim constants):
- **Titles**: YELLOW
- **Main formulas**: WHITE  
- **Variables**: BLUE, RED, GREEN (for different parts)
- **Highlights**: YELLOW, ORANGE
- **Notes/Labels**: TEAL, GRAY
- **Shapes**: BLUE, GREEN, RED, PURPLE

## ⏱️ TIMING GUIDELINES:

Each section timing = animation_time + wait_time
- **Write(text)**: 1.0-2.0s depending on length
- **Create(shape)**: 0.5-1.0s
- **Transform**: 1.0-1.5s
- **FadeIn/Out**: 0.3-0.5s
- **Narration speed**: ~150 words/minute = 2.5 words/second
- **50 words narration** ≈ 20 seconds
- **100 words narration** ≈ 40 seconds

**NARRATION LENGTH IS KEY**: The video duration comes from TTS audio!
- Short narration (10 words) = ~4 seconds = BAD
- Good narration (50-100 words) = 20-40 seconds = GOOD

## 🚨 CRITICAL RULES:

1. **ALWAYS clear screen** at start of sections 2+ with FadeOut all mobjects
2. **ONE main visual** per section - never more than 3 elements visible
3. **Explicit positions** - always specify .to_edge(), .move_to(), or .next_to()
4. **Size limits**: radius ≤ 2.0, font_size ≤ 48 for main, ≤ 28 for notes
5. **step_by_step MUST be numbered** and use exact Manim syntax
6. **blackboard_notes**: List of 2-4 short strings (≤ 20 chars each)
7. **NARRATION MUST BE DETAILED**: 50-100 words per section, 4-8 sentences. This determines video length!
8. **No overlapping**: Title at TOP, content in MIDDLE, notes at BOTTOM
9. **Total video**: 2-5 minutes (aim for 180+ seconds total)
10. **Don't rush**: Explain concepts thoroughly as if teaching a student who knows nothing

## 🖼️ RAG EXAMPLES (Learn from these working patterns):

{rag_examples}

## 📝 YOUR TASK:

Generate a detailed animation script for: **"{topic}"**

Return ONLY valid JSON. No markdown fences, no explanation.
'''


@dataclass
class AnimationScript:
    """Structured output from Prompt Maker."""
    topic: str
    total_duration: float
    sections: List[Dict]
    raw_json: Dict
    
    @classmethod
    def from_json(cls, data: Dict) -> 'AnimationScript':
        """Create AnimationScript from parsed JSON."""
        return cls(
            topic=data.get("topic", "Unknown"),
            total_duration=data.get("total_duration_estimate", 60),
            sections=data.get("sections", []),
            raw_json=data
        )
    
    def get_section(self, section_id: int) -> Optional[Dict]:
        """Get a specific section by ID."""
        for s in self.sections:
            if s.get("id") == section_id:
                return s
        return None


class PromptMaker:
    """
    LLM Step 1: Generates refined animation prompts from topic + RAG.
    
    This is the CREATIVE stage - focuses on pedagogy and visual planning.
    The output is a structured AnimationScript that the code generator uses.
    """
    
    def __init__(self):
        """Initialize Prompt Maker with Groq LLM."""
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
            temperature=0.5  # Slightly creative for better scripts
        )
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        print(f"   📝 Prompt Maker initialized (Groq {GROQ_MODEL})")
    
    def generate_prompt(self, topic: str, rag_context: str = "", max_retries: int = 3) -> Optional[AnimationScript]:
        """
        Generate structured animation script from topic + RAG examples.
        
        Args:
            topic: User's requested topic
            rag_context: RAG-retrieved Manim code examples
            max_retries: Number of retry attempts
            
        Returns:
            AnimationScript object with structured sections
        """
        print(f"   📝 Prompt Maker creating script for: '{topic}'")
        
        if rag_context:
            print(f"   📚 Using {len(rag_context):,} chars of RAG context")
        
        # Build the prompt
        full_prompt = PROMPT_MAKER_SYSTEM.format(
            topic=topic,
            rag_examples=rag_context[:8000] if rag_context else "No examples available - use standard Manim patterns."
        )
        
        # Try to generate with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                script_data = self._call_llm(full_prompt)
                if script_data and script_data.get("sections"):
                    # Save the raw output for debugging
                    self._save_prompt_output(topic, script_data)
                    
                    script = AnimationScript.from_json(script_data)
                    print(f"   ✅ Script generated: {len(script.sections)} sections, ~{script.total_duration}s")
                    return script
            except Exception as e:
                last_error = str(e)
                print(f"   ⚠️ Attempt {attempt + 1}/{max_retries} failed: {last_error[:60]}...")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        # Fallback script
        print(f"   ⚠️ Using fallback script after {max_retries} attempts")
        return self._fallback_script(topic)
    
    def _call_llm(self, prompt: str) -> Dict:
        """Call LLM and parse JSON response."""
        response = self.groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=4000,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean markdown fences
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # Parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to fix common issues
            content = self._fix_json(content)
            return json.loads(content)
    
    def _fix_json(self, content: str) -> str:
        """Fix common JSON issues."""
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        return content
    
    def _save_prompt_output(self, topic: str, script_data: Dict):
        """Save the prompt maker output to a file for debugging."""
        # Create output directory
        output_dir = os.path.join(SCRIPT_DIR, "prompt_outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create safe filename
        safe_topic = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')[:30]
        timestamp = int(time.time())
        filename = f"prompt_output_{safe_topic}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save with pretty formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Prompt output saved: {filepath}")
    
    def _fallback_script(self, topic: str) -> AnimationScript:
        """Generate fallback script when LLM fails."""
        clean_topic = topic[:30].replace('"', "'")
        
        fallback = {
            "topic": topic,
            "total_duration_estimate": 180,
            "sections": [
                {
                    "id": 1,
                    "type": "hook",
                    "title": "Introduction",
                    "narration": f"Welcome to this educational video! Today we're going to explore {clean_topic} in detail. This is a fundamental concept that you'll use throughout your math journey. By the end of this video, you'll have a solid understanding of what {clean_topic} means and how to apply it. Let's dive in and discover why this topic is so important!",
                    "duration_estimate": 25,
                    "visual_mode": "2D",
                    "blackboard_notes": ["Introduction", "Key Concept"],
                    "animation_plan": {
                        "main_elements": ["Title text in YELLOW"],
                        "animations": ["Write(title) over 1.5s"],
                        "layout": "Title at TOP center",
                        "color_scheme": {"title": "YELLOW"}
                    }
                },
                {
                    "id": 2,
                    "type": "formula",
                    "title": "The Core Formula",
                    "narration": f"Here's the key formula for {clean_topic}. Take a moment to look at it carefully. Notice how each part of this formula serves a specific purpose. Understanding this formula is crucial because it forms the foundation for everything else we'll learn. Let me break down what each symbol represents.",
                    "duration_estimate": 30,
                    "visual_mode": "2D",
                    "blackboard_notes": ["Main Formula", "Key Variables"],
                    "animation_plan": {
                        "main_elements": ["Main formula with MathTex"],
                        "animations": ["Write(formula) over 1.5s"],
                        "layout": "Formula at CENTER",
                        "color_scheme": {"formula": "WHITE"}
                    }
                },
                {
                    "id": 3,
                    "type": "breakdown",
                    "title": "Breaking It Down",
                    "narration": f"Now let's understand each part of {clean_topic} step by step. First, we have the left side of the equation which represents one aspect of the concept. Then we have the right side which shows the result. Notice how these parts are connected - when one changes, the other must change too. This relationship is what makes this concept so powerful.",
                    "duration_estimate": 35,
                    "visual_mode": "2D",
                    "blackboard_notes": ["Part 1", "Part 2", "Connection"],
                    "animation_plan": {
                        "main_elements": ["Component labels"],
                        "animations": ["Write each component"],
                        "layout": "Components arranged vertically",
                        "color_scheme": {"components": "BLUE"}
                    }
                },
                {
                    "id": 4,
                    "type": "example",
                    "title": "Worked Example",
                    "narration": f"Let's work through a concrete example of {clean_topic}. Suppose we have specific values to work with. First, we identify what we know and what we need to find. Then we apply our formula step by step. Watch carefully as I substitute the values and simplify. And there's our answer! Notice how the formula gave us exactly what we needed.",
                    "duration_estimate": 40,
                    "visual_mode": "2D",
                    "blackboard_notes": ["Given", "Find", "Solution"],
                    "animation_plan": {
                        "main_elements": ["Example problem", "Solution steps"],
                        "animations": ["Transform through steps"],
                        "layout": "Problem at TOP, solution below",
                        "color_scheme": {"answer": "GREEN"}
                    }
                },
                {
                    "id": 5,
                    "type": "visualization",
                    "title": "Visual Understanding",
                    "narration": f"Now let's visualize {clean_topic} to build intuition. Sometimes seeing a concept visually helps it click in your mind. Watch how the different parts relate to each other in this visual representation. This geometric interpretation shows why the formula works the way it does. Keep this image in mind whenever you work with this concept.",
                    "duration_estimate": 30,
                    "visual_mode": "2D",
                    "blackboard_notes": ["Visual Proof", "Intuition"],
                    "animation_plan": {
                        "main_elements": ["Graph or shape visualization"],
                        "animations": ["Create visual"],
                        "layout": "Centered visualization",
                        "color_scheme": {"visual": "TEAL"}
                    }
                },
                {
                    "id": 6,
                    "type": "summary",
                    "title": "Key Takeaways",
                    "narration": f"Let's summarize what we learned about {clean_topic}. First, we discovered the main formula and what each part means. Then we worked through an example showing how to apply it. Finally, we visualized the concept to deepen our understanding. Remember these key points and practice with more examples. Great job learning this important concept!",
                    "duration_estimate": 30,
                    "visual_mode": "2D",
                    "blackboard_notes": ["Formula", "Steps", "Practice"],
                    "animation_plan": {
                        "main_elements": ["Summary bullet points"],
                        "animations": ["Write summary"],
                        "layout": "Bullets at CENTER",
                        "color_scheme": {"summary": "YELLOW"}
                    }
                }
            ]
        }
        
        return AnimationScript.from_json(fallback)


# ============== CONVENIENCE FUNCTION ==============
def create_animation_script(topic: str, rag_context: str = "") -> Optional[AnimationScript]:
    """
    Convenience function for Step 1 of the pipeline.
    
    Args:
        topic: User's topic
        rag_context: RAG-retrieved examples
        
    Returns:
        AnimationScript ready for code generator
    """
    maker = PromptMaker()
    return maker.generate_prompt(topic, rag_context)


if __name__ == "__main__":
    # Test the Prompt Maker
    script = create_animation_script("Pythagorean Theorem")
    if script:
        print(f"\n✅ Generated script: {script.topic}")
        for section in script.sections:
            print(f"   Section {section['id']}: {section['title']} ({section.get('duration_estimate', '?')}s)")
