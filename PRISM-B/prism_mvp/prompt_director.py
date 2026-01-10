"""
PRISM Prompt Director - The "Director" Stage
=============================================
Uses Groq (fast) to analyze topics and create detailed Manim instructions.

ROLE: Plan the video like a film director
- Break down topic into pedagogical sections
- Create specific visual instructions for each scene
- Define the Khan Academy / 3Blue1Brown aesthetic requirements
- Output structured JSON for the Cinematographer (Gemini)

ARCHITECTURE:
User Prompt → Director (Groq) → Detailed Production Plan JSON
"""

import os
import json
import re
from typing import Dict, Optional, List
from dataclasses import dataclass

from langchain_groq import ChatGroq


# ============== CONFIGURATION ==============
GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.3-70b-versatile"


# ============== DIRECTOR MEGA-PROMPT ==============
DIRECTOR_PROMPT = '''You are a **Senior Educational Video Director** specializing in Khan Academy and 3Blue1Brown style mathematics animations.

Your job: Take a topic and create a DETAILED PRODUCTION PLAN that a Manim programmer can execute perfectly.

## 🎨 SIGNATURE VISUAL STYLE

### Color Palette
- Background: Pure BLACK (#000000)
- Primary: BLUE - main shapes, titles
- Highlight: YELLOW - emphasis, important terms
- Secondary: TEAL - secondary elements, labels  
- Success: GREEN - correct answers, examples
- Warning: RED - attention, errors
- Text: WHITE - body text, formulas

### Typography Rules
- ALL mathematics: `MathTex(r"formula")` with LaTeX
- Labels/titles: `Text("text", font_size=X)`
- NEVER use `\\bullet` - use `Text("•")` instead
- Font sizes: Title=48, Section=40, Body=32, Small=24

### Layout (Split-Screen)
```
┌─────────────────────────────────────────────────────┐
│                 TITLE (YELLOW, TOP)                 │
├────────────────┬────────────────────────────────────┤
│                │                                    │
│   BLACKBOARD   │      MAIN ANIMATION AREA           │
│   (LEFT 30%)   │      (RIGHT 70%)                   │
│                │                                    │
│   • Key points │      Shapes, graphs, equations     │
│   • Formulas   │      Step-by-step animations       │
│   • Notes      │                                    │
│                │                                    │
└────────────────┴────────────────────────────────────┘
```

## ⚠️ CRITICAL BLACKBOARD RULES
The "blackboard_text" field must follow these rules EXACTLY:
1. Maximum 25 characters per line
2. Maximum 3 lines total (use | as separator, NOT \\n)
3. NO special Unicode symbols (no ², ³, √, ±, ≤, ≥)
4. Use simple ASCII: x^2 not x², sqrt() not √
5. Keep it SHORT - just key terms, not explanations

GOOD blackboard_text examples:
- "Quadratic Formula"
- "a=1 | b=5 | c=6"
- "x = -2, -3"
- "Discriminant > 0"

BAD blackboard_text (TOO LONG/COMPLEX):
- "a = coefficient of x squared which multiplies..."
- "The discriminant b²-4ac determines..."

## 🎬 PEDAGOGICAL STRUCTURE (Follow This Exactly)

### Section 1: HOOK (8-12 seconds)
- Start with intriguing question or surprising fact
- Connect to real-world application
- Create curiosity

### Section 2: FORMULA (10-15 seconds)  
- Present the main formula prominently
- Highlight each variable/term
- Color-code components

### Section 3: BREAKDOWN (15-20 seconds)
- Explain each part of the formula
- Use visual annotations
- Build understanding piece by piece

### Section 4: EXAMPLE (15-20 seconds)
- Concrete worked problem
- Show substitution step-by-step
- Highlight the final answer in GREEN

### Section 5: VISUALIZATION (10-15 seconds)
- Graph, diagram, or geometric proof
- Make abstract concept tangible
- Use animation to show relationships

### Section 6: SUMMARY (8-12 seconds)
- 2-3 bullet points of key takeaways
- Final formula display
- Memorable closing

## 🎯 YOUR TASK

Topic: "{topic}"

Create a detailed production plan. Return ONLY valid JSON (no markdown):

{{
  "topic": "{topic}",
  "total_duration": 75,
  "sections": [
    {{
      "id": 1,
      "type": "hook",
      "title": "The Big Question",
      "duration": 10,
      "narration": "What if I told you one simple equation could predict the path of every thrown ball? Let's discover the quadratic formula.",
      "visual_mode": "2D",
      "blackboard_text": "Quadratic Formula",
      "manim_instructions": [
        "Create title Text('The Quadratic Formula', font_size=48, color=YELLOW) at TOP edge",
        "Animate title with Write() over 1.5 seconds",
        "Create parabola using ParametricFunction at RIGHT side, color BLUE",
        "Animate parabola with Create() over 2 seconds",
        "Add small ball Dot following parabola path",
        "Wait remaining time for narration"
      ]
    }},
    {{
      "id": 2,
      "type": "formula",
      "title": "The Formula",
      "duration": 12,
      "narration": "Here it is. X equals negative b, plus or minus the square root of b squared minus 4 a c, all divided by 2 a.",
      "visual_mode": "2D",
      "blackboard_text": "Main Formula",
      "manim_instructions": [
        "Clear previous with FadeOut",
        "Create section title Text('The Formula', font_size=40, color=BLUE) at TOP",
        "Create main formula MathTex(r'x = \\\\frac{{-b \\\\pm \\\\sqrt{{b^2 - 4ac}}}}{{2a}}', font_size=56) at CENTER-RIGHT",
        "Animate formula with Write() over 3 seconds",
        "Highlight 'b' terms with Indicate() in YELLOW",
        "Highlight 'a' terms with Indicate() in BLUE",
        "Highlight 'c' term with Indicate() in TEAL"
      ]
    }},
    {{
      "id": 3,
      "type": "breakdown",
      "title": "Understanding Each Part",
      "duration": 18,
      "narration": "Let's break this down. The letter a is the coefficient of x squared. B is the coefficient of x. And c is the constant term. The discriminant, b squared minus 4 a c, tells us how many solutions exist.",
      "visual_mode": "2D",
      "blackboard_text": "a, b, c values",
      "manim_instructions": [
        "Keep formula visible, shift to upper area",
        "Create standard form MathTex(r'ax^2 + bx + c = 0') below main formula",
        "Draw arrows from 'a', 'b', 'c' to their positions in standard form",
        "Color code: a=BLUE, b=YELLOW, c=TEAL",
        "Highlight discriminant part with surrounding Rectangle in YELLOW",
        "Animate each label with Write()"
      ]
    }},
    {{
      "id": 4,
      "type": "example",
      "title": "Worked Example",
      "duration": 18,
      "narration": "Let's solve x squared plus 5x plus 6 equals 0. Here a equals 1, b equals 5, c equals 6. Plugging in, we get negative 5 plus or minus square root of 25 minus 24, over 2. That's negative 5 plus or minus 1, over 2. So x equals negative 2 or negative 3!",
      "visual_mode": "2D",
      "blackboard_text": "a=1 | b=5 | c=6",
      "manim_instructions": [
        "Clear and show problem MathTex(r'x^2 + 5x + 6 = 0') at TOP",
        "Show substitution step: MathTex(r'x = \\\\frac{{-5 \\\\pm \\\\sqrt{{25-24}}}}{{2}}')",
        "Transform to: MathTex(r'x = \\\\frac{{-5 \\\\pm 1}}{{2}}')",
        "Split into two solutions side by side",
        "Show x = -2 on LEFT, x = -3 on RIGHT",
        "Highlight both answers with SurroundingRectangle in GREEN"
      ]
    }},
    {{
      "id": 5,
      "type": "visualization",
      "title": "See It Graphically",
      "duration": 12,
      "narration": "And look! When we graph y equals x squared plus 5x plus 6, it crosses the x-axis at exactly negative 2 and negative 3. The roots are where the parabola meets the axis!",
      "visual_mode": "2D",
      "blackboard_text": "Roots: x = -2, -3",
      "manim_instructions": [
        "Create Axes at CENTER-RIGHT area",
        "Plot parabola y = x^2 + 5x + 6 in BLUE",
        "Mark x-intercepts at x=-2 and x=-3 with Dots in GREEN",
        "Add labels '-2' and '-3' below the dots",
        "Animate the parabola being drawn with Create()"
      ]
    }},
    {{
      "id": 6,
      "type": "summary",
      "title": "Key Takeaways",
      "duration": 10,
      "narration": "Remember: the quadratic formula works for ANY quadratic equation. Just identify a, b, and c, plug them in, and solve. You've got this!",
      "visual_mode": "2D",
      "blackboard_text": "Remember!",
      "manim_instructions": [
        "Clear and create summary area at CENTER",
        "Add title Text('Key Takeaways', color=BLUE) at top",
        "List 3 bullet points with Write() animation",
        "Show mini formula at end",
        "FadeOut all"
      ]
    }}
  ]
}}

CRITICAL RULES:
1. Return ONLY valid JSON - NO markdown code fences, NO explanations
2. Each section MUST have: id, type, title, duration, narration, visual_mode, blackboard_text, manim_instructions
3. manim_instructions must be SPECIFIC with colors, positions, sizes, durations
4. narration must be natural speech (what narrator will say)
5. Total duration of all sections should be ~75-90 seconds
6. Use proper LaTeX in any MathTex references (escape backslashes: \\\\frac not \\frac)

Generate the production plan for "{topic}" now:'''


