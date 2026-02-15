"""
PRISM Prompt Maker - Animation Script Generator
================================================
API CALL 1 of 2: Topic → Structured 3-section animation script.

Uses Groq LLM to generate a JSON animation script with exactly 3 sections:
  1. Introduction      - Hook + concept definition (30-45s)
  2. Concept Explanation - Visual diagrams + formula breakdown (45-70s)  
  3. Worked Examples    - Solved example + practice questions with answers (50-80s)

Input:  Topic string + RAG context
Output: VideoScript with 3 Segments (narration, visual instructions, blackboard notes)
"""

import json
import re
import time
from dataclasses import dataclass
from typing import Optional

from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL
from data_models import Segment, VideoScript

# ============== SYSTEM PROMPT ==============
PROMPT_MAKER_SYSTEM = """You are PRISM, an expert educational animation script writer.
You create EXACTLY 3-section video scripts for math concepts (Manim Community Edition).

OUTPUT FORMAT: Valid JSON object (no markdown, no ```json blocks).

STRUCTURE (exactly 3 sections):
{
  "topic": "<topic name>",
  "sections": [
    {
      "id": 1,
      "title": "Introduction",
      "section_type": "introduction",
      "narration": "30-45 second narration (80-120 words). Hook the viewer, state the topic, show the main formula/definition.",
      "blackboard_notes": ["Formula 1", "Key Definition"],
      "visual_instructions": [
        "Show title text with topic name",
        "Display the main formula with MathTex",
        "Highlight key terms"
      ],
      "visual_mode": "2D"
    },
    {
      "id": 2,
      "title": "Concept Explanation",
      "section_type": "concept",
      "narration": "45-70 second narration (120-180 words). Break down the concept with visual diagrams. Explain each part of the formula step-by-step.",
      "blackboard_notes": ["Step 1: ...", "Step 2: ...", "Key insight"],
      "visual_instructions": [
        "Draw a labeled diagram showing the concept",
        "Animate formula transformation step by step",
        "Use color coding to highlight relationships"
      ],
      "visual_mode": "2D"
    },
    {
      "id": 3,
      "title": "Worked Examples & Practice",
      "section_type": "examples",
      "narration": "50-80 second narration (130-200 words). Solve one example step-by-step. Then present 2-3 practice questions WITH their answers.",
      "blackboard_notes": ["Example: ...", "Step 1: ...", "Answer: ...", "Practice Q1: ... Answer: ...", "Practice Q2: ... Answer: ..."],
      "visual_instructions": [
        "Show the example problem",
        "Animate the solution steps one by one",
        "Display practice questions with answers revealed"
      ],
      "visual_mode": "2D"
    }
  ]
}

RULES:
- EXACTLY 3 sections, no more, no less.
- Section 3 MUST include at least 2 practice questions WITH answers in blackboard_notes.
- Use "2D" visual_mode unless the topic genuinely requires 3D (vectors, 3D geometry).
- Narration should be natural, conversational, educational (like 3Blue1Brown).
- blackboard_notes: short formulas/text shown on screen (LaTeX-friendly).
- visual_instructions: what Manim should animate (be specific about shapes, positions, colors).
- Output ONLY the JSON object. No explanation, no markdown."""


