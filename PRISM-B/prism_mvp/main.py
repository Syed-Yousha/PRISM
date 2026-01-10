"""
PRISM - Click-and-Watch Video Generator
=======================================
NEW ARCHITECTURE: Director → Cinematographer Pattern

PIPELINE:
1. RAG: Fetch relevant Manim code examples from Curator database
2. DIRECTOR (Groq): Analyze topic → Create detailed production plan
3. AUDIO: Generate TTS audio from narrations (parallel, 8 workers)
4. CINEMATOGRAPHER (Gemini): Convert plan → Perfect Manim code
5. RENDER: Execute Manim → Generate video
6. MERGE: Combine audio + video + background music
7. CLEANUP: Remove temporary files

WHY THIS WORKS:
- Groq (fast) plans the video structure with specific instructions
- Gemini (smart) converts instructions to correct Manim code
- RAG prevents hallucination by providing working examples
- Audio-first timing ensures perfect sync
"""

import os
import sys
import time
import glob
import urllib.request
from typing import Optional

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    concatenate_audioclips,
    CompositeAudioClip,
    vfx
)

from prompt_director import PromptDirector
from audio_engine import AudioEngine
from manim_engine import ManimEngine, GENERATED_SCRIPT_PATH
from rag_engine import RAGEngine
from data_models import VideoScript


# ============== CONFIGURATION ==============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(SCRIPT_DIR, "media", "music")

RENDER_QUALITY = "l"  # l=480p (fast), m=720p (default), h=1080p
BGM_VOLUME = 0.03  # Very subtle background music (3% volume)
# Free royalty-free music URLs (with fallbacks)
BGM_URLS = [
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",  # SoundHelix (no auth needed)
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Shipping_Lanes.mp3",
]


# ============== AUDIO HELPERS ==============
def get_bgm() -> Optional[str]:
    """Download or get cached background music."""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    path = os.path.join(MUSIC_DIR, "bgm.mp3")
    
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        return path
    
    # Try each URL with proper headers
    for url in BGM_URLS:
        try:
            print(f"   🎵 Downloading background music...")
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=15) as response:
                with open(path, 'wb') as f:
                    f.write(response.read())
            if os.path.exists(path) and os.path.getsize(path) > 10000:
                print("   ✅ BGM downloaded")
                return path
        except Exception as e:
            print(f"   ⚠️ BGM source failed, trying next...")
            continue
    
    print("   ⚠️ All BGM sources failed - video will have narration only")
    return None


def merge_audio(video_script: VideoScript) -> Optional[str]:
    """Concatenate segment audio into single track."""
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
    
    for c in clips:
        c.close()
    merged.close()
    
    return output


def mix_bgm(voice_path: str, output_path: str) -> str:
    """Mix voiceover with background music."""
    try:
        voice = AudioFileClip(voice_path)
        bgm_path = get_bgm()
        
        if not bgm_path:
            return voice_path
        
        bgm = AudioFileClip(bgm_path)
        
        if bgm.duration < voice.duration:
            loops = int(voice.duration / bgm.duration) + 1
            bgm = concatenate_audioclips([bgm] * loops)
        
        bgm = bgm.with_duration(voice.duration).with_volume_scaled(BGM_VOLUME)
        mixed = CompositeAudioClip([voice, bgm])
        mixed.write_audiofile(output_path, logger=None)
        
        voice.close()
        bgm.close()
        mixed.close()
        
        return output_path
        
    except Exception as e:
        print(f"   ⚠️ BGM mixing failed: {e}")
        return voice_path


def merge_video_audio(video_path: str, audio_path: str, output_path: str) -> str:
    """Combine video with audio track."""
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    
    # Handle duration mismatch
    if video.duration < audio.duration - 0.5:
        shortfall = audio.duration - video.duration + 0.5
        video = video.with_effects([vfx.Freeze(t=video.duration - 0.1, freeze_duration=shortfall)])
        print(f"   ℹ️ Extended video by {shortfall:.1f}s")
    
    if audio.duration > video.duration:
        audio = audio.with_duration(video.duration)
    
    final = video.with_audio(audio)
    final.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        logger=None
    )
    
    video.close()
    audio.close()
    final.close()
    
    return output_path


def cleanup_temp_files(output_dir: str):
    """Remove temporary files."""
    patterns = ["temp*.mp3", "temp*.m4a", "temp*.wav", "temp-audio.*"]
    
    for pattern in patterns:
        for f in glob.glob(os.path.join(output_dir, pattern)):
            try:
                os.remove(f)
            except:
                pass
    
    for f in glob.glob(os.path.join(SCRIPT_DIR, "temp*")):
        try:
            os.remove(f)
        except:
            pass


