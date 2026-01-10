"""
PRISM Generated Scene
=====================
Topic: Linear equations
Sections: 6
Generated: 2026-01-10 21:03:37
Style: Khan Academy / 3Blue1Brown
"""

from manim import *
import numpy as np

config.background_color = "#000000"


class GenScene(ThreeDScene):
    """Auto-generated educational animation."""
    
    def construct(self):
        # 2D camera setup
        self.set_camera_orientation(phi=0*DEGREES, theta=-90*DEGREES)
        

        # ════════════════════════════════════════════════════════════
        # SECTION 1: THE POWER OF LINES (13.7s) [FALLBACK]
        # ════════════════════════════════════════════════════════════

        # Title
        title = Text("The Power of Lines", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # Hook visual - engaging question mark
        hook_text = Text("?", font_size=144, color=YELLOW)
        hook_text.move_to(ORIGIN)
        self.play(Write(hook_text), run_time=1.0)
        self.play(hook_text.animate.scale(1.3), run_time=0.5)
        self.play(hook_text.animate.scale(1/1.3), run_time=0.3)
        self.play(FadeOut(hook_text), run_time=0.5)
        
        self.wait(9.2)


        # ════════════════════════════════════════════════════════════
        # SECTION 2: THE FORMULA (9.5s) [FALLBACK]
        # ════════════════════════════════════════════════════════════

        # Clear previous
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

        # Title
        title = Text("The Formula", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # Main formula - centered and prominent
        formula = MathTex(r"f(x) = ax^2 + bx + c", font_size=56, color=WHITE)
        formula.move_to(ORIGIN)
        box = SurroundingRectangle(formula, color=BLUE, buff=0.3)
        self.play(Write(formula), run_time=2.0)
        self.play(Create(box), run_time=0.5)
        self.play(Indicate(formula, color=YELLOW), run_time=0.8)
        
        self.wait(5.0)


        # ════════════════════════════════════════════════════════════
        # SECTION 3: UNDERSTANDING EACH PART (13.2s) [FALLBACK]
        # ════════════════════════════════════════════════════════════

        # Clear previous
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

        # Title
        title = Text("Understanding Each Part", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # Breakdown - color-coded parts
        eq = MathTex(r"a", r"x^2", r"+", r"b", r"x", r"+", r"c", font_size=56)
        eq[0].set_color(BLUE)
        eq[3].set_color(YELLOW)
        eq[6].set_color(TEAL)
        eq.move_to(ORIGIN)
        self.play(Write(eq), run_time=1.5)
        self.play(Indicate(eq[0], color=BLUE, scale_factor=1.3), run_time=0.5)
        self.play(Indicate(eq[3], color=YELLOW, scale_factor=1.3), run_time=0.5)
        self.play(Indicate(eq[6], color=TEAL, scale_factor=1.3), run_time=0.5)
        
        self.wait(8.7)


        # ════════════════════════════════════════════════════════════
        # SECTION 4: WORKED EXAMPLE (11.6s) [FALLBACK]
        # ════════════════════════════════════════════════════════════

        # Clear previous
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

        # Title
        title = Text("Worked Example", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # Worked example - step by step
        step1 = MathTex(r"x^2 + 5x + 6 = 0", font_size=44, color=WHITE)
        step1.move_to(UP * 0.5)
        self.play(Write(step1), run_time=1.2)
        
        step2 = MathTex(r"x = -2", font_size=48, color=GREEN)
        step3 = MathTex(r"x = -3", font_size=48, color=GREEN)
        answers = VGroup(step2, step3).arrange(RIGHT, buff=1.5)
        answers.move_to(DOWN * 1)
        self.play(Write(step2), run_time=0.8)
        self.play(Write(step3), run_time=0.8)
        
        box = SurroundingRectangle(answers, color=GREEN, buff=0.3)
        self.play(Create(box), run_time=0.5)
        
        self.wait(7.1)


        # ════════════════════════════════════════════════════════════
        # SECTION 5: SEE IT GRAPHICALLY (13.2s) [FALLBACK]
        # ════════════════════════════════════════════════════════════

        # Clear previous
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

        # Title
        title = Text("See It Graphically", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # Graph - centered axes with curve
        axes = Axes(
            x_range=[-4, 4, 1], y_range=[-2, 8, 2],
            x_length=6, y_length=4,
            axis_config={"color": WHITE, "include_tip": True}
        ).move_to(ORIGIN)
        curve = axes.plot(lambda x: x**2, color=BLUE, x_range=[-2.5, 2.5])
        label = MathTex(r"y = x^2", font_size=32, color=BLUE).next_to(curve, UR)
        self.add_fixed_in_frame_mobjects(label)
        self.play(Create(axes), run_time=1.0)
        self.play(Create(curve), run_time=1.5)
        self.play(Write(label), run_time=0.5)
        
        self.wait(8.7)


        # ════════════════════════════════════════════════════════════
        # SECTION 6: KEY TAKEAWAYS (11.5s) [FALLBACK]
        # ════════════════════════════════════════════════════════════

        # Clear previous
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

        # Title
        title = Text("Key Takeaways", font_size=44, color=YELLOW)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.0)

        # Summary - clean bullet points centered
        p1 = Text("• Key concept learned", font_size=28, color=WHITE)
        p2 = Text("• Formula applied", font_size=28, color=WHITE)
        p3 = Text("• Example solved", font_size=28, color=WHITE)
        points = VGroup(p1, p2, p3).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        points.move_to(ORIGIN)
        self.add_fixed_in_frame_mobjects(p1, p2, p3)
        self.play(Write(p1), run_time=0.7)
        self.play(Write(p2), run_time=0.7)
        self.play(Write(p3), run_time=0.7)
        
        self.wait(7.0)

        # ═══════════════════════════════════════════════════════════
        # END - Cleanup
        # ═══════════════════════════════════════════════════════════
        self.wait(0.5)
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=1.0)
