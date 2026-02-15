"""
PRISM Main Pipeline - Video Generation Orchestrator
====================================================
Orchestrates the full video generation pipeline:

  Phase 1: RAG Context     — Retrieve Manim examples from ChromaDB
  Phase 2: Script (Call 1) — Generate 3-section animation script via Groq (free)
  Phase 3: Audio (TTS)     — Generate narration audio via gTTS (free, no API call)
  Phase 4: Code (Call 2)   — Generate Manim code via Gemini (1 call, free tier)
  Phase 5: Render          — Render Manim scene to video
  Phase 6: Merge           — Combine video + audio into final output

API CALLS: 2 total
  Call 1: Groq  → animation script  (free, unlimited)
  Call 2: Gemini → Manim code       (free tier, 1 call)
  (optional): Groq → error fix retry (free)

Usage:
  python main.py                          # Interactive — asks for topic
  python main.py "Pythagorean Theorem"    # Direct topic
  python main.py "Quadratic Formula" -q m # With quality
"""

import os
import sys
import time
import argparse
import json
import subprocess as sp
import platform
from typing import Optional

from config import (
    SCRIPT_DIR, MEDIA_DIR, RENDER_QUALITY,
    BGM_ENABLED, BGM_VOLUME, BGM_URLS,
)
from rag_engine import RAGEngine
from prompt_maker import PromptMaker
from audio_engine import AudioEngine
from manim_engine import ManimEngine
from data_models import VideoScript


def run_pipeline(topic: str, quality: str = RENDER_QUALITY) -> Optional[str]:
    """
    Run the full PRISM video generation pipeline.
    
    Args:
        topic: Educational math topic (e.g., "Pythagorean Theorem")
        quality: Render quality ('l'=480p, 'm'=720p, 'h'=1080p)
        
    Returns:
        Path to final video file, or None on failure
    """
    print("\n" + "=" * 60)
    print(f"🔮 PRISM Video Generator")
    print(f"   Topic: {topic}")
    print(f"   Quality: {quality}")
    print("=" * 60)
    
    pipeline_start = time.time()
    
    # Override quality if specified
    if quality != RENDER_QUALITY:
        import config
        config.RENDER_QUALITY = quality
    
    # ──── Phase 1: RAG Context ────
    print("\n📚 Phase 1: Retrieving RAG context...")
    phase_start = time.time()
    try:
        rag_engine = RAGEngine()
        rag_context = rag_engine.get_context(topic)
        print(f"   ✅ RAG context: {len(rag_context):,} chars ({time.time() - phase_start:.1f}s)")
    except Exception as e:
        print(f"   ⚠️ RAG failed ({e}), continuing without context")
        rag_context = ""
    
    # ──── Phase 2: Script Generation (API Call 1) ────
    print("\n📝 Phase 2: Generating animation script (API Call 1)...")
    phase_start = time.time()
    try:
        prompt_maker = PromptMaker()
        video_script = prompt_maker.generate_script(topic, rag_context)
        print(f"   ✅ Script: {len(video_script.segments)} sections ({time.time() - phase_start:.1f}s)")
    except Exception as e:
        print(f"   ❌ Script generation failed: {e}")
        return None
    
    # Save script for debugging
    _save_debug_output(video_script, "animation_script.json")
    
    # ──── Phase 3: Audio Generation (gTTS, no API call) ────
    print("\n🔊 Phase 3: Generating audio (gTTS)...")
    phase_start = time.time()
    try:
        audio_engine = AudioEngine()
        audio_paths = audio_engine.generate_audio_from_script(video_script)
        if not audio_paths:
            print("   ❌ Audio generation failed")
            return None
        print(f"   ✅ Audio: {len(audio_paths)} files, {video_script.total_duration:.1f}s total ({time.time() - phase_start:.1f}s)")
    except Exception as e:
        print(f"   ❌ Audio failed: {e}")
        return None
    
    # ──── Phase 4: Code Generation (API Call 2 — OpenRouter) ────
    print("\n🎬 Phase 4: Generating Manim code (API Call 2 — Claude)...")
    phase_start = time.time()
    try:
        manim_engine = ManimEngine()
        video_path = manim_engine.generate_and_render(video_script, rag_context)
        print(f"   ⏱️ Code + Render took {time.time() - phase_start:.1f}s")
    except Exception as e:
        print(f"   ❌ Code generation/render failed: {e}")
        video_path = None
    
    if not video_path:
        print("\n   ❌ Video rendering failed after all retries")
        return None
    
    # ──── Phase 5: Merge Audio + Video ────
    print("\n🎵 Phase 5: Merging audio and video...")
    phase_start = time.time()
    try:
        final_path = merge_video_audio(video_path, audio_paths, topic)
        if final_path:
            print(f"   ✅ Final video: {final_path} ({time.time() - phase_start:.1f}s)")
        else:
            print("   ⚠️ Merge failed, returning raw video")
            final_path = video_path
    except Exception as e:
        print(f"   ⚠️ Merge error ({e}), returning raw video")
        final_path = video_path
    
    # ──── Summary ────
    total_time = time.time() - pipeline_start
    print("\n" + "=" * 60)
    print(f"✅ PRISM Complete!")
    print(f"   Topic: {topic}")
    print(f"   Duration: {video_script.total_duration:.1f}s video")
    print(f"   Pipeline: {total_time:.1f}s total")
    print(f"   API Calls: Groq=1 (script) + Claude=1 (code)")
    print(f"   Output: {final_path}")
    print("=" * 60 + "\n")
    
    # Auto-open the video
    _open_video(final_path)
    
    return final_path


