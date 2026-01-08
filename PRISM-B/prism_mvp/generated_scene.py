"""
PRISM Generated Scene
Topic: Quadratic Formula
Generated: 2026-01-08 08:42:39
Segments: 4
Total Duration: 36.0s
"""

from manim import *
import numpy as np

# Scene configuration
config.background_color = "#0a0a0a"


class GenScene(ThreeDScene):
    """Auto-generated educational animation."""
    
    def construct(self):

        # ═══════════════════════════════════════════════════════════
        # SEGMENT 1: Introduction (9.9s, 2D)
        # Type: hook
        # ═══════════════════════════════════════════════════════════
        self.set_camera_orientation(phi=0*DEGREES, theta=-90*DEGREES)
        # Title
        title = Tex(r"\textbf{Introduction}", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)

        shape = Circle(radius=1.5, color=BLUE, fill_opacity=0.3)
        shape.move_to(RIGHT * 2.5)
        self.play(Create(shape), run_time=1.5)

        self.wait(6.4)

        # ═══════════════════════════════════════════════════════════
        # SEGMENT 2: Core Concept (8.6s, 2D)
        # Type: concept
        # ═══════════════════════════════════════════════════════════
        # Clear previous
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.3)

        # Title
        title = Tex(r"\textbf{Core Concept}", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)

        shape = Circle(radius=1.5, color=BLUE, fill_opacity=0.3)
        shape.move_to(RIGHT * 2.5)
        self.play(Create(shape), run_time=1.5)

        self.wait(5.1)

        # ═══════════════════════════════════════════════════════════
        # SEGMENT 3: Example (7.2s, 2D)
        # Type: example
        # ═══════════════════════════════════════════════════════════
        # Clear previous
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.3)

        # Title
        title = Tex(r"\textbf{Example}", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)

        shape = Circle(radius=1.5, color=BLUE, fill_opacity=0.3)
        shape.move_to(RIGHT * 2.5)
        self.play(Create(shape), run_time=1.5)

        self.wait(3.7)

        # ═══════════════════════════════════════════════════════════
        # SEGMENT 4: Summary (10.3s, 2D)
        # Type: summary
        # ═══════════════════════════════════════════════════════════
        # Clear previous
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.3)

        # Title
        title = Tex(r"\textbf{Summary}", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)

        shape = Circle(radius=1.5, color=BLUE, fill_opacity=0.3)
        shape.move_to(RIGHT * 2.5)
        self.play(Create(shape), run_time=1.5)

        self.wait(6.8)

        # ═══════════════════════════════════════════════════════════
        # END - Cleanup
        # ═══════════════════════════════════════════════════════════
        self.wait(0.3)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)
