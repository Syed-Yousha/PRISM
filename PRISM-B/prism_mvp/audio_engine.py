"""
PRISM Audio Engine - Parallel TTS Generator
============================================
Generates audio from Director's narration plan.

ROLE: Convert text narrations → MP3 audio files with precise durations
- Parallel TTS generation (8 workers = 7x speedup)
- Precise duration measurement with mutagen
- Audio-first timing drives animation sync

ARCHITECTURE:
Director's Plan → Audio Engine → MP3 files + durations → VideoScript
"""

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

from gtts import gTTS
from mutagen.mp3 import MP3

from data_models import Segment, VideoScript


# ============== CONFIGURATION ==============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_WORKERS = 8
AUDIO_BUFFER = 0.3  # Extra time after each segment


class AudioEngine:
    """
    Audio Engine: Parallel TTS generator for video narration.
    
    Takes Director's plan sections and generates audio files
    with precise duration measurements.
    """
    
    def __init__(self, max_workers: int = MAX_WORKERS):
        """Initialize Audio Engine."""
        self.max_workers = max_workers
        self.output_dir = None
        print(f"   🎤 Audio Engine initialized ({max_workers} workers)")
    
    def _ensure_output_dir(self, topic: str) -> str:
        """Create output directory for audio files."""
        safe_name = re.sub(r"[^\w\s-]", "", topic).replace(" ", "_")[:25]
        timestamp = int(time.time())
        audio_dir = os.path.join(SCRIPT_DIR, "media", "audio", f"{safe_name}_{timestamp}")
        os.makedirs(audio_dir, exist_ok=True)
        self.output_dir = audio_dir
        return audio_dir
    
    def generate_from_plan(self, plan: Dict) -> VideoScript:
        """
        Generate audio from Director's production plan.
        
        Args:
            plan: Director's plan with sections containing narration
            
        Returns:
            VideoScript with segments, audio paths, and durations
        """
        topic = plan.get("topic", "Educational Topic")
        sections = plan.get("sections", [])
        
        print(f"   🎤 Generating audio for {len(sections)} sections...")
        
        # Create output directory
        output_dir = self._ensure_output_dir(topic)
        
        # Convert plan sections to Segment objects
        segments = []
        for section in sections:
            seg = Segment(
                id=section.get("id", len(segments) + 1),
                title=section.get("title", "Section"),
                text=section.get("narration", ""),
                narration=section.get("narration", ""),
                visual_plan="\n".join(section.get("manim_instructions", [])),
                visual_instruction="\n".join(section.get("manim_instructions", [])),
                blackboard_notes=section.get("blackboard_text", ""),
                on_screen_notes=section.get("blackboard_text", ""),
                visual_mode=section.get("visual_mode", "2D"),
                section_type=section.get("type", "concept"),
                duration=section.get("duration", 10)  # Director's estimated duration
            )
            segments.append(seg)
        
        # Generate audio in parallel
        segments = self._generate_audio_parallel(segments, output_dir)
        
        # Build VideoScript
        video_script = VideoScript(topic=topic, output_dir=output_dir)
        for seg in segments:
            video_script.add_segment(seg)
        
        # Save script for debugging
        script_path = os.path.join(output_dir, "script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(video_script.to_json())
        
        print(f"   ✅ Audio complete: {video_script.total_duration:.1f}s total")
        return video_script
    
    def _generate_audio_parallel(self, segments: List[Segment], output_dir: str) -> List[Segment]:
        """Generate audio for all segments in parallel."""
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
    
    def _generate_single_audio(self, segment: Segment, output_dir: str) -> Segment:
        """Generate audio for a single segment."""
        safe_title = re.sub(r"[^\w\s-]", "", segment.title).replace(" ", "_")[:15]
        audio_path = os.path.join(output_dir, f"seg_{segment.id:02d}_{safe_title}.mp3")
        
        try:
            text = segment.narration or segment.text
            if not text:
                text = f"Section {segment.id}: {segment.title}"
            
            # Generate TTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(audio_path)
            
            # Measure duration
            audio = MP3(audio_path)
            segment.audio_path = audio_path
            segment.duration = round(audio.info.length + AUDIO_BUFFER, 2)
            
        except Exception as e:
            print(f"      ⚠️ TTS error for segment {segment.id}: {e}")
            segment.audio_path = ""
            # Keep Director's estimated duration
        
        return segment


# ============== EXPORTS ==============
__all__ = ['AudioEngine']
