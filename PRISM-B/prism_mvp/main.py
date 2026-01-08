"""
PRISM - Click-and-Watch Video Generator
=======================================
Production-ready orchestrator with maximum speed optimizations.

ARCHITECTURE:
1. RAG First: Fetch knowledge context upfront
2. Audio First: Generate script + audio in parallel (drives timing)
3. Visual Core: Generate Manim code with RAG context
4. Merge & Clean: Combine audio/video, cleanup temp files

OPTIMIZATIONS:
- Single RAG call upfront
- Single LLM call for complete script
- Parallel audio generation (8 workers)
- Manim caching enabled
- Auto-cleanup of temporary files

WORKFLOW:
Topic → RAG Fetch → Parallel Audio → Code Gen (RAG-enhanced) → Render → Merge → Cleanup
"""

import os
import sys
import time
import glob
import shutil
import urllib.request
from typing import Optional

from moviepy import (
    VideoFileClip, 
    AudioFileClip, 
    concatenate_audioclips, 
    CompositeAudioClip, 
    vfx
)

from audio_engine import AudioEngine
from manim_engine import ManimEngine, GENERATED_SCRIPT_PATH
from rag_engine import RAGEngine
from data_models import VideoScript


# ============== CONFIGURATION ==============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(SCRIPT_DIR, "media", "music")

# Render quality: 'l'=480p15, 'm'=720p30 (recommended), 'h'=1080p60
RENDER_QUALITY = "m"

# Background music settings
BGM_VOLUME = 0.08  # 8% volume for subtle background
BGM_URL = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"


# ============== AUDIO HELPERS ==============
def get_bgm() -> Optional[str]:
    """
    Get or download background music.
    
    Downloads royalty-free music on first run, caches for future use.
    
    Returns:
        Path to BGM file, or None if download fails
    """
    os.makedirs(MUSIC_DIR, exist_ok=True)
    path = os.path.join(MUSIC_DIR, "bgm.mp3")
    
    # Check cache
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        return path
    
    try:
        print("   🎵 Downloading background music...")
        urllib.request.urlretrieve(BGM_URL, path)
        return path if os.path.exists(path) else None
    except Exception as e:
        print(f"   ⚠️ BGM download failed: {e}")
        return None


def merge_audio(video_script: VideoScript) -> Optional[str]:
    """
    Concatenate all segment audio into one track.
    
    Combines individual segment MP3s into a single narration track.
    
    Args:
        video_script: VideoScript with audio paths
        
    Returns:
        Path to merged audio file, or None if no audio
    """
    clips = []
    
    for seg in video_script.segments:
        if seg.audio_path and os.path.exists(seg.audio_path):
            try:
                clips.append(AudioFileClip(seg.audio_path))
            except Exception as e:
                print(f"   ⚠️ Could not load audio for segment {seg.id}: {e}")
    
    if not clips:
        print("   ⚠️ No audio clips to merge")
        return None
    
    merged = concatenate_audioclips(clips)
    output = os.path.join(video_script.output_dir, "narration.mp3")
    merged.write_audiofile(output, logger=None)
    
    # Cleanup
    for c in clips:
        c.close()
    merged.close()
    
    return output


def mix_bgm(voice_path: str, output_path: str) -> str:
    """
    Mix voiceover with background music.
    
    Loops BGM if needed, sets to low volume (8%) to not overpower narration.
    
    Args:
        voice_path: Path to narration audio
        output_path: Path for output mixed audio
        
    Returns:
        Path to mixed audio (or voice_path if mixing fails)
    """
    try:
        voice = AudioFileClip(voice_path)
        bgm_path = get_bgm()
        
        if not bgm_path:
            return voice_path
        
        bgm = AudioFileClip(bgm_path)
        
        # Loop BGM if shorter than voice
        if bgm.duration < voice.duration:
            loops = int(voice.duration / bgm.duration) + 1
            bgm = concatenate_audioclips([bgm] * loops)
        
        # Trim and reduce volume
        bgm = bgm.with_duration(voice.duration).with_volume_scaled(BGM_VOLUME)
        
        # Mix
        mixed = CompositeAudioClip([voice, bgm])
        mixed.write_audiofile(output_path, logger=None)
        
        # Cleanup
        voice.close()
        bgm.close()
        mixed.close()
        
        return output_path
        
    except Exception as e:
        print(f"   ⚠️ BGM mixing failed: {e}")
        return voice_path