def merge_video_audio(video_path: str, audio_paths: list, topic: str) -> Optional[str]:
    """
    Merge rendered video with audio narration using ffmpeg (reliable).
    Falls back to moviepy if ffmpeg is not available.
    
    Args:
        video_path: Path to rendered .mp4
        audio_paths: List of audio .mp3 files (one per section)
        topic: Topic name for output filename
        
    Returns:
        Path to final merged video, or None
    """
    if not audio_paths:
        return video_path
    
    # Output path
    safe_topic = "".join(c if c.isalnum() or c in " _-" else "_" for c in topic)[:50]
    output_dir = os.path.join(MEDIA_DIR, "videos", "final")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"PRISM_{safe_topic}.mp4")
    
    # Step 1: Concatenate all audio files into one
    concat_audio = os.path.join(MEDIA_DIR, "audio", "_combined.mp3")
    valid_paths = [p for p in audio_paths if p and os.path.exists(p)]
    if not valid_paths:
        return video_path
    
    # Try ffmpeg first (most reliable)
    if _ffmpeg_available():
        try:
            result = _merge_with_ffmpeg(video_path, valid_paths, concat_audio, output_path)
            if result:
                return result
        except Exception as e:
            print(f"   ⚠️ ffmpeg merge failed: {e}, trying moviepy...")
    
    # Fallback: moviepy
    return _merge_with_moviepy(video_path, valid_paths, output_path)


def _ffmpeg_available() -> bool:
    """Check if ffmpeg is installed."""
    try:
        sp.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def _merge_with_ffmpeg(video_path: str, audio_paths: list, concat_audio: str, output_path: str) -> Optional[str]:
    """Merge video + audio using ffmpeg (most reliable method)."""
    
    # Step 1: Create a concat list file for audio
    list_file = os.path.join(os.path.dirname(concat_audio), "_audiolist.txt")
    with open(list_file, 'w', encoding='utf-8') as f:
        for p in audio_paths:
            # ffmpeg concat needs forward slashes and escaped quotes
            safe_p = p.replace('\\', '/')
            f.write(f"file '{safe_p}'\n")
    
    # Step 2: Concatenate audio files
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", concat_audio
    ]
    result = sp.run(concat_cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"   ⚠️ Audio concat failed: {result.stderr[:300]}")
        # Fallback: just use first audio
        concat_audio = audio_paths[0]
    
    # Step 3: Merge video + audio
    merge_cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", concat_audio,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-map", "0:v:0",
        "-map", "1:a:0",
        output_path,
    ]
    result = sp.run(merge_cmd, capture_output=True, text=True, timeout=120)
    
    # Cleanup temp files
    for f in [list_file]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
    
    if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        print(f"   ✅ Merged with ffmpeg: {output_path}")
        return output_path
    else:
        print(f"   ⚠️ ffmpeg merge error: {result.stderr[:300]}")
        return None


