"""
PRISM Audio Engine - Text-to-Speech Generator
==============================================
NO API CALLS - Uses gTTS (free Google TTS) + mutagen for duration.

Takes narration text from VideoScript segments and generates audio files.
Parallel generation with ThreadPoolExecutor for speed.

Input:  VideoScript with narration text per segment
Output: Audio files (.mp3) per segment, durations updated in VideoScript
"""

import os
import time
import tempfile
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from gtts import gTTS
from mutagen.mp3 import MP3

from config import SCRIPT_DIR, MEDIA_DIR, MAX_WORKERS, AUDIO_BUFFER


class AudioEngine:
    """
    Generates TTS audio from VideoScript narrations.
    No LLM calls — purely gTTS + mutagen.
    """
    
    def __init__(self):
        self.audio_dir = os.path.join(MEDIA_DIR, "audio")
        os.makedirs(self.audio_dir, exist_ok=True)
    
    def generate_audio_from_script(self, video_script) -> List[str]:
        """
        Generate audio files for all segments in the VideoScript.
        Updates segment.audio_path and segment.duration in-place.
        
        Args:
            video_script: VideoScript with narration text per segment
            
        Returns:
            List of audio file paths
        """
        segments = video_script.segments
        if not segments:
            print("   ⚠️ No segments to generate audio for")
            return []
        
        print(f"\n   🔊 Generating audio for {len(segments)} sections...")
        start = time.time()
        
        # Prepare tasks: (segment_index, narration_text, output_path)
        tasks = []
        for i, seg in enumerate(segments):
            narration = seg.narration.strip()
            if not narration:
                narration = f"Section {seg.id}: {seg.title}"
            
            filename = f"section_{seg.id:02d}_{seg.section_type}.mp3"
            filepath = os.path.join(self.audio_dir, filename)
            tasks.append((i, narration, filepath))
        
        # Generate in parallel
        audio_paths = [None] * len(tasks)
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(tasks))) as executor:
            futures = {
                executor.submit(self._generate_single_audio, text, path): (idx, path)
                for idx, text, path in tasks
            }
            
            for future in as_completed(futures):
                idx, path = futures[future]
                try:
                    success = future.result()
                    if success:
                        audio_paths[idx] = path
                        # Get duration
                        duration = self._get_duration(path)
                        segments[idx].audio_path = path
                        segments[idx].duration = duration + AUDIO_BUFFER
                    else:
                        print(f"   ⚠️ Audio generation failed for section {idx + 1}")
                except Exception as e:
                    print(f"   ❌ Audio error for section {idx + 1}: {e}")
        
        elapsed = time.time() - start
        valid = [p for p in audio_paths if p]
        total_dur = sum(s.duration for s in segments if s.duration > 0)
        
        print(f"   🔊 Generated {len(valid)}/{len(tasks)} audio files in {elapsed:.1f}s")
        print(f"   🔊 Total audio duration: {total_dur:.1f}s")
        
        # Update total duration
        video_script.total_duration = total_dur
        
        return [p for p in audio_paths if p]
    
    def _generate_single_audio(self, text: str, output_path: str) -> bool:
        """
        Generate a single audio file from text using gTTS.
        
        Args:
            text: Narration text
            output_path: Path to save the .mp3 file
            
        Returns:
            True if successful
        """
        try:
            # Clean text for TTS
            clean_text = self._clean_for_tts(text)
            if not clean_text:
                clean_text = "This section covers the topic."
            
            tts = gTTS(text=clean_text, lang='en', slow=False)
            
            # Write to temp file first, then move (atomic)
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False, dir=self.audio_dir) as tmp:
                tmp_path = tmp.name
                tts.save(tmp_path)
            
            # Move to final path
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(tmp_path, output_path)
            
            return os.path.exists(output_path) and os.path.getsize(output_path) > 0
            
        except Exception as e:
            print(f"   ❌ TTS failed: {e}")
            # Cleanup temp file
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False
    
    def _clean_for_tts(self, text: str) -> str:
        """Clean text for better TTS output."""
        import re
        # Remove LaTeX commands
        text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
        text = re.sub(r'\\[a-zA-Z]+', '', text)
        # Remove special chars but keep basic punctuation
        text = re.sub(r'[{}$^_\\]', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Replace common math symbols with words
        text = text.replace('>=', ' greater than or equal to ')
        text = text.replace('<=', ' less than or equal to ')
        text = text.replace('!=', ' not equal to ')
        text = text.replace('==', ' equals ')
        text = text.replace('**', ' to the power of ')
        text = text.replace('*', ' times ')
        text = text.replace('/', ' divided by ')
        text = text.replace('+', ' plus ')
        text = text.replace('-', ' minus ')
        text = text.replace('=', ' equals ')
        # Clean up multiple spaces from replacements
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _get_duration(self, filepath: str) -> float:
        """Get audio duration in seconds using mutagen."""
        try:
            audio = MP3(filepath)
            return audio.info.length
        except Exception:
            # Fallback: estimate from file size (~16kbps for gTTS)
            try:
                size = os.path.getsize(filepath)
                return size / 2000  # rough estimate
            except Exception:
                return 5.0  # safe default


# ============== CLI TESTING ==============
if __name__ == "__main__":
    from data_models import Segment, VideoScript
    
    print("\n🔊 PRISM Audio Engine - Test\n")
    
    script = VideoScript(topic="Test")
    script.add_segment(Segment(
        id=1, title="Introduction", section_type="introduction",
        narration="Welcome to this lesson on the Pythagorean theorem."
    ))
    script.add_segment(Segment(
        id=2, title="Concept", section_type="concept",
        narration="The Pythagorean theorem states that a squared plus b squared equals c squared."
    ))
    script.add_segment(Segment(
        id=3, title="Examples", section_type="examples",
        narration="Let's try an example. If a equals 3 and b equals 4, what is c?"
    ))
    
    engine = AudioEngine()
    paths = engine.generate_audio_from_script(script)
    
    print(f"\nGenerated {len(paths)} audio files:")
    for seg in script.segments:
        print(f"  Section {seg.id}: {seg.duration:.1f}s — {seg.audio_path}")