def merge_video_audio(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Combine video with audio track.
    
    Handles duration mismatch by freezing last frame if video is shorter.
    
    Args:
        video_path: Path to video file
        audio_path: Path to audio file
        output_path: Path for output video
        
    Returns:
        Path to merged video
    """
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    
    # Handle duration mismatch
    if video.duration < audio.duration - 0.5:
        shortfall = audio.duration - video.duration + 0.5
        video = video.with_effects([vfx.Freeze(t=video.duration - 0.1, freeze_duration=shortfall)])
        print(f"   ℹ️ Extended video by {shortfall:.1f}s to match audio")
    
    if audio.duration > video.duration:
        audio = audio.with_duration(video.duration)
    
    # Merge
    final = video.with_audio(audio)
    final.write_videofile(
        output_path, 
        codec='libx264', 
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a', 
        remove_temp=True, 
        logger=None
    )
    
    # Cleanup
    video.close()
    audio.close()
    final.close()
    
    return output_path


def cleanup_temp_files(output_dir: str, aggressive: bool = False):
    """
    Remove temporary files after successful merge.
    
    Args:
        output_dir: Directory to clean
        aggressive: If True, also removes intermediate audio files
    """
    # Temp file patterns
    patterns = ["temp*.mp3", "temp*.m4a", "temp*.wav", "temp-audio.*"]
    
    for pattern in patterns:
        for f in glob.glob(os.path.join(output_dir, pattern)):
            try:
                os.remove(f)
            except Exception:
                pass
    
    # Clean workspace temp files
    for f in glob.glob(os.path.join(SCRIPT_DIR, "temp*")):
        try:
            os.remove(f)
        except Exception:
            pass
    
    if aggressive:
        # Remove intermediate audio files (keep script.json for debugging)
        for f in glob.glob(os.path.join(output_dir, "seg_*.mp3")):
            try:
                os.remove(f)
            except Exception:
                pass
        
        # Remove narration.mp3 and mixed.mp3
        for f in ["narration.mp3", "mixed.mp3"]:
            path = os.path.join(output_dir, f)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass


# ============== MAIN PIPELINE ==============
def run_pipeline(topic: str, quality: str = RENDER_QUALITY, cleanup: bool = True) -> str:
    """
    Full Automated Pipeline: Topic → Video
    
    WORKFLOW:
    1. RAG Fetch: Get relevant code examples from knowledge base
    2. Audio Gen: Single LLM call + parallel TTS generation
    3. Code Gen: Generate Manim code with RAG context
    4. Render: Render video with caching
    5. Merge: Combine audio + video with BGM
    6. Cleanup: Remove temporary files
    
    OPTIMIZATIONS:
    - Single RAG call upfront (no repeated queries)
    - Single LLM call for complete script (no 7 separate calls)
    - Parallel audio generation (8 workers → 7x speedup)
    - Manim caching enabled (huge speedup on re-renders)
    
    Args:
        topic: Educational topic (e.g., "Pythagorean Theorem")
        quality: Render quality ('l', 'm', 'h')
        cleanup: Whether to remove temp files after success
        
    Returns:
        Path to final video file, or empty string on failure
    """
    start = time.time()
    
    # Header
    quality_names = {'l': '480p', 'm': '720p', 'h': '1080p'}
    print("\n" + "═" * 60)
    print("   🔮 PRISM Video Generator - Maximum Speed Edition")
    print("═" * 60)
    print(f"   📚 Topic: {topic}")
    print(f"   🎬 Quality: {quality} ({quality_names[quality]})")
    print("═" * 60)
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE 0: RAG - Knowledge Fetch
    # ═══════════════════════════════════════════════════════════════
    print("\n📚 PHASE 0: Loading knowledge base...")
    phase_start = time.time()
    
    rag = RAGEngine()
    rag_context = rag.get_context(topic)
    
    rag_time = time.time() - phase_start
    print(f"   ✅ RAG complete ({len(rag_context):,} chars, {rag_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE 1: AUDIO - Script + Parallel Audio Generation
    # ═══════════════════════════════════════════════════════════════
    print("\n📢 PHASE 1: Generating script + audio (parallel)...")
    phase_start = time.time()
    
    audio_engine = AudioEngine()
    video_script = audio_engine.process(topic, rag_context)
    
    if not video_script.segments:
        print("   ❌ Failed to generate script")
        return ""
    
    audio_time = time.time() - phase_start
    print(f"   ✅ Audio complete: {len(video_script.segments)} segments, {video_script.total_duration:.1f}s total ({audio_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE 2: VISUAL - Code Generation + Rendering
    # ═══════════════════════════════════════════════════════════════
    print("\n🎨 PHASE 2: Generating animation code...")
    phase_start = time.time()
    
    manim = ManimEngine(quality=quality)
    code = manim.generate_full_code(video_script, rag_context)
    
    code_time = time.time() - phase_start
    print(f"   ✅ Code generated ({len(code):,} chars, {code_time:.1f}s)")
    
    print("\n🎬 PHASE 3: Rendering video...")
    phase_start = time.time()
    
    video_path = manim.render(code, topic)
    
    if not video_path or not os.path.exists(video_path):
        print(f"   ❌ Render failed. Debug code at: {GENERATED_SCRIPT_PATH}")
        return ""
    
    render_time = time.time() - phase_start
    print(f"   ✅ Render complete ({render_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE 4: MERGE - Audio + Video + BGM
    # ═══════════════════════════════════════════════════════════════
    print("\n🔧 PHASE 4: Merging audio + video...")
    phase_start = time.time()
    
    narration = merge_audio(video_script)
    if not narration:
        print("   ⚠️ No narration audio, returning raw video")
        return video_path
    
    # Mix with background music
    mixed = os.path.join(video_script.output_dir, "mixed.mp3")
    final_audio = mix_bgm(narration, mixed)
    
    # Final output path
    safe_name = topic.replace(" ", "_")[:25]
    timestamp = int(time.time())
    final_path = os.path.join(os.path.dirname(video_path), f"PRISM_{safe_name}_{timestamp}.mp4")
    
    # Merge video + audio
    final = merge_video_audio(video_path, final_audio, final_path)
    
    merge_time = time.time() - phase_start
    print(f"   ✅ Merge complete ({merge_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE 5: CLEANUP
    # ═══════════════════════════════════════════════════════════════
    if cleanup:
        cleanup_temp_files(video_script.output_dir)
        cleanup_temp_files(SCRIPT_DIR)
    
    # ═══════════════════════════════════════════════════════════════
    # COMPLETE
    # ═══════════════════════════════════════════════════════════════
    elapsed = time.time() - start
    
    print("\n" + "═" * 60)
    print("   🎉 VIDEO COMPLETE!")
    print("═" * 60)
    print(f"   📁 Output: {final}")
    print(f"   📊 Video Duration: {video_script.total_duration:.0f}s")
    print(f"   ⏱️  Total Time: {elapsed:.0f}s")
    print(f"   📈 Breakdown:")
    print(f"       RAG:    {rag_time:.1f}s")
    print(f"       Audio:  {audio_time:.1f}s")
    print(f"       Code:   {code_time:.1f}s")
    print(f"       Render: {render_time:.1f}s")
    print(f"       Merge:  {merge_time:.1f}s")
    print("═" * 60)
    
    return final


# ============== CLI ==============
def main():
    """
    CLI Entry Point: Enter topic, get video.
    
    Interactive mode - prompts for topic and generates video.
    """
    print("\n" + "═" * 60)
    print("   🔮 PRISM - Educational Video Generator")
    print("   Enter a topic, get a video. It's that simple.")
    print("═" * 60)
    
    topic = input("\n📝 Enter topic: ").strip()
    if not topic:
        topic = "Pythagorean Theorem"
        print(f"   Using default: {topic}")
    
    # Quality selection
    print("\n🎬 Quality options:")
    print("   l = 480p  (fastest, ~1 min)")
    print("   m = 720p  (recommended, ~2 min)")
    print("   h = 1080p (best, ~4 min)")
    quality = input("Select quality [m]: ").strip().lower()
    if quality not in ['l', 'm', 'h']:
        quality = 'm'
    
    time_estimates = {'l': '~1', 'm': '~2', 'h': '~4'}
    print(f"\n⏳ Generating video... (estimated: {time_estimates[quality]} minutes)")
    print("   You can watch progress below.\n")
    
    video = run_pipeline(topic, quality=quality)
    
    if video and os.path.exists(video):
        print(f"\n🎥 Opening video...")
        if sys.platform == "win32":
            os.startfile(video)
        elif sys.platform == "darwin":
            os.system(f'open "{video}"')
        else:
            os.system(f'xdg-open "{video}"')
    else:
        print("\n❌ Video generation failed. Check logs above for details.")


# ============== PROGRAMMATIC API ==============
def generate_video(
    topic: str, 
    quality: str = "m", 
    cleanup: bool = True
) -> str:
    """
    Programmatic API for video generation.
    
    Use this function to integrate PRISM into other applications.
    
    Args:
        topic: Educational topic
        quality: 'l' (480p), 'm' (720p), 'h' (1080p)
        cleanup: Whether to remove temp files after success
        
    Returns:
        Path to generated video file
        
    Example:
        >>> from main import generate_video
        >>> video_path = generate_video("Pythagorean Theorem", quality="m")
        >>> print(f"Video saved to: {video_path}")
    """
    return run_pipeline(topic, quality=quality, cleanup=cleanup)


def quick_preview(topic: str) -> str:
    """
    Generate a quick preview video (480p, fastest settings).
    
    Good for testing script/visual quality before full render.
    
    Args:
        topic: Educational topic
        
    Returns:
        Path to preview video
    """
    return run_pipeline(topic, quality="l", cleanup=True)


def high_quality(topic: str) -> str:
    """
    Generate high-quality video (1080p60).
    
    Use for final production output.
    
    Args:
        topic: Educational topic
        
    Returns:
        Path to high-quality video
    """
    return run_pipeline(topic, quality="h", cleanup=True)


# ============== ENTRY POINT ==============
if __name__ == "__main__":
    main()