# ============== MAIN PIPELINE ==============
def run_pipeline(topic: str, quality: str = RENDER_QUALITY, cleanup: bool = True) -> str:
    """
    Full Pipeline: Topic → Video
    
    NEW ARCHITECTURE:
    1. RAG Fetch - Get working code examples
    2. Director (Groq) - Create detailed production plan  
    3. Audio - Parallel TTS generation
    4. Cinematographer (Gemini) - Generate Manim code
    5. Render - Execute Manim
    6. Merge - Combine audio + video + BGM
    """
    start = time.time()
    
    # Header
    quality_names = {'l': '480p', 'm': '720p', 'h': '1080p'}
    print("\n" + "═" * 60)
    print("   🔮 PRISM Video Generator v2.0")
    print("   Director → Cinematographer Architecture")
    print("═" * 60)
    print(f"   📚 Topic: {topic}")
    print(f"   🎬 Quality: {quality} ({quality_names.get(quality, '720p')})")
    print("═" * 60)
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 0: RAG - Knowledge Fetch
    # ═══════════════════════════════════════════════════════════
    print("\n📚 PHASE 0: Loading knowledge base...")
    phase_start = time.time()
    
    rag = RAGEngine()
    rag_context = rag.get_context(topic)
    
    rag_time = time.time() - phase_start
    print(f"   ✅ RAG complete ({len(rag_context):,} chars, {rag_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 1: DIRECTOR (Groq) - Production Planning
    # ═══════════════════════════════════════════════════════════
    print("\n🎬 PHASE 1: Director planning video...")
    phase_start = time.time()
    
    director = PromptDirector()
    plan = director.create_production_plan(topic, rag_context)
    
    director_time = time.time() - phase_start
    sections_count = len(plan.get("sections", []))
    print(f"   ✅ Plan ready: {sections_count} sections ({director_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 2: AUDIO - Parallel TTS Generation
    # ═══════════════════════════════════════════════════════════
    print("\n🎤 PHASE 2: Generating audio...")
    phase_start = time.time()
    
    audio_engine = AudioEngine()
    video_script = audio_engine.generate_from_plan(plan)
    
    if not video_script.segments:
        print("   ❌ No audio generated")
        return ""
    
    audio_time = time.time() - phase_start
    print(f"   ✅ Audio: {video_script.total_duration:.1f}s ({audio_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 3: CINEMATOGRAPHER (Gemini) - Code Generation
    # ═══════════════════════════════════════════════════════════
    print("\n🎥 PHASE 3: Cinematographer generating code...")
    phase_start = time.time()
    
    cinematographer = ManimEngine(quality=quality)
    code = cinematographer.generate_full_scene(plan, video_script, rag_context)
    
    code_time = time.time() - phase_start
    print(f"   ✅ Code: {len(code):,} chars ({code_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 4: RENDER - Manim Execution
    # ═══════════════════════════════════════════════════════════
    print("\n🎨 PHASE 4: Rendering video...")
    phase_start = time.time()
    
    video_path = cinematographer.render(code, topic)
    
    if not video_path or not os.path.exists(video_path):
        print(f"   ❌ Render failed. Debug: {GENERATED_SCRIPT_PATH}")
        return ""
    
    render_time = time.time() - phase_start
    print(f"   ✅ Rendered ({render_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 5: MERGE - Audio + Video + BGM
    # ═══════════════════════════════════════════════════════════
    print("\n🔧 PHASE 5: Merging audio + video...")
    phase_start = time.time()
    
    narration = merge_audio(video_script)
    if not narration:
        print("   ⚠️ No narration, returning raw video")
        return video_path
    
    mixed = os.path.join(video_script.output_dir, "mixed.mp3")
    final_audio = mix_bgm(narration, mixed)
    
    safe_name = topic.replace(" ", "_")[:25]
    timestamp = int(time.time())
    final_path = os.path.join(os.path.dirname(video_path), f"PRISM_{safe_name}_{timestamp}.mp4")
    
    final = merge_video_audio(video_path, final_audio, final_path)
    
    merge_time = time.time() - phase_start
    print(f"   ✅ Merged ({merge_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 6: CLEANUP
    # ═══════════════════════════════════════════════════════════
    if cleanup:
        cleanup_temp_files(video_script.output_dir)
        cleanup_temp_files(SCRIPT_DIR)
    
    # ═══════════════════════════════════════════════════════════
    # COMPLETE
    # ═══════════════════════════════════════════════════════════
    elapsed = time.time() - start
    
    print("\n" + "═" * 60)
    print("   🎉 VIDEO COMPLETE!")
    print("═" * 60)
    print(f"   📁 Output: {final}")
    print(f"   📊 Duration: {video_script.total_duration:.0f}s")
    print(f"   ⏱️  Total Time: {elapsed:.0f}s")
    print(f"   📈 Breakdown:")
    print(f"       RAG:          {rag_time:.1f}s")
    print(f"       Director:     {director_time:.1f}s")
    print(f"       Audio:        {audio_time:.1f}s")
    print(f"       Code Gen:     {code_time:.1f}s")
    print(f"       Render:       {render_time:.1f}s")
    print(f"       Merge:        {merge_time:.1f}s")
    print("═" * 60)
    
    return final


# ============== CLI ==============
def main():
    """CLI Entry Point."""
    print("\n" + "═" * 60)
    print("   🔮 PRISM v2.0 - Educational Video Generator")
    print("   Director → Cinematographer Architecture")
    print("═" * 60)
    
    topic = input("\n📝 Enter topic: ").strip()
    if not topic:
        topic = "Quadratic Formula"
        print(f"   Using default: {topic}")
    
    print("\n🎬 Quality options:")
    print("   l = 480p  (fastest, ~1 min)")
    print("   m = 720p  (recommended, ~2 min)")
    print("   h = 1080p (best, ~4 min)")
    quality = input("Select quality [l]: ").strip().lower()
    if quality not in ['l', 'm', 'h']:
        quality = 'l'
    
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
        print("\n❌ Video generation failed.")


# ============== API ==============
def generate_video(topic: str, quality: str = "l", cleanup: bool = True) -> str:
    """
    Programmatic API for video generation.
    
    Args:
        topic: Educational topic
        quality: 'l' (480p), 'm' (720p), 'h' (1080p)
        cleanup: Remove temp files after success
        
    Returns:
        Path to generated video
    """
    return run_pipeline(topic, quality=quality, cleanup=cleanup)


# ============== ENTRY POINT ==============
if __name__ == "__main__":
    main()
