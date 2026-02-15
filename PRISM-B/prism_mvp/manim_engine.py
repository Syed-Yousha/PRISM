"""
PRISM Manim Engine — Code Generator & Renderer
================================================
Uses Claude 3.5 Sonnet (via OpenRouter) for Manim code generation
with auto-repair loop on render failure.

Design: Strict split-screen — text LEFT, visuals RIGHT,
title centered top, BLACK background, no overlapping.
"""

import os
import re
import time
import subprocess
from typing import Optional

from openai import OpenAI

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    SCRIPT_DIR,
    MEDIA_DIR,
    GENERATED_SCRIPT_PATH,
    RENDER_QUALITY,
    QUALITY_PRESETS,
)

# ─────────────────────────────────────────────────────────
# System prompt — strict split-screen educational layout
# ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are an expert Manim Community Edition developer.
Your job is to produce a SINGLE Python file containing one Scene class
that animates an educational math video.

The screen is 14.2 × 8 Manim units (x ∈ [-7.1, 7.1], y ∈ [-4, 4]).

══════════════  STRICT SPLIT-SCREEN LAYOUT  ══════════════

1. SCREEN PARTITION — imagine a vertical line at x = 0:

   ┌──────────────┬──────────────┐
   │  LEFT HALF   │  RIGHT HALF  │
   │  x < -2      │  x > 2       │
   │              │              │
   │  ALL TEXT:   │  ALL VISUALS:│
   │  • Titles    │  • Shapes    │
   │  • Formulas  │  • Diagrams  │
   │  • Bullets   │  • Graphs    │
   │  • Steps     │  • Drawings  │
   └──────────────┴──────────────┘

2. POSITIONING CODE (mandatory patterns):

   # Text on the LEFT:
   text_group = VGroup(text1, text2, ...).arrange(DOWN, buff=0.35)
   text_group.to_edge(LEFT, buff=1)

   # Visuals on the RIGHT:
   visual_group = VGroup(shape, labels, ...).arrange(DOWN, buff=0.3)
   visual_group.to_edge(RIGHT, buff=1)

   ⛔ FORBIDDEN: move_to(ORIGIN) when both text AND visuals are on screen.
   ⛔ FORBIDDEN: placing text and shapes at the same x-coordinate.

3. TITLE — the ONLY element that may be centered:
   title = Text("Topic Name", color=WHITE).scale(0.8)
   title.to_edge(UP, buff=0.4)
   (Title spans the full width; FadeOut the title before the split content.)

4. COLLISION AVOIDANCE (CRITICAL):
   • NEVER place Text/MathTex on top of Lines, Polygons, or shapes.
   • For shape labels, ALWAYS use next_to with a direction vector:
       label.next_to(shape, UP, buff=0.25)
       side_label.next_to(line.get_center(), LEFT, buff=0.2)
   • NEVER use absolute coordinates (move_to) for labels near shapes.
   • For triangle / polygon side labels, use the midpoint of each side:
       mid = (vertex_a + vertex_b) / 2
       label.next_to(Dot(point=mid), direction, buff=0.2)

══════════════  TYPOGRAPHY  ══════════════

Background : Pure BLACK (#000000) — the Manim default. Never change it.
Title      : WHITE, .scale(0.8)
Body text  : WHITE, .scale(0.55)
Key terms  : YELLOW only — never another highlight color for text.
Math       : MathTex / Tex in WHITE, .scale(0.65)
Answers    : Surrounded by a YELLOW SurroundingRectangle.
Shape colors: BLUE, GREEN, RED, ORANGE as needed.

══════════════  ANIMATION FLOW  ══════════════

Per section:
  1. FadeOut everything first:
       self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)
  2. Write the title (centered UP), wait briefly, then FadeOut the title.
  3. Write/FadeIn the text block on the LEFT.
  4. Create/GrowFromCenter the visual on the RIGHT.
  5. Use self.wait() + run_time to match the section's target duration.

Transitions: Write, FadeIn, FadeOut, Create, GrowFromCenter,
             TransformMatchingTex, ReplacementTransform.

══════════════  EDUCATIONAL QUALITY  ══════════════

