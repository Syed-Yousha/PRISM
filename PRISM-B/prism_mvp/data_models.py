"""
PRISM Data Models
=================
Core data structures for the PRISM video generation pipeline.
Defines Segment and VideoScript models for type-safe data flow.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json


@dataclass
class Segment:
    """
    A single segment of the educational video.
    
    Each segment represents one coherent piece of the video with:
    - Narration text (what is spoken)
    - Blackboard notes (text displayed on the blackboard)
    - Visual instruction (what should be animated)
    - Audio file and its measured duration
    
    Attributes:
        id: Unique segment identifier (1-indexed)
        text: The narration text to be spoken (legacy, same as narration)
        visual_plan: Description of visuals for this segment (legacy, same as visual_instruction)
        narration: The spoken narration text
        on_screen_notes: Text/formulas to display on screen (legacy, same as blackboard_notes)
        blackboard_notes: Text/formulas to display on blackboard (supports LaTeX)
        visual_instruction: Specific animation instructions for Manim
        visual_mode: "2D" for formulas/diagrams, "3D" for spatial topics
        section_type: Type of section (hook, concept, example, summary, etc.)
        audio_path: Path to generated audio file
        duration: Exact duration in seconds (measured from audio)
        title: Optional short title for the segment
    """
    id: int
    text: str
    visual_plan: str
    narration: str = ""
    on_screen_notes: str = ""
    blackboard_notes: str = ""
    visual_instruction: str = ""
    visual_mode: str = "2D"
    section_type: str = "concept"
    audio_path: str = ""
    duration: float = 0.0
    title: str = ""
    
    def __post_init__(self):
        """Ensure backward compatibility - sync legacy fields with new fields."""
        # If new fields are empty, populate from legacy fields
        if not self.narration and self.text:
            self.narration = self.text
        # If legacy fields are empty, populate from new fields
        if not self.text and self.narration:
            self.text = self.narration
        if not self.visual_plan and self.visual_instruction:
            self.visual_plan = self.visual_instruction
        if not self.visual_instruction and self.visual_plan:
            self.visual_instruction = self.visual_plan
        # Sync blackboard_notes with on_screen_notes
        if not self.blackboard_notes and self.on_screen_notes:
            self.blackboard_notes = self.on_screen_notes
        if not self.on_screen_notes and self.blackboard_notes:
            self.on_screen_notes = self.blackboard_notes
    
    def to_dict(self) -> Dict:
        """Convert segment to dictionary format."""
        return {
            "id": self.id,
            "text": self.text,
            "visual_plan": self.visual_plan,
            "narration": self.narration,
            "on_screen_notes": self.on_screen_notes,
            "blackboard_notes": self.blackboard_notes,
            "visual_instruction": self.visual_instruction,
            "visual_mode": self.visual_mode,
            "section_type": self.section_type,
            "audio_path": self.audio_path,
            "duration": self.duration,
            "title": self.title
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Segment":
        """Create Segment from dictionary."""
        return cls(
            id=data.get("id", 0),
            text=data.get("text", ""),
            visual_plan=data.get("visual_plan", ""),
            narration=data.get("narration", ""),
            on_screen_notes=data.get("on_screen_notes", ""),
            blackboard_notes=data.get("blackboard_notes", data.get("on_screen_notes", "")),
            visual_instruction=data.get("visual_instruction", ""),
            visual_mode=data.get("visual_mode", "2D"),
            section_type=data.get("section_type", "concept"),
            audio_path=data.get("audio_path", ""),
            duration=data.get("duration", 0.0),
            title=data.get("title", "")
        )
    
    def __repr__(self) -> str:
        return f"Segment(id={self.id}, title='{self.title}', duration={self.duration:.2f}s)"


@dataclass
class VideoScript:
    """
    Complete video script containing all segments.
    
    Attributes:
        topic: The main topic of the video
        segments: List of Segment objects
        total_duration: Sum of all segment durations
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
            List of dicts with all segment data including visual_mode and section_type
        """
        return [
            {
                "id": s.id,
                "title": s.title,
                "text": s.text,
                "visual_plan": s.visual_plan,
                "narration": s.narration,
                "on_screen_notes": s.on_screen_notes,
                "blackboard_notes": s.blackboard_notes,
                "visual_instruction": s.visual_instruction,
                "visual_mode": s.visual_mode,
                "section_type": s.section_type,
                "audio_path": s.audio_path,
                "duration": s.duration
            }
            for s in self.segments
        ]
    
    def __repr__(self) -> str:
        return f"VideoScript(topic='{self.topic}', segments={len(self.segments)}, duration={self.total_duration:.2f}s)"


# ============== HELPER FUNCTIONS ==============
def create_segment(
    segment_id: int,
    text: str,
    visual_plan: str,
    title: str = ""
) -> Segment:
    """
    Factory function to create a new Segment.
    
    Args:
        segment_id: Unique ID for the segment
        text: Narration text
        visual_plan: Visual description for animation
        title: Optional title
        
    Returns:
        New Segment instance (without audio yet)
    """
    return Segment(
        id=segment_id,
        text=text,
        visual_plan=visual_plan,
        title=title or f"Segment {segment_id}"
    )


# ============== TESTING ==============
if __name__ == "__main__":
    # Test the data models
    print("🧪 Testing PRISM Data Models\n")
    
    # Create segments
    seg1 = Segment(
        id=1,
        title="Introduction",
        text="Welcome to our exploration of the Pythagorean theorem.",
        visual_plan="3D axes fade in, camera rotates slowly",
        duration=5.5
    )
    
    seg2 = Segment(
        id=2,
        title="Core Concept",
        text="The theorem states that a squared plus b squared equals c squared.",
        visual_plan="Triangle appears with labeled sides, squares grow from each side",
        duration=7.2
    )
    
    # Create video script
    script = VideoScript(topic="Pythagorean Theorem")
    script.add_segment(seg1)
    script.add_segment(seg2)
    
    print(f"Created: {script}")
    print(f"\nSegments:")
    for seg in script.segments:
        print(f"  {seg}")
    
    print(f"\nJSON output:")
    print(script.to_json())
    
    print(f"\nDurations for Manim:")
    for d in script.get_durations_for_manim():
        print(f"  Segment {d['id']}: {d['duration']:.2f}s - {d['title']}")