class PromptMaker:
    """
    Generates structured 3-section animation scripts via Groq LLM.
    This is API CALL 1 of 2 in the PRISM pipeline.
    """
    
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set. Add it to your .env file.")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = GROQ_MODEL
    
    def generate_script(self, topic: str, rag_context: str = "") -> VideoScript:
        """
        Generate a 3-section animation script for the given topic.
        
        Args:
            topic: Educational topic (e.g., "Pythagorean Theorem")
            rag_context: RAG context with Manim examples and reference
            
        Returns:
            VideoScript with 3 Segments
        """
        print(f"\n   📝 Generating animation script for: {topic}")
        start = time.time()
        
        user_prompt = f"""Create a 3-section educational animation script for: "{topic}"

RAG CONTEXT (use these Manim patterns):
{rag_context[:8000] if rag_context else "No RAG context available. Use standard Manim CE patterns."}

Remember: Output ONLY valid JSON. Exactly 3 sections. Include practice questions with answers in section 3."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PROMPT_MAKER_SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=3000,
            )
            
            raw = response.choices[0].message.content.strip()
            elapsed = time.time() - start
            print(f"   📝 Script generated in {elapsed:.1f}s")
            
            # Parse JSON from response
            script_data = self._parse_json(raw)
            
            if script_data and "sections" in script_data:
                return self._build_video_script(topic, script_data)
            else:
                print("   ⚠️ Invalid script format, using fallback")
                return self._fallback_script(topic)
                
        except Exception as e:
            print(f"   ❌ Script generation failed: {e}")
            return self._fallback_script(topic)
    
    def _parse_json(self, raw: str) -> Optional[dict]:
        """Extract and parse JSON from LLM response."""
        # Try direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        
        # Strip markdown code blocks
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', raw, flags=re.MULTILINE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object in text
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        print(f"   ⚠️ Could not parse JSON from response ({len(raw)} chars)")
        return None
    
    def _build_video_script(self, topic: str, data: dict) -> VideoScript:
        """Build VideoScript from parsed JSON data."""
        script = VideoScript(topic=topic)
        
        sections = data.get("sections", [])
        if len(sections) != 3:
            print(f"   ⚠️ Expected 3 sections, got {len(sections)}. Adjusting...")
            # Pad or trim to exactly 3
            while len(sections) < 3:
                sections.append({
                    "id": len(sections) + 1,
                    "title": ["Introduction", "Concept Explanation", "Worked Examples & Practice"][len(sections)],
                    "section_type": ["introduction", "concept", "examples"][len(sections)],
                    "narration": f"Section {len(sections) + 1} about {topic}.",
                    "blackboard_notes": [],
                    "visual_instructions": [],
                    "visual_mode": "2D",
                })
            sections = sections[:3]
        
        for i, sec in enumerate(sections):
            segment = Segment(
                id=i + 1,
                title=sec.get("title", f"Section {i+1}"),
                narration=sec.get("narration", ""),
                blackboard_notes=sec.get("blackboard_notes", []),
                visual_instructions=sec.get("visual_instructions", []),
                visual_mode=sec.get("visual_mode", "2D"),
                section_type=sec.get("section_type", ["introduction", "concept", "examples"][i]),
            )
            script.add_segment(segment)
        
        print(f"   ✅ Script: {len(script.segments)} sections")
        for seg in script.segments:
            words = len(seg.narration.split())
            print(f"      Section {seg.id}: {seg.title} ({words} words, {seg.visual_mode})")
        
        return script
    
    def _fallback_script(self, topic: str) -> VideoScript:
        """Generate a safe fallback script if LLM fails."""
        print(f"   🔄 Using fallback script for: {topic}")
        script = VideoScript(topic=topic)
        
        fallback_sections = [
            Segment(
                id=1,
                title="Introduction",
                section_type="introduction",
                narration=f"Welcome! Today we're going to explore {topic}. "
                          f"This is a fundamental concept in mathematics that you'll find incredibly useful. "
                          f"Let's start by understanding what {topic} is all about and see its key formula.",
                blackboard_notes=[topic, "Key formula"],
                visual_instructions=[
                    f"Display title: {topic}",
                    "Show the main formula with MathTex",
                    "Fade in a simple diagram",
                ],
                visual_mode="2D",
            ),
            Segment(
                id=2,
                title="Concept Explanation",
                section_type="concept",
                narration=f"Now let's break down {topic} step by step. "
                          f"The key idea here is understanding how each part of the formula works together. "
                          f"Watch as we build up the concept visually, piece by piece. "
                          f"Notice how each element connects to the others.",
                blackboard_notes=["Step 1: Identify", "Step 2: Apply", "Step 3: Solve"],
                visual_instructions=[
                    "Draw a labeled diagram",
                    "Animate formula breakdown step by step",
                    "Use color coding for different parts",
                ],
                visual_mode="2D",
            ),
            Segment(
                id=3,
                title="Worked Examples & Practice",
                section_type="examples",
                narration=f"Let's work through an example of {topic}. "
                          f"Follow along as we solve this step by step. "
                          f"And here are some practice questions for you to try, with answers provided.",
                blackboard_notes=[
                    f"Example: Solve using {topic}",
                    "Step 1: Set up", "Step 2: Calculate", "Answer: See solution",
                    "Practice Q1: Try this problem — Answer: ...",
                    "Practice Q2: Another problem — Answer: ...",
                ],
                visual_instructions=[
                    "Show the example problem",
                    "Animate solution steps",
                    "Display practice questions with answers",
                ],
                visual_mode="2D",
            ),
        ]
        
        for seg in fallback_sections:
            script.add_segment(seg)
        
        return script


# ============== CLI TESTING ==============
if __name__ == "__main__":
    print("\n🔮 PRISM Prompt Maker - Test\n")
    pm = PromptMaker()
    script = pm.generate_script("Pythagorean Theorem")
    print(f"\n{script.to_json()}")
