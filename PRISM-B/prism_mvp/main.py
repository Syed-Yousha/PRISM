"""
PRISM - Audio-First Video Generator
====================================
TWO-STEP LLM ARCHITECTURE:

┌─────────────────────────────────────────────────────────────────┐
│                    PRISM v3.1 PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   RAG        │      │  LLM STEP 1  │      │  LLM STEP 2  │  │
│  │  Knowledge   │─────>│   PROMPT     │─────>│    CODE      │  │
│  │   Fetch      │      │    MAKER     │      │  GENERATOR   │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                     │                      │          │
│   Manim Examples        AnimationScript         Manim Code     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Then: Audio Generation → Render → Merge                        │
└─────────────────────────────────────────────────────────────────┘

STEP 1 (PromptMaker): Topic + RAG → Detailed Animation Script
STEP 2 (ManimEngine): Animation Script → Executable Manim Code

WHY TWO STEPS:
- Step 1 focuses on PEDAGOGY and VISUAL PLANNING
- Step 2 focuses on CORRECT MANIM SYNTAX
- Separation of concerns = fewer errors!
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

from audio_engine import AudioEngine
from manim_engine import ManimEngine
from rag_engine import RAGEngine
from prompt_maker import PromptMaker, AnimationScript
from data_models import VideoScript
from config import (
    SCRIPT_DIR, MUSIC_DIR, RENDER_QUALITY, BGM_VOLUME, BGM_URLS,
    GENERATED_SCRIPT_PATH, BGM_ENABLED
)

# Import Bespoke curator for verified Manim examples
try:
    from bespoke_curator import initialize_bespoke_database
    BESPOKE_AVAILABLE = True
except ImportError:
    BESPOKE_AVAILABLE = False


# ============== AUDIO HELPERS ==============
def get_bgm() -> Optional[str]:
    """Download or get cached background music."""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    path = os.path.join(MUSIC_DIR, "bgm.mp3")
    
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        return path
    
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
        except Exception:
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
    """Mix voiceover with background music (if enabled)."""
    # Check if BGM is disabled
    if not BGM_ENABLED:
        return voice_path
    
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
    
    TWO-STEP LLM ARCHITECTURE:
    1. RAG Fetch - Get working code examples
    2. LLM Step 1 (PromptMaker) - Generate detailed animation script
    3. Audio Generation - Create narration audio with exact durations
    4. LLM Step 2 (ManimEngine) - Generate Manim code from script
    5. Render - Execute Manim
    6. Merge - Combine audio + video + BGM
    """
    start = time.time()
    
    # Header
    quality_names = {'l': '480p', 'm': '720p', 'h': '1080p'}
    print("\n" + "═" * 60)
    print("   🔮 PRISM Video Generator v3.1")
    print("   Two-Step LLM Architecture")
    print("═" * 60)
    print(f"   📚 Topic: {topic}")
    print(f"   🎬 Quality: {quality} ({quality_names.get(quality, '720p')})")
    print("═" * 60)
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 1: RAG - Knowledge Fetch + Bespoke Database
    # ═══════════════════════════════════════════════════════════
    print("\n📚 PHASE 1: Loading knowledge base (RAG)...")
    phase_start = time.time()
    
    # Initialize Bespoke Manim database (verified examples)
    if BESPOKE_AVAILABLE:
        print("   🎬 Initializing Bespoke Manim database...")
        try:
            initialize_bespoke_database()
        except Exception as e:
            print(f"   ⚠️ Bespoke init failed: {e}")
    
    rag = RAGEngine()
    rag_context = rag.get_context(topic)
    
    rag_time = time.time() - phase_start
    print(f"   ✅ RAG complete ({len(rag_context):,} chars, {rag_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 2: LLM STEP 1 - Prompt Maker (Animation Script)
    # ═══════════════════════════════════════════════════════════
    print("\n📝 PHASE 2: LLM Step 1 - PromptMaker creating animation script...")
    phase_start = time.time()
    
    prompt_maker = PromptMaker()
    animation_script = prompt_maker.generate_prompt(topic, rag_context)
    
    if not animation_script or not animation_script.sections:
        print("   ❌ PromptMaker failed to create animation script")
        return ""
    
    promptmaker_time = time.time() - phase_start
    print(f"   ✅ Animation Script: {len(animation_script.sections)} sections (~{animation_script.total_duration}s)")
    
    # Show section details
    for section in animation_script.sections:
        print(f"      Section {section.get('id')}: {section.get('title')} ({section.get('type')})")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 3: AUDIO - Generate narration with exact durations
    # ═══════════════════════════════════════════════════════════
    print("\n🎤 PHASE 3: Generating audio narration...")
    phase_start = time.time()
    
    director = AudioEngine()
    # Convert AnimationScript to VideoScript format for audio generation
    video_script = director.generate_audio_from_script(topic, animation_script)
    
    if not video_script or not video_script.segments:
        print("   ❌ Audio generation failed")
        return ""
    
    audio_time = time.time() - phase_start
    print(f"   ✅ Audio: {video_script.total_duration:.1f}s total ({audio_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 4: LLM STEP 2 - Code Generator (Manim Code)
    # ═══════════════════════════════════════════════════════════
    print("\n🔧 PHASE 4: LLM Step 2 - ManimEngine generating code...")
    phase_start = time.time()
    
    engineer = ManimEngine(quality=quality)
    code = engineer.generate_from_script(animation_script, video_script)
    
    if not code:
        print("   ❌ Code Generator failed")
        return ""
    
    codegen_time = time.time() - phase_start
    print(f"   ✅ Code: {len(code):,} chars ({codegen_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 5: RENDER - Manim Execution (with retry)
    # ═══════════════════════════════════════════════════════════
    print("\n🎨 PHASE 5: Rendering video...")
    phase_start = time.time()
    
    video_path = engineer.render(code, topic)
    
    if not video_path or not os.path.exists(video_path):
        print(f"   ❌ Render failed. Debug: {GENERATED_SCRIPT_PATH}")
        return ""
    
    render_time = time.time() - phase_start
    print(f"   ✅ Rendered ({render_time:.1f}s)")
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 6: MERGE - Audio + Video + BGM
    # ═══════════════════════════════════════════════════════════
    print("\n🔧 PHASE 6: Merging audio + video...")
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
    # PHASE 7: CLEANUP
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
    print(f"   📈 Breakdown (2-Step LLM Pipeline):")
    print(f"       RAG:              {rag_time:.1f}s")
    print(f"       LLM Step 1:       {promptmaker_time:.1f}s  (PromptMaker)")
    print(f"       Audio Gen:        {audio_time:.1f}s")
    print(f"       LLM Step 2:       {codegen_time:.1f}s  (CodeGenerator)")
    print(f"       Render:           {render_time:.1f}s")
    print(f"       Merge:            {merge_time:.1f}s")
    print("═" * 60)
    
    # ═══════════════════════════════════════════════════════════
    # AUTO-OPEN VIDEO
    # ═══════════════════════════════════════════════════════════
    if final and os.path.exists(final):
        print(f"\n🎥 Opening video...")
        try:
            if sys.platform == "win32":
                os.startfile(final)
            elif sys.platform == "darwin":
                os.system(f'open "{final}"')
            else:
                os.system(f'xdg-open "{final}"')
        except Exception as e:
            print(f"   ⚠️ Could not auto-open video: {e}")
    
    return final


# ============== CLI ==============
def main():
    """CLI Entry Point."""
    print("\n" + "═" * 60)
    print("   🔮 PRISM v3.1 - Two-Step LLM Video Generator")
    print("   RAG → PromptMaker (Step 1) → CodeGenerator (Step 2)")
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


if __name__ == "__main__":
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
        video = run_pipeline(topic, quality='l')
    else:
        main()
