"""
PRISM Data Models
=================
Core data structures for the PRISM video generation pipeline.
Defines Segment and VideoScript models for type-safe data flow.

TEMPLATE-BASED ARCHITECTURE (v2.0):
- LLM selects a template_id and provides template_data
- Templates handle all Manim complexity internally
- No more raw Manim code generation = no syntax errors

AUDIO-FIRST ARCHITECTURE:
- Director generates script with List[str] blackboard_notes
- Audio Engine measures exact durations
- Template Engine renders animations synced to audio
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any
import json


# ============== TEMPLATE IDS ==============
VALID_TEMPLATES = [
    "linear_transform",   # 3b1b-style grid transformation
    "concept_split",      # Split screen: bullets left, visual right
    "formula_reveal",     # Step-by-step formula derivation
    "graph_function",     # Animated function plotting
    "shape_morph",        # Shape transformation animations
    "custom",             # Fallback for custom code (legacy)
]


@dataclass
class Segment:
    """
    A single segment of the educational video.
    
    TEMPLATE-BASED APPROACH (v2.0):
    Instead of visual_instructions (raw Manim code), segments now specify:
    - template_id: Which proven template to use (e.g., "linear_transform")
    - template_data: Data to fill the template (e.g., {"matrix": [[2,1],[0,1]]})
    
    Each segment represents one coherent piece of the video with:
    - Narration text (what is spoken)
    - Blackboard notes as List[str] (each item = one line on blackboard)
    - Template selection and data (what should be animated)
    - Audio file and its measured duration
    
    Attributes:
        id: Unique segment identifier (1-indexed)
        title: Short title for the segment
        narration: The spoken narration text
        blackboard_notes: List of strings for blackboard display
        template_id: Template to use ("linear_transform", "concept_split", etc.)
        template_data: Dictionary of data for the template
        visual_mode: "2D" for formulas/diagrams, "3D" for spatial topics
        section_type: Type of section (hook, formula, breakdown, example, visualization, summary)
        audio_path: Path to generated audio file
        duration: Exact duration in seconds (measured from audio)
        
        Legacy fields (for backward compatibility):
        visual_instructions, text, visual_plan, on_screen_notes, visual_instruction
    """
    id: int
    title: str = ""
    narration: str = ""
    blackboard_notes: Union[List[str], str] = field(default_factory=list)
    
    # NEW: Template-based fields (v2.0)
    template_id: str = "concept_split"  # Default template
    template_data: Dict[str, Any] = field(default_factory=dict)
    
    # Legacy fields (still supported for backward compatibility)
    visual_instructions: List[str] = field(default_factory=list)
    visual_mode: str = "2D"
    section_type: str = "concept"
    audio_path: str = ""
    duration: float = 0.0
    
    # Legacy fields for backward compatibility
    text: str = ""
    visual_plan: str = ""
    on_screen_notes: str = ""
    visual_instruction: str = ""
    
    def __post_init__(self):
        """Normalize fields, validate template, and sync legacy fields."""
        # CRITICAL: Convert string blackboard_notes to list
        if isinstance(self.blackboard_notes, str):
            if self.blackboard_notes:
                # Split by common delimiters: |, \n, or comma
                if "|" in self.blackboard_notes:
                    self.blackboard_notes = [n.strip() for n in self.blackboard_notes.split("|") if n.strip()]
                elif "\n" in self.blackboard_notes:
                    self.blackboard_notes = [n.strip() for n in self.blackboard_notes.split("\n") if n.strip()]
                else:
                    self.blackboard_notes = [self.blackboard_notes.strip()]
            else:
                self.blackboard_notes = []
        
        # Ensure it's always a list
        if self.blackboard_notes is None:
            self.blackboard_notes = []
        
        # Ensure template_data is a dict
        if self.template_data is None:
            self.template_data = {}
        
        # Validate template_id
        if self.template_id and self.template_id not in VALID_TEMPLATES:
            # Try to map legacy section types to templates
            template_mapping = {
                "hook": "concept_split",
                "formula": "formula_reveal",
                "breakdown": "concept_split",
                "example": "concept_split",
                "visualization": "graph_function",
                "summary": "concept_split",
            }
            self.template_id = template_mapping.get(self.section_type, "concept_split")
        
        # Auto-populate template_data from segment fields if empty
        if not self.template_data:
            self.template_data = self._build_default_template_data()
        
        # Sync legacy fields
        if not self.text and self.narration:
            self.text = self.narration
        if not self.narration and self.text:
            self.narration = self.text
            
        if self.visual_instructions and not self.visual_instruction:
            self.visual_instruction = "\n".join(self.visual_instructions)
        if not self.visual_instructions and self.visual_instruction:
            self.visual_instructions = [self.visual_instruction]
            
        if not self.visual_plan and self.visual_instruction:
            self.visual_plan = self.visual_instruction
        if not self.visual_instruction and self.visual_plan:
            self.visual_instruction = self.visual_plan
            
        # Sync on_screen_notes with blackboard_notes (as string for legacy)
        if not self.on_screen_notes and self.blackboard_notes:
            self.on_screen_notes = " | ".join(self.blackboard_notes)
    
    def _build_default_template_data(self) -> Dict[str, Any]:
        """
        Build default template_data from segment fields.
        
        This allows legacy segments (without explicit template_data) to work
        with the new template system by auto-generating appropriate data.
        """
        data = {
            "title": self.title,
            "notes": self.get_blackboard_notes_list(),
            "duration": self.duration,
        }
        
        # Add template-specific defaults based on section_type
        if self.section_type in ["formula", "breakdown"]:
            # Formula reveal template
            data["formula_steps"] = [self.title] if self.title else ["Formula"]
            
        elif self.section_type == "visualization":
            # Graph function template
            data["function"] = "x**2"  # Default parabola
            data["x_range"] = [-4, 4, 1]
            data["y_range"] = [-2, 6, 1]
            
        else:
            # Concept split template (default)
            # Convert visual_instructions to bullet points
            bullets = self.visual_instructions[:5] if self.visual_instructions else []
            if not bullets and self.narration:
                # Extract key phrases from narration
                sentences = self.narration.split(". ")
                bullets = [s[:40] for s in sentences[:3] if s]
            data["bullet_points"] = bullets
            data["visual_type"] = "text"
        
        return data
    
    def get_blackboard_notes_list(self) -> List[str]:
        """Get blackboard notes as a guaranteed list."""
        if isinstance(self.blackboard_notes, list):
            return self.blackboard_notes
        elif isinstance(self.blackboard_notes, str) and self.blackboard_notes:
            return [n.strip() for n in self.blackboard_notes.split("|") if n.strip()]
        return []
    
    def get_template_data(self) -> Dict[str, Any]:
        """
        Get complete template data with segment context.
        
        Merges explicit template_data with segment fields for full context.
        """
        base_data = {
            "title": self.title,
            "notes": self.get_blackboard_notes_list(),
            "duration": self.duration,
            "visual_mode": self.visual_mode,
        }
        # Overlay explicit template_data
        base_data.update(self.template_data)
        return base_data
    
    def to_dict(self) -> Dict:
        """Convert segment to dictionary format."""
        return {
            "id": self.id,
            "title": self.title,
            "narration": self.narration,
            "blackboard_notes": self.blackboard_notes if isinstance(self.blackboard_notes, list) else [self.blackboard_notes],
            # Template fields (v2.0)
            "template_id": self.template_id,
            "template_data": self.template_data,
            # Other fields
            "visual_instructions": self.visual_instructions,
            "visual_mode": self.visual_mode,
            "section_type": self.section_type,
            "audio_path": self.audio_path,
            "duration": self.duration,
            # Legacy fields
            "text": self.text,
            "visual_plan": self.visual_plan,
            "on_screen_notes": self.on_screen_notes,
            "visual_instruction": self.visual_instruction
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Segment":
        """Create Segment from dictionary."""
        # Handle blackboard_notes - ensure it becomes a list
        bb_notes = data.get("blackboard_notes", data.get("on_screen_notes", []))
        if isinstance(bb_notes, str):
            bb_notes = [n.strip() for n in bb_notes.split("|") if n.strip()] if bb_notes else []
        
        return cls(
            id=data.get("id", 0),
            title=data.get("title", ""),
            narration=data.get("narration", data.get("text", "")),
            blackboard_notes=bb_notes,
            # Template fields (v2.0)
            template_id=data.get("template_id", "concept_split"),
            template_data=data.get("template_data", {}),
            # Other fields
            visual_instructions=data.get("visual_instructions", data.get("manim_instructions", [])),
            visual_mode=data.get("visual_mode", "2D"),
            section_type=data.get("section_type", data.get("type", "concept")),
            audio_path=data.get("audio_path", ""),
            duration=data.get("duration", 0.0),
            text=data.get("text", ""),
            visual_plan=data.get("visual_plan", ""),
            on_screen_notes=data.get("on_screen_notes", ""),
            visual_instruction=data.get("visual_instruction", "")
        )
    
    def __repr__(self) -> str:
        return f"Segment(id={self.id}, template='{self.template_id}', title='{self.title}', duration={self.duration:.2f}s)"


@dataclass
class VideoScript:
    """
    Complete video script containing all segments.
    
    Attributes:
        topic: The main topic of the video
        segments: List of Segment objects
        total_duration: Sum of all segment durations (from audio)
        output_dir: Directory where audio files are saved
    """
    topic: str
    segments: List[Segment] = field(default_factory=list)
    total_duration: float = 0.0
    output_dir: str = ""
    
    def add_segment(self, segment: Segment) -> None:
        """Add a segment and update total duration."""
        self.segments.append(segment)
        self.total_duration += segment.duration
    
    def get_segment(self, segment_id: int) -> Optional[Segment]:
        """Get segment by ID."""
        for seg in self.segments:
            if seg.id == segment_id:
                return seg
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            "topic": self.topic,
            "total_duration": self.total_duration,
            "segment_count": len(self.segments),
            "output_dir": self.output_dir,
            "segments": [s.to_dict() for s in self.segments]
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "VideoScript":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        script = cls(
            topic=data.get("topic", ""),
            output_dir=data.get("output_dir", "")
        )
        for seg_data in data.get("segments", []):
            segment = Segment.from_dict(seg_data)
            script.segments.append(segment)
            script.total_duration += segment.duration
        return script
    
    def get_durations_for_manim(self) -> List[Dict]:
        """
        Return segment data formatted for Manim engine.
        
        Returns:
            List of dicts with all segment data including template fields
        """
        return [
            {
                "id": s.id,
                "title": s.title,
                "narration": s.narration,
                "blackboard_notes": s.get_blackboard_notes_list(),
                # Template fields (v2.0)
                "template_id": s.template_id,
                "template_data": s.get_template_data(),
                # Legacy fields
                "visual_instructions": s.visual_instructions,
                "visual_mode": s.visual_mode,
                "section_type": s.section_type,
                "audio_path": s.audio_path,
                "duration": s.duration
            }
            for s in self.segments
        ]
    
    def get_segments_by_template(self, template_id: str) -> List[Segment]:
        """Get all segments using a specific template."""
        return [s for s in self.segments if s.template_id == template_id]
    
    def __repr__(self) -> str:
        return f"VideoScript(topic='{self.topic}', segments={len(self.segments)}, duration={self.total_duration:.2f}s)"


# ============== HELPER FUNCTIONS ==============
def create_segment(
    segment_id: int,
    narration: str,
    blackboard_notes: List[str],
    visual_instructions: List[str],
    title: str = "",
    section_type: str = "concept",
    visual_mode: str = "2D"
) -> Segment:
    """
    Factory function to create a new Segment.
    
    Args:
        segment_id: Unique ID for the segment
        narration: Narration text
        blackboard_notes: List of notes for blackboard (each = one line)
        visual_instructions: List of Manim animation instructions
        title: Optional title
        section_type: Type of section
        visual_mode: "2D" or "3D"
        
    Returns:
        New Segment instance (without audio yet)
    """
    return Segment(
        id=segment_id,
        title=title or f"Segment {segment_id}",
        narration=narration,
        blackboard_notes=blackboard_notes,
        visual_instructions=visual_instructions,
        section_type=section_type,
        visual_mode=visual_mode
    )


# ============== TESTING ==============
if __name__ == "__main__":
    # Test the data models
    print("🧪 Testing PRISM Data Models v2.0 (Template-Based)\n")
    print("=" * 60)
    
    # Test 1: Template-based segment (NEW!)
    print("\n📋 Test 1: Template-Based Segment")
    seg_template = Segment(
        id=1,
        title="Linear Transformation",
        narration="Watch how this matrix transforms the entire plane.",
        blackboard_notes=["Matrix transforms space", "Shear along x-axis"],
        template_id="linear_transform",
        template_data={
            "matrix": [[2, 1], [0, 1]],
            "vector": [1, 1],
            "show_basis": True
        },
        section_type="visualization",
        duration=8.0
    )
    print(f"  Segment: {seg_template}")
    print(f"  Template ID: {seg_template.template_id}")
    print(f"  Template Data: {seg_template.template_data}")
    print(f"  Full Template Data: {seg_template.get_template_data()}")
    
    # Test 2: Legacy segment (auto-converts to template)
    print("\n📋 Test 2: Legacy Segment (Auto-Template)")
    seg_legacy = Segment(
        id=2,
        title="Core Concept",
        narration="The theorem states that a squared plus b squared equals c squared.",
        blackboard_notes=["Formula", "Proof Method"],
        visual_instructions=["Show formula", "Animate squares"],
        section_type="formula",
        duration=7.2
    )
    print(f"  Segment: {seg_legacy}")
    print(f"  Auto-assigned Template: {seg_legacy.template_id}")
    print(f"  Auto-generated Data: {seg_legacy.template_data}")
    
    # Test 3: Concept split template
    print("\n📋 Test 3: Concept Split Screen")
    seg_split = Segment(
        id=3,
        title="Quadratic Formula",
        narration="The quadratic formula solves any quadratic equation.",
        blackboard_notes=["ax² + bx + c = 0", "Find x values"],
        template_id="concept_split",
        template_data={
            "bullet_points": ["Works for any quadratic", "Gives exact solutions", "Easy to apply"],
            "latex_formula": r"x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}",
            "visual_type": "formula"
        },
        section_type="formula",
        duration=10.0
    )
    print(f"  Segment: {seg_split}")
    print(f"  Template: {seg_split.template_id}")
    print(f"  Bullets: {seg_split.template_data.get('bullet_points')}")
    
    # Test 4: VideoScript with mixed templates
    print("\n📋 Test 4: VideoScript with Multiple Templates")
    script = VideoScript(topic="Linear Algebra Intro")
    script.add_segment(seg_template)
    script.add_segment(seg_legacy)
    script.add_segment(seg_split)
    
    print(f"  Script: {script}")
    print(f"  Segments by template:")
    for seg in script.segments:
        print(f"    - {seg.id}: {seg.template_id} ({seg.duration:.1f}s)")
    
    # Test 5: Serialization
    print("\n📋 Test 5: JSON Serialization")
    json_str = script.to_json()
    print(f"  JSON length: {len(json_str)} chars")
    print(f"  Sample:\n{json_str[:600]}...")
    
    # Test 6: Deserialization
    print("\n📋 Test 6: Deserialization")
    script2 = VideoScript.from_json(json_str)
    print(f"  Restored: {script2}")
    for seg in script2.segments:
        print(f"    - {seg}")
    
    print("\n" + "=" * 60)
    print("✅ Data Models v2.0 test complete!")
    print("   Templates available:", VALID_TEMPLATES)