class PromptDirector:
    """
    The Director: Analyzes topics and creates detailed video production plans.
    
    Uses Groq for fast inference (~1-2 seconds) to plan video structure.
    Output is consumed by ManimEngine (Gemini) to generate actual code.
    """
    
    def __init__(self):
        """Initialize Groq client."""
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
            temperature=0.7,
            max_tokens=6000
        )
        print("   🎬 Director initialized (Groq)")
    
    def create_production_plan(self, topic: str, rag_context: str = "") -> Dict:
        """
        Analyze topic and create detailed production plan.
        
        Args:
            topic: User's topic or prompt
            rag_context: Optional RAG context for reference
            
        Returns:
            Structured production plan as dictionary
        """
        print(f"   🎬 Director planning video for: '{topic}'")
        
        try:
            # Build prompt with RAG context if available
            prompt = DIRECTOR_PROMPT.format(topic=topic)
            
            if rag_context:
                prompt += f"\n\nREFERENCE CODE EXAMPLES (use for syntax guidance):\n{rag_context[:2000]}"
            
            # Call Groq
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Extract JSON from response
            plan = self._extract_json(content)
            
            if plan and "sections" in plan:
                sections = plan.get("sections", [])
                total_duration = sum(s.get("duration", 10) for s in sections)
                print(f"   ✅ Plan created: {len(sections)} sections, ~{total_duration}s total")
                return plan
            else:
                print("   ⚠️ Could not parse plan, using fallback")
                return self._fallback_plan(topic)
                
        except Exception as e:
            print(f"   ⚠️ Director error: {e}")
            return self._fallback_plan(topic)
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from LLM response."""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in markdown code blocks
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*"sections"[\s\S]*\}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1) if '```' in pattern else match.group(0)
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _fallback_plan(self, topic: str) -> Dict:
        """Generate fallback production plan when LLM fails."""
        return {
            "topic": topic,
            "total_duration": 75,
            "sections": [
                {
                    "id": 1,
                    "type": "hook",
                    "title": "Introduction",
                    "duration": 12,
                    "narration": f"Have you ever wondered about {topic}? Today, we'll explore this fascinating concept step by step and see why it matters.",
                    "visual_mode": "2D",
                    "blackboard_text": topic,
                    "manim_instructions": [
                        f"Create title Text('{topic}', font_size=48, color=YELLOW) at UP edge",
                        "Animate title with Write() over 2 seconds",
                        "Create decorative underline Line below title in BLUE",
                        "Wait for narration to complete"
                    ]
                },
                {
                    "id": 2,
                    "type": "formula",
                    "title": "The Core Formula",
                    "duration": 15,
                    "narration": f"Here is the key formula for {topic}. Pay attention to each component as we highlight them.",
                    "visual_mode": "2D",
                    "blackboard_text": f"Key Formula for {topic}",
                    "manim_instructions": [
                        "Clear previous content with FadeOut",
                        "Create section title at TOP",
                        "Display main formula using MathTex at CENTER",
                        "Animate with Write() over 2 seconds",
                        "Highlight key terms with Indicate() in YELLOW"
                    ]
                },
                {
                    "id": 3,
                    "type": "breakdown",
                    "title": "Breaking It Down",
                    "duration": 18,
                    "narration": f"Let's understand each part of {topic}. We'll go through it component by component to build a complete picture.",
                    "visual_mode": "2D",
                    "blackboard_text": "Components:\\n• Part 1\\n• Part 2\\n• Part 3",
                    "manim_instructions": [
                        "Keep formula visible, move to upper portion",
                        "Create explanation labels with arrows",
                        "Color code different parts: BLUE, YELLOW, TEAL",
                        "Animate each explanation with Write()",
                        "Build blackboard notes on LEFT side"
                    ]
                },
                {
                    "id": 4,
                    "type": "example",
                    "title": "Worked Example",
                    "duration": 18,
                    "narration": f"Now let's apply {topic} to a real example. Follow along as we work through each step of the calculation.",
                    "visual_mode": "2D",
                    "blackboard_text": "Example:\\nStep 1: ...\\nStep 2: ...\\nAnswer: ...",
                    "manim_instructions": [
                        "Clear and show problem statement at TOP",
                        "Show Step 1 with MathTex, animate with Write()",
                        "Transform to Step 2 showing simplification",
                        "Transform to final answer",
                        "Highlight answer with SurroundingRectangle in GREEN",
                        "Add checkmark next to answer"
                    ]
                },
                {
                    "id": 5,
                    "type": "visualization",
                    "title": "Visual Representation",
                    "duration": 12,
                    "narration": f"Let's see {topic} visually. This diagram helps us understand the concept intuitively.",
                    "visual_mode": "2D",
                    "blackboard_text": "Visual insight",
                    "manim_instructions": [
                        "Clear previous content",
                        "Create appropriate visual: graph, shape, or diagram",
                        "Animate creation with Create() or DrawBorderThenFill()",
                        "Add labels and annotations",
                        "Highlight key relationships"
                    ]
                },
                {
                    "id": 6,
                    "type": "summary",
                    "title": "Key Takeaways",
                    "duration": 10,
                    "narration": f"Let's recap what we learned about {topic}. Remember these key points and you'll master this concept!",
                    "visual_mode": "2D",
                    "blackboard_text": f"Summary:\\n• Key point 1\\n• Key point 2\\n• Key point 3",
                    "manim_instructions": [
                        "Clear and create summary box at CENTER",
                        "Add title 'Key Takeaways' in BLUE",
                        "List 3 bullet points with Write() animation",
                        "Show mini formula at bottom",
                        "Final fade out of all elements"
                    ]
                }
            ]
        }
    
    def get_sections_for_audio(self, plan: Dict) -> List[Dict]:
        """
        Extract section data formatted for audio engine.
        
        Returns list of dicts with: id, title, narration, duration, etc.
        """
        sections = []
        for section in plan.get("sections", []):
            sections.append({
                "id": section.get("id", len(sections) + 1),
                "title": section.get("title", "Section"),
                "narration": section.get("narration", ""),
                "duration": section.get("duration", 10),
                "visual_mode": section.get("visual_mode", "2D"),
                "section_type": section.get("type", "concept"),
                "blackboard_text": section.get("blackboard_text", ""),
                "manim_instructions": section.get("manim_instructions", [])
            })
        return sections


# ============== TEST ==============
if __name__ == "__main__":
    print("\n" + "="*60)
    print("   PRISM Director Test")
    print("="*60)
    
    director = PromptDirector()
    plan = director.create_production_plan("Quadratic Formula")
    
    print("\n📋 Production Plan:")
    print(json.dumps(plan, indent=2)[:2000] + "...")
    
    print("\n📝 Sections for Audio:")
    for sec in director.get_sections_for_audio(plan):
        print(f"   {sec['id']}. {sec['title']} ({sec['duration']}s)")
