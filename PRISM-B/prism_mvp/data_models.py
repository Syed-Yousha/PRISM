"""
PRISM Data Models
=================
Lean data structures for the 2-call video generation pipeline.

3-SECTION STRUCTURE:
  1. Introduction - Hook + concept definition + main formula
  2. Concept Explanation - Visual diagrams + formula breakdown
  3. Worked Examples & Practice - Solved example + practice Qs with answers
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any
import json


@dataclass
class Segment:
    """A single section of the educational video."""
    id: int
    title: str = ""
    narration: str = ""
    blackboard_notes: Union[List[str], str] = field(default_factory=list)
    visual_instructions: List[str] = field(default_factory=list)
    visual_mode: str = "2D"
    section_type: str = "concept"
    audio_path: str = ""
    duration: float = 0.0
    
    def __post_init__(self):
        # Normalize blackboard_notes to list
        if isinstance(self.blackboard_notes, str):
            if self.blackboard_notes:
                if "|" in self.blackboard_notes:
                    self.blackboard_notes = [n.strip() for n in self.blackboard_notes.split("|") if n.strip()]
                else:
                    self.blackboard_notes = [self.blackboard_notes.strip()]
            else:
                self.blackboard_notes = []
        if self.blackboard_notes is None:
            self.blackboard_notes = []
    
    def get_blackboard_notes_list(self) -> List[str]:
        if isinstance(self.blackboard_notes, list):
            return self.blackboard_notes
        elif isinstance(self.blackboard_notes, str) and self.blackboard_notes:
            return [n.strip() for n in self.blackboard_notes.split("|") if n.strip()]
        return []
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "narration": self.narration,
            "blackboard_notes": self.blackboard_notes if isinstance(self.blackboard_notes, list) else [self.blackboard_notes],
            "visual_instructions": self.visual_instructions,
            "visual_mode": self.visual_mode,
            "section_type": self.section_type,
            "audio_path": self.audio_path,
            "duration": self.duration,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Segment":
        bb_notes = data.get("blackboard_notes", [])
        if isinstance(bb_notes, str):
            bb_notes = [n.strip() for n in bb_notes.split("|") if n.strip()] if bb_notes else []
        return cls(
            id=data.get("id", 0),
            title=data.get("title", ""),
            narration=data.get("narration", data.get("text", "")),
            blackboard_notes=bb_notes,
            visual_instructions=data.get("visual_instructions", data.get("manim_instructions", [])),
            visual_mode=data.get("visual_mode", "2D"),
            section_type=data.get("section_type", data.get("type", "concept")),
            audio_path=data.get("audio_path", ""),
            duration=data.get("duration", 0.0),
        )


@dataclass
class VideoScript:
    """Complete video script containing all segments."""
    topic: str
    segments: List[Segment] = field(default_factory=list)
    total_duration: float = 0.0
    output_dir: str = ""
    
    def add_segment(self, segment: Segment) -> None:
        self.segments.append(segment)
        self.total_duration += segment.duration
    
    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "total_duration": self.total_duration,
            "segment_count": len(self.segments),
            "output_dir": self.output_dir,
            "segments": [s.to_dict() for s in self.segments]
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "VideoScript":
        data = json.loads(json_str)
        script = cls(topic=data.get("topic", ""), output_dir=data.get("output_dir", ""))
        for seg_data in data.get("segments", []):
            seg = Segment.from_dict(seg_data)
            script.segments.append(seg)
            script.total_duration += seg.duration
        return script
