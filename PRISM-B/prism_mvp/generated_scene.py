"""
PRISM Generated Scene - Audio-Synced
=====================================
Topic: Fractions
Sections: 6
Generated: 2026-01-18 17:00:29
Style: Khan Academy / 3Blue1Brown
"""

from manim import *
import numpy as np

config.background_color = "#1e1e1e"


class GenScene(Scene):
    """Auto-generated educational animation with clean 2D layout."""
    
    def construct(self):

        # ════════════════════════════════════════════════════════════
        # SECTION 1: INTRODUCTION TO FRACTIONS (10.6s)
        # Type: hook
        # ════════════════════════════════════════════════════════════
        title = Text("Introduction to Fractions", font_size=40, color=YELLOW)
        title.to_edge(UP, buff=0.5)

        formula = MathTex(r"\frac{a}{b}", font_size=44)
        formula.move_to(ORIGIN)

        notes = VGroup()
        for note in ['Part of a whole', 'Numerator and denominator']:
            notes.add(Text(note, font_size=24, color=TEAL))
        notes.arrange(RIGHT, buff=0.8)
        notes.to_edge(DOWN, buff=0.5)

        self.play(Write(title), run_time=1.5)
        self.play(Write(formula), run_time=1.5)
        self.play(Write(notes), run_time=0.8)
        self.wait(10.6 - 3.8)


        # ════════════════════════════════════════════════════════════
        # SECTION 2: FRACTION NOTATION (7.5s)
        # Type: formula
        # ════════════════════════════════════════════════════════════
        # Clear previous content for clean slate
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

        # Create title
        title = Text("Fraction Notation", font_size=40, color=YELLOW)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.0)

        # Create formula
        formula = MathTex(r"a/b", font_size=44)
        formula.move_to(ORIGIN)
        self.play(Write(formula), run_time=1.5)

        # Create notes
        notes = VGroup()
        for note in ['Numerator', 'Denominator', 'Fraction notation']:
            notes.add(Text(note, font_size=24, color=TEAL))
        notes.arrange(RIGHT, buff=0.8)
        notes.to_edge(DOWN, buff=0.5)
        self.play(Write(notes), run_time=0.8)

        # Indicate numerator and denominator
        numerator = Text("Numerator", font_size=24, color=TEAL)
        numerator.next_to(formula, UP, buff=0.2)
        denominator = Text("Denominator", font_size=24, color=TEAL)
        denominator.next_to(formula, DOWN, buff=0.2)
        self.play(Write(numerator), Write(denominator), run_time=1.0)

        # Fill remaining time
        self.wait(2.2)


        # ════════════════════════════════════════════════════════════
        # SECTION 3: UNDERSTANDING FRACTIONS (7.8s)
        # Type: breakdown
        # ════════════════════════════════════════════════════════════
        # Clear previous content for clean slate
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

        # Title
        title = Text("Understanding Fractions", font_size=40, color=YELLOW)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.0)

        # Main content
        main_content = Text("To understand fractions, we need to consider the relationship between the numerator and the denominator.", font_size=28)
        main_content.move_to(ORIGIN)
        self.play(Write(main_content), run_time=2.3)

        # Blackboard Notes
        notes = VGroup()
        for note in ['Equal parts', 'Comparing fractions']:
            notes.add(Text(note, font_size=24, color=TEAL))
        notes.arrange(RIGHT, buff=0.8)
        notes.to_edge(DOWN, buff=0.5)
        self.play(Write(notes), run_time=0.8)

        # Fill remaining time
        self.wait(7.8 - 0.5 - 1.0 - 2.3 - 0.8 - 0.2)  # 3.2 seconds remaining


        # ════════════════════════════════════════════════════════════
        # SECTION 4: ADDING FRACTIONS (4.9s)
        # Type: example
        # ════════════════════════════════════════════════════════════
        # Clear previous content for clean slate
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

        # Title
        title = Text("Adding Fractions", font_size=40, color=YELLOW)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.8)

        # Main content
        formula = MathTex(r"\frac{a}{b} + \frac{c}{d} = \frac{ad + bc}{bd}", font_size=44)
        formula.move_to(ORIGIN)
        self.play(Write(formula), run_time=1.5)

        # Notes
        notes = VGroup()
        for note in ['Common denominator', 'Adding fractions']:
            notes.add(Text(note, font_size=24, color=TEAL))
        notes.arrange(RIGHT, buff=0.8)
        notes.to_edge(DOWN, buff=0.5)
        self.play(Write(notes), run_time=0.8)

        # Fill remaining time
        self.wait(1.1)


        # ════════════════════════════════════════════════════════════
        # SECTION 5: FRACTION VISUALIZATION (5.6s)
        # Type: visualization
        # ════════════════════════════════════════════════════════════
        # Clear previous content for clean slate
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

        # Create title
        title = Text("Fraction Visualization", font_size=40, color=YELLOW)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.0)

        # Create main content
        main_content = Text("Visualizing fractions can help us better understand their relationships.", font_size=44)
        main_content.move_to(ORIGIN)
        self.play(Write(main_content), run_time=1.5)

        # Create notes
        notes = VGroup()
        for note in ['Visualizing fractions', 'Circle representation']:
            notes.add(Text(note, font_size=24, color=TEAL))
        notes.arrange(RIGHT, buff=0.8)
        notes.to_edge(DOWN, buff=0.5)
        self.play(Write(notes), run_time=0.8)

        # Calculate remaining time
        remaining_time = 5.6 - 0.5 - 1.0 - 1.5 - 0.8
        self.wait(remaining_time)


        # ════════════════════════════════════════════════════════════
        # SECTION 6: SUMMARY OF FRACTIONS (7.6s)
        # Type: summary
        # ════════════════════════════════════════════════════════════
        # Clear previous content for clean slate
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)

        # Title
        title = Text("Summary of Fractions", font_size=40, color=YELLOW)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.0)

        # Main content
        main_content = Text("Fractions represent a part of a whole", font_size=44)
        main_content.move_to(ORIGIN)
        self.play(Write(main_content), run_time=2.0)

        # Notes
        notes = VGroup()
        for note in ['Fractions', 'Part of a whole']:
            notes.add(Text(note, font_size=24, color=TEAL))
        notes.arrange(RIGHT, buff=0.8)
        notes.to_edge(DOWN, buff=0.5)
        self.play(Write(notes), run_time=0.8)

        # Fill remaining time
        self.wait(7.6 - 0.5 - 1.0 - 2.0 - 0.8 - 0.5)

        # ═══════════════════════════════════════════════════════════
        # END - Cleanup
        # ═══════════════════════════════════════════════════════════
        self.wait(0.5)
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=1.0)