Section 1 — Introduction:
  • Animate the topic title (centered).
  • Show the key formula/definition on the LEFT.
  • Optionally show a simple icon or shape on the RIGHT.

Section 2 — Concept Explanation:
  • Step-by-step text on the LEFT (numbered or bulleted).
  • Labeled diagram on the RIGHT — labels placed with next_to().
  • Highlight key terms in YELLOW.

Section 3 — Worked Example:
  • "Example:" header on the LEFT.
  • Problem statement + numbered solution steps on the LEFT.
  • Visual representation of the problem on the RIGHT.
  • Highlight the FINAL ANSWER with a YELLOW SurroundingRectangle.

══════════════  CODE RULES  ══════════════

1.  Output ONLY valid Python.  No markdown fences, no prose.
2.  First line: from manim import *
3.  Second line: import numpy as np
4.  Class name MUST be:  class GenScene(Scene):
5.  Use Scene (2-D), NOT ThreeDScene.
6.  Do NOT call self.set_camera_orientation or add_fixed_in_frame_mobjects.
7.  For multi-part math use separate strings:
        MathTex("a^2", "+", "b^2", "=", "c^2")
8.  Keep all text ≤ 50 chars per line — split into multiple Text/MathTex
    objects and stack with VGroup(...).arrange(DOWN, buff=0.3).
9.  Every self.play() call must have run_time=... explicitly set.
"""

# ─────────────────────────────────────────────────────────
# Auto-repair prompt sent when render fails
# ─────────────────────────────────────────────────────────
REPAIR_PROMPT = """\
The Manim code below failed to render.  Fix it and return ONLY the
corrected Python code — no explanation, no markdown.

Keep the same class name GenScene(Scene), keep the same visual content,
and use Manim Community Edition syntax.

ERROR:
{error}