def _merge_with_moviepy(video_path: str, audio_paths: list, output_path: str) -> Optional[str]:
    """Fallback: merge video + audio using moviepy."""
    try:
        from moviepy.editor import (
            VideoFileClip, AudioFileClip,
            concatenate_audioclips,
        )
    except ImportError:
        print("   ⚠️ Neither ffmpeg nor moviepy available — returning raw video (no audio)")
        return video_path
    
    try:
        video = VideoFileClip(video_path)
        
        audio_clips = []
        for path in audio_paths:
            audio_clips.append(AudioFileClip(path))
        
        combined_audio = concatenate_audioclips(audio_clips)
        
        # Trim audio to video length if needed
        if combined_audio.duration > video.duration:
            combined_audio = combined_audio.subclip(0, video.duration)
        
        final = video.set_audio(combined_audio)
        
        final.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            bitrate='2000k',
            audio_bitrate='128k',
            logger=None,
        )
        
        # Cleanup
        video.close()
        for clip in audio_clips:
            clip.close()
        combined_audio.close()
        final.close()
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"   ✅ Merged with moviepy: {output_path}")
            return output_path
            
    except Exception as e:
        print(f"   ❌ moviepy merge failed: {e}")
    
    return video_path


def _open_video(path: str) -> None:
    """Auto-open the video file with the default system player."""
    if not path or not os.path.exists(path):
        return
    
    print(f"\n   🎬 Opening video...")
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            sp.Popen(["open", path])
        else:  # Linux
            sp.Popen(["xdg-open", path])
    except Exception as e:
        print(f"   ⚠️ Could not auto-open video: {e}")
        print(f"   📂 Open manually: {path}")


def get_bgm() -> Optional[str]:
    """Download background music if BGM is enabled."""
    if not BGM_ENABLED:
        return None
    
    music_dir = os.path.join(MEDIA_DIR, "music")
    os.makedirs(music_dir, exist_ok=True)
    
    bgm_path = os.path.join(music_dir, "bgm.mp3")
    if os.path.exists(bgm_path):
        return bgm_path
    
    import urllib.request
    for url in BGM_URLS:
        try:
            print(f"   🎵 Downloading BGM...")
            urllib.request.urlretrieve(url, bgm_path)
            if os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 1000:
                return bgm_path
        except Exception:
            continue
    
    return None


def _save_debug_output(video_script: VideoScript, filename: str) -> None:
    """Save intermediate output for debugging."""
    debug_dir = os.path.join(SCRIPT_DIR, "prompt_outputs")
    os.makedirs(debug_dir, exist_ok=True)
    
    filepath = os.path.join(debug_dir, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(video_script.to_json())
    except Exception:
        pass


def generate_video(topic: str, quality: str = "l") -> Optional[str]:
    """
    Public API for video generation.
    
    Args:
        topic: Math topic to explain
        quality: 'l' (480p), 'm' (720p), 'h' (1080p)
        
    Returns:
        Path to final video, or None
    """
    return run_pipeline(topic, quality)


# ============== CLI ==============
def main():
    parser = argparse.ArgumentParser(
        description="PRISM - AI Educational Video Generator",
        epilog="Example: python main.py \"Pythagorean Theorem\" --quality m",
    )
    parser.add_argument(
        "topic",
        type=str,
        nargs="?",       # Make topic OPTIONAL
        default=None,
        help="Math topic to generate a video for (will prompt if not provided)",
    )
    parser.add_argument(
        "--quality", "-q",
        choices=["l", "m", "h"],
        default=RENDER_QUALITY,
        help="Render quality: l=480p, m=720p, h=1080p (default: l)",
    )
    
    args = parser.parse_args()
    
    topic = args.topic
    
    # Interactive prompt if no topic provided
    if not topic:
        print("\n" + "=" * 60)
        print("🔮 PRISM - AI Educational Video Generator")
        print("=" * 60)
        print("\nAPI Usage: Groq (script) + Claude (code) = 2 calls total")
        print("Audio: gTTS (free, no API key needed)\n")
        topic = input("📚 Enter a math topic (e.g., Pythagorean Theorem): ").strip()
        if not topic:
            print("❌ No topic entered. Exiting.")
            sys.exit(1)
    
    result = run_pipeline(topic, args.quality)
    
    if result:
        print(f"\n🎉 Video saved to: {result}")
        sys.exit(0)
    else:
        print("\n❌ Video generation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
