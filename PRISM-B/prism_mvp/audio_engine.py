"""
PRISM Audio Engine - The "Director" Stage
==========================================
Generates the complete script AND audio in one step.

AUDIO-FIRST ARCHITECTURE:
1. LLM generates script with List[str] blackboard_notes (NOT pipe-separated!)
2. Parallel TTS generation using ThreadPoolExecutor
3. EXACT duration measurement using mutagen
4. Returns VideoScript with real durations for Manim sync

This is the DIRECTOR - it creates the master timeline that
the Cinematographer (Manim Engine) MUST follow.
"""

import os
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

from gtts import gTTS
from mutagen.mp3 import MP3
from langchain_groq import ChatGroq

from data_models import Segment, VideoScript
from config import SCRIPT_DIR, GROQ_API_KEY, GROQ_MODEL, MAX_WORKERS, AUDIO_BUFFER

# ============== DIRECTOR PROMPT ==============
DIRECTOR_SCRIPT_PROMPT = '''You are a **Senior Educational Video Director** creating Khan Academy / 3Blue1Brown style math videos.

Create a DETAILED SCRIPT for this topic: "{topic}"

## ⚠️ CRITICAL FORMAT RULES

### blackboard_notes MUST be a List of Strings, NOT a pipe-separated string!
**CORRECT:**
```json
"blackboard_notes": ["Formula", "a = 1", "b = 5"]
```

**WRONG (will break the system):**
```json
"blackboard_notes": "Formula | a = 1 | b = 5"
```

### Each note should be:
- Maximum 20 characters
- Simple ASCII only (no ², √, ±)
- One concept per note

## 🎬 REQUIRED STRUCTURE (6 Sections)

Return ONLY valid JSON (no markdown, no explanation):

{{
  "topic": "{topic}",
  "sections": [
    {{
      "id": 1,
      "type": "hook",
      "title": "The Big Question",
      "narration": "What if I told you one simple equation could predict the path of every thrown ball? Let's discover it.",
      "visual_mode": "2D",
      "blackboard_notes": ["Big Idea", "Real World"],
      "manim_instructions": [
        "Create title Text at TOP in YELLOW",
        "Show an intriguing visual related to topic",
        "Animate with Write() over 1.5 seconds"
      ]
    }},
    {{
      "id": 2,
      "type": "formula",
      "title": "The Formula",
      "narration": "Here's the core formula we'll be working with today.",
      "visual_mode": "2D",
      "blackboard_notes": ["Main Formula"],
      "manim_instructions": [
        "Display main formula using MathTex at CENTER",
        "Highlight key variables with Indicate()",
        "Use YELLOW for emphasis"
      ]
    }},
    {{
      "id": 3,
      "type": "breakdown",
      "title": "Understanding Each Part",
      "narration": "Let's break this down piece by piece to understand each component.",
      "visual_mode": "2D",
      "blackboard_notes": ["Part A", "Part B", "Part C"],
      "manim_instructions": [
        "Show each component separately",
        "Color code: a=BLUE, b=YELLOW, c=TEAL",
        "Draw arrows connecting related parts"
      ]
    }},
    {{
      "id": 4,
      "type": "example",
      "title": "Worked Example",
      "narration": "Let's work through a concrete example step by step.",
      "visual_mode": "2D",
      "blackboard_notes": ["Step 1", "Step 2", "Answer"],
      "manim_instructions": [
        "Show problem at TOP",
        "Transform through each step",
        "Highlight final answer in GREEN box"
      ]
    }},
    {{
      "id": 5,
      "type": "visualization",
      "title": "See It Visually",
      "narration": "Now let's visualize this concept to really understand it.",
      "visual_mode": "2D",
      "blackboard_notes": ["Visual Key"],
      "manim_instructions": [
        "Create graph or geometric visualization",
        "Animate the relationship",
        "Show how formula connects to visual"
      ]
    }},
    {{
      "id": 6,
      "type": "summary",
      "title": "Key Takeaways",
      "narration": "Let's summarize what we learned today about this important concept.",
      "visual_mode": "2D",
      "blackboard_notes": ["Remember", "Practice"],
      "manim_instructions": [
        "Show 2-3 bullet points",
        "Display final formula",
        "End with checkmark animation"
      ]
    }}
  ]
}}

Generate the script for: "{topic}"
'''