CODE:
{code}
"""

class ManimEngine:
    """Generate Manim code via Claude 3.5 Sonnet (OpenRouter) and render it."""

    MAX_REPAIR_ATTEMPTS = 3

    def __init__(self) -> None:
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is missing — add it to .env")

        self._client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        self._model = OPENROUTER_MODEL

    # ── public entry point ───────────────────────────────
    def generate_and_render(
        self,
        video_script,
        rag_context: str = "",
    ) -> Optional[str]:
        """Generate code, save to generated_scene.py, render, auto-repair."""
        print(f"\n   🎬 Generating Manim code for: {video_script.topic}")

        user_prompt = self._build_user_prompt(video_script, rag_context)
        code = self._call_llm(SYSTEM_PROMPT, user_prompt, label="generate")

        if not code:
            print("   ❌ Code generation failed")
            return None

        code = self._post_process(code)
        self._save(code)

        # Render loop with auto-repair
        quality_flag = f"-q{RENDER_QUALITY}"
        quality_name = QUALITY_PRESETS.get(RENDER_QUALITY, ("480p15", 15))[0]

        for attempt in range(1 + self.MAX_REPAIR_ATTEMPTS):
            print(f"\n   🎥 Render attempt {attempt + 1}/{1 + self.MAX_REPAIR_ATTEMPTS}...")
            ok, error = self._render(quality_flag)

            if ok:
                video = self._find_video(quality_name)
                if video:
                    print(f"   ✅ Render successful: {video}")
                    return video

            # Auto-repair via Claude
            if attempt < self.MAX_REPAIR_ATTEMPTS:
                print(f"   ❌ Render error — sending to Claude for repair...")
                current_code = self._read_script()
                repair_prompt = REPAIR_PROMPT.format(
                    error=error[-2000:],
                    code=current_code,
                )
                fixed = self._call_llm(SYSTEM_PROMPT, repair_prompt, label="repair")
                if fixed:
                    fixed = self._post_process(fixed)
                    self._save(fixed)
                    continue

            print(f"   ❌ Render failed: {error[:400]}")

        return None

    # ── prompt builder ───────────────────────────────────
    def _build_user_prompt(self, video_script, rag_context: str) -> str:
        sections = []
        for seg in video_script.segments:
            notes = seg.get_blackboard_notes_list()
            sections.append(
                f"--- SECTION {seg.id}: {seg.title} ---\n"
                f"Duration: {seg.duration:.1f}s\n"
                f'Narration: "{seg.narration}"\n'
                f"Notes: {notes}\n"
                f"Visuals: {seg.visual_instructions}\n"
            )

        rag_block = rag_context[:5000] if rag_context else "(none)"

        return (
            f'Topic: "{video_script.topic}"\n\n'
            f"SECTIONS:\n{''.join(sections)}\n"
            f"Total duration: ~{video_script.total_duration:.1f}s\n\n"
            f"REQUIREMENTS:\n"
            f"1. The last section MUST have at least ONE fully worked example with step-by-step solution.\n"
            f"2. Highlight the final answer with a YELLOW SurroundingRectangle.\n"
            f"3. FadeOut ALL objects before each new section.\n"
            f"4. Match each section's target duration with self.wait() and run_time.\n\n"
            f"REFERENCE CODE PATTERNS:\n{rag_block}\n\n"
            f"OUTPUT: Python code only."
        )

    # ── LLM call (Claude via OpenRouter) ─────────────────
    def _call_llm(
        self,
        system: str,
        user: str,
        *,
        label: str = "call",
    ) -> Optional[str]:
        try:
            t0 = time.time()
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
                max_tokens=8192,
            )
            raw = resp.choices[0].message.content or ""
            elapsed = time.time() - t0
            print(f"   🤖 Claude [{label}] → {len(raw)} chars in {elapsed:.1f}s")
            return self._extract_code(raw)
        except Exception as exc:
            print(f"   ❌ Claude API error ({label}): {exc}")
            return None

    # ── code extraction / cleanup ────────────────────────
    @staticmethod
    def _extract_code(raw: str) -> Optional[str]:
        if not raw:
            return None
        text = raw.strip()
        # Strip markdown fences
        text = re.sub(r"^```(?:python)?\s*\n?", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n?```\s*$", "", text, flags=re.MULTILINE)
        text = text.strip()
        if not text:
            return None
        # Ensure manim import present
        if "from manim import" not in text:
            text = "from manim import *\nimport numpy as np\n\n" + text
        return text

    @staticmethod
    def _post_process(code: str) -> str:
        # Fix Dot(ORIGIN) → Dot(point=ORIGIN)
        code = re.sub(
            r"Dot\((?!point=)((?:ORIGIN|UP|DOWN|LEFT|RIGHT|np\.array|\[))",
            r"Dot(point=\1",
            code,
        )
        # Ensure class name is GenScene(Scene) — NOT ThreeDScene
        code = re.sub(
            r"class\s+GenScene\s*\(\s*ThreeDScene\s*\)",
            "class GenScene(Scene)",
            code,
        )
        return code

    # ── file I/O ─────────────────────────────────────────
    @staticmethod
    def _save(code: str) -> None:
        with open(GENERATED_SCRIPT_PATH, "w", encoding="utf-8") as fh:
            fh.write(code)
        print(f"   💾 Saved → {GENERATED_SCRIPT_PATH}")

    @staticmethod
    def _read_script() -> str:
        try:
            with open(GENERATED_SCRIPT_PATH, "r", encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── rendering ────────────────────────────────────────
    @staticmethod
    def _render(quality_flag: str) -> tuple:
        """Run manim render.  Returns (success: bool, stderr: str)."""
        cmd = [
            "manim", "render",
            quality_flag,
            GENERATED_SCRIPT_PATH,
            "GenScene",
            "--disable_caching",
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=SCRIPT_DIR,
            )
            if result.returncode == 0:
                return True, ""
            return False, result.stderr or "Unknown render error"
        except subprocess.TimeoutExpired:
            return False, "Render timed out (300s)"
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _find_video(quality_name: str) -> Optional[str]:
        video_dir = os.path.join(
            MEDIA_DIR, "videos", "generated_scene", quality_name,
        )
        if not os.path.isdir(video_dir):
            return None
        for fname in os.listdir(video_dir):
            if fname.endswith(".mp4"):
                return os.path.join(video_dir, fname)
        return None