class AudioEngine:
    """
    The Director: Generates script AND audio with precise durations.
    
    This is the MASTER timeline. The Manim engine MUST follow these durations.
    """
    
    def __init__(self, max_workers: int = MAX_WORKERS):
        """Initialize the Director (Audio Engine)."""
        self.max_workers = max_workers
        self.output_dir = None
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
            temperature=0.4
        )
        print(f"   🎬 Director initialized (Groq + {max_workers} TTS workers)")
    
    def generate_script_and_audio(self, topic: str, max_retries: int = 3) -> Optional[VideoScript]:
        """
        Main entry point: Generate complete script with audio.
        
        Args:
            topic: Educational topic to create video about
            max_retries: Number of retry attempts on LLM errors
            
        Returns:
            VideoScript with segments containing real audio durations
        """
        print(f"   🎬 Director creating script for: '{topic}'")
        
        # Step 1: Generate script from LLM (with retry logic)
        plan = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                plan = self._generate_script(topic)
                if plan and plan.get("sections"):
                    print(f"   ✅ Script generated: {len(plan['sections'])} sections")
                    break
            except Exception as e:
                last_error = str(e)
                print(f"   ⚠️ Script generation failed (attempt {attempt + 1}/{max_retries}): {last_error[:60]}...")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
        
        if not plan or not plan.get("sections"):
            print(f"   ❌ Failed to generate script after {max_retries} attempts")
            # Return fallback script
            plan = self._fallback_script(topic)
        
        # Step 2: Create output directory
        output_dir = self._ensure_output_dir(topic)
        
        # Step 3: Convert plan to Segment objects
        segments = self._plan_to_segments(plan)
        
        # Step 4: Generate audio in parallel with retry
        segments = self._generate_audio_parallel(segments, output_dir)
        
        # Step 5: Build VideoScript
        video_script = VideoScript(topic=topic, output_dir=output_dir)
        for seg in segments:
            video_script.add_segment(seg)
        
        # Save script for debugging
        self._save_script(video_script, output_dir)
        
        print(f"   ✅ Director complete: {video_script.total_duration:.1f}s total audio")
        return video_script
    
    def _generate_script(self, topic: str) -> Dict:
        """Generate script using LLM."""
        prompt = DIRECTOR_SCRIPT_PROMPT.format(topic=topic)
        response = self.llm.invoke(prompt)
        
        # Extract JSON from response
        content = response.content.strip()
        
        # Remove markdown code fences if present
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # Parse JSON
        try:
            plan = json.loads(content)
            return plan
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues
            content = self._fix_json(content)
            return json.loads(content)
    
    def _fix_json(self, content: str) -> str:
        """Attempt to fix common JSON issues."""
        # Remove trailing commas
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        # Fix unquoted keys (rare but happens)
        content = re.sub(r'(\w+)(?=\s*:)', r'"\1"', content)
        return content
    
    def _fallback_script(self, topic: str) -> Dict:
        """Generate fallback script when LLM fails."""
        clean_topic = topic[:30].replace('"', "'")
        return {
            "topic": topic,
            "sections": [
                {
                    "id": 1,
                    "type": "hook",
                    "title": "Introduction",
                    "narration": f"Welcome to this educational video about {clean_topic}. Let's explore this fascinating topic together.",
                    "visual_mode": "2D",
                    "blackboard_notes": ["Introduction", "Key Topic"],
                    "manim_instructions": ["Show title", "Display topic overview"]
                },
                {
                    "id": 2,
                    "type": "formula",
                    "title": "Core Concept",
                    "narration": f"Here's the main concept we'll be learning about {clean_topic} today.",
                    "visual_mode": "2D",
                    "blackboard_notes": ["Core Idea"],
                    "manim_instructions": ["Display main formula or concept"]
                },
                {
                    "id": 3,
                    "type": "breakdown",
                    "title": "Understanding",
                    "narration": f"Let's break down the key components of {clean_topic}.",
                    "visual_mode": "2D",
                    "blackboard_notes": ["Part 1", "Part 2"],
                    "manim_instructions": ["Show components"]
                },
                {
                    "id": 4,
                    "type": "example",
                    "title": "Example",
                    "narration": f"Now let's work through an example to see {clean_topic} in action.",
                    "visual_mode": "2D",
                    "blackboard_notes": ["Example", "Solution"],
                    "manim_instructions": ["Show worked example"]
                },
                {
                    "id": 5,
                    "type": "visualization",
                    "title": "Visualization",
                    "narration": f"Let's visualize {clean_topic} to build intuition.",
                    "visual_mode": "2D",
                    "blackboard_notes": ["Visual"],
                    "manim_instructions": ["Create visual demonstration"]
                },
                {
                    "id": 6,
                    "type": "summary",
                    "title": "Summary",
                    "narration": f"To summarize what we learned about {clean_topic}, remember the key points we covered.",
                    "visual_mode": "2D",
                    "blackboard_notes": ["Key Points", "Practice"],
                    "manim_instructions": ["Show summary points"]
                }
            ]
        }
    
    def _plan_to_segments(self, plan: Dict) -> List[Segment]:
        """Convert plan to Segment objects."""
        segments = []
        
        for section in plan.get("sections", []):
            # Ensure blackboard_notes is a List[str]
            bb_notes = section.get("blackboard_notes", [])
            if isinstance(bb_notes, str):
                # Convert pipe-separated string to list
                bb_notes = [n.strip() for n in bb_notes.split("|") if n.strip()]
            
            seg = Segment(
                id=section.get("id", len(segments) + 1),
                title=section.get("title", f"Section {len(segments) + 1}"),
                narration=section.get("narration", ""),
                blackboard_notes=bb_notes,
                visual_instructions=section.get("manim_instructions", []),
                visual_mode=section.get("visual_mode", "2D"),
                section_type=section.get("type", "concept")
            )
            segments.append(seg)
        
        return segments
    
    def _ensure_output_dir(self, topic: str) -> str:
        """Create output directory for audio files."""
        safe_name = re.sub(r"[^\w\s-]", "", topic).replace(" ", "_")[:25]
        timestamp = int(time.time())
        audio_dir = os.path.join(SCRIPT_DIR, "media", "audio", f"{safe_name}_{timestamp}")
        os.makedirs(audio_dir, exist_ok=True)
        self.output_dir = audio_dir
        return audio_dir
    
    def _generate_audio_parallel(self, segments: List[Segment], output_dir: str) -> List[Segment]:
        """Generate audio for all segments in parallel."""
        print(f"   🎤 Generating audio for {len(segments)} sections...")
        start = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._generate_single_audio, seg, output_dir): seg.id
                for seg in segments
            }
            
            for future in as_completed(futures):
                seg_id = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"      ⚠️ Audio failed for segment {seg_id}: {e}")
        
        elapsed = time.time() - start
        print(f"      Generated {len(segments)} clips in {elapsed:.1f}s")
        
        # Sort by ID
        segments.sort(key=lambda s: s.id)
        return segments
    
    def _generate_single_audio(self, segment: Segment, output_dir: str, max_retries: int = 2) -> Segment:
        """Generate audio for a single segment with retry logic."""
        safe_title = re.sub(r"[^\w\s-]", "", segment.title).replace(" ", "_")[:15]
        audio_path = os.path.join(output_dir, f"seg_{segment.id:02d}_{safe_title}.mp3")
        
        text = segment.narration or f"Section {segment.id}: {segment.title}"
        
        for attempt in range(max_retries + 1):
            try:
                # Generate TTS
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(audio_path)
                
                # CRUCIAL: Measure EXACT duration using mutagen
                audio = MP3(audio_path)
                segment.audio_path = audio_path
                segment.duration = round(audio.info.length + AUDIO_BUFFER, 2)
                
                return segment
                
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(1)
                else:
                    print(f"      ⚠️ TTS failed for segment {segment.id}: {e}")
                    segment.audio_path = ""
                    segment.duration = 10.0  # Default fallback duration
        
        return segment
    
    def _save_script(self, video_script: VideoScript, output_dir: str) -> None:
        """Save script for debugging."""
        script_path = os.path.join(output_dir, "script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(video_script.to_json())
    
    def generate_audio_from_script(self, topic: str, animation_script) -> Optional[VideoScript]:
        """
        Generate audio from PromptMaker's AnimationScript.
        
        This is used in the 2-step LLM pipeline where Step 1 (PromptMaker)
        already generated the animation script.
        
        Args:
            topic: Video topic
            animation_script: AnimationScript from PromptMaker (Step 1)
            
        Returns:
            VideoScript with audio durations
        """
        print(f"   🎤 Generating audio from AnimationScript...")
        
        # Create output directory
        output_dir = self._ensure_output_dir(topic)
        
        # Convert AnimationScript sections to Segments
        segments = []
        for section in animation_script.sections:
            # Extract blackboard notes
            bb_notes = section.get("blackboard_notes", [])
            if isinstance(bb_notes, str):
                bb_notes = [n.strip() for n in bb_notes.split("|") if n.strip()]
            
            # Extract visual instructions from animation_plan
            anim_plan = section.get("animation_plan", {})
            visual_instructions = []
            if anim_plan:
                visual_instructions.extend(anim_plan.get("main_elements", []))
                visual_instructions.extend(anim_plan.get("animations", []))
            
            seg = Segment(
                id=section.get("id", len(segments) + 1),
                title=section.get("title", f"Section {len(segments) + 1}"),
                narration=section.get("narration", ""),
                blackboard_notes=bb_notes,
                visual_instructions=visual_instructions,
                visual_mode=section.get("visual_mode", "2D"),
                section_type=section.get("type", "concept")
            )
            segments.append(seg)
        
        # Generate audio in parallel
        segments = self._generate_audio_parallel(segments, output_dir)
        
        # Build VideoScript
        video_script = VideoScript(topic=topic, output_dir=output_dir)
        for seg in segments:
            video_script.add_segment(seg)
        
        # Save for debugging
        self._save_script(video_script, output_dir)
        
        print(f"   ✅ Audio generation complete: {video_script.total_duration:.1f}s")
        return video_script
    
    # Legacy method for backward compatibility
    def generate_from_plan(self, plan: Dict) -> VideoScript:
        """
        Legacy method: Generate audio from existing plan.
        For backward compatibility with old code.
        """
        topic = plan.get("topic", "Educational Topic")
        sections = plan.get("sections", [])
        
        print(f"   🎤 [Legacy] Generating audio for {len(sections)} sections...")
        
        output_dir = self._ensure_output_dir(topic)
        segments = self._plan_to_segments(plan)
        segments = self._generate_audio_parallel(segments, output_dir)
        
        video_script = VideoScript(topic=topic, output_dir=output_dir)
        for seg in segments:
            video_script.add_segment(seg)
        
        self._save_script(video_script, output_dir)
        
        print(f"   ✅ Audio complete: {video_script.total_duration:.1f}s total")
        return video_script


# ============== EXPORTS ==============
__all__ = ['AudioEngine']


# ============== TESTING ==============
if __name__ == "__main__":
    print("=" * 60)
    print("🎬 PRISM Audio Engine (Director) Test")
    print("=" * 60)
    
    engine = AudioEngine()
    
    # Test with a topic
    video_script = engine.generate_script_and_audio("Pythagorean Theorem")
    
    if video_script:
        print(f"\n📝 Generated Script:")
        print(f"   Topic: {video_script.topic}")
        print(f"   Duration: {video_script.total_duration:.1f}s")
        print(f"   Segments: {len(video_script.segments)}")
        
        for seg in video_script.segments:
            print(f"\n   Section {seg.id}: {seg.title}")
            print(f"      Type: {seg.section_type}")
            print(f"      Duration: {seg.duration:.1f}s")
            print(f"      Notes: {seg.get_blackboard_notes_list()}")
            print(f"      Audio: {seg.audio_path[:50]}..." if seg.audio_path else "      Audio: None")
    
    print("\n✅ Director test complete")
