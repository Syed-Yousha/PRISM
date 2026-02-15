from manim import *
import numpy as np

class GenScene(Scene):
    def construct(self):
        # Section 1: Introduction
        title = Text("Circle Properties", color=WHITE).scale(0.8)
        title.to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=1.5)
        self.wait(1)

        intro_text = VGroup(
            Text("A circle is a set of points equidistant from", color=WHITE).scale(0.55),
            Text("a central point called the ", color=WHITE).scale(0.55),
            Text("center", color=YELLOW).scale(0.55),
            Text("The distance from center to any point is the", color=WHITE).scale(0.55),
            Text("radius", color=YELLOW).scale(0.55),
            MathTex(r"C = 2\pi r", color=WHITE).scale(0.65)
        ).arrange(DOWN, buff=0.35)
        intro_text.to_edge(LEFT, buff=1)

        # Right side visual
        circle = Circle(radius=1.5, color=BLUE)
        center_dot = Dot(color=YELLOW)
        radius_line = Line(ORIGIN, RIGHT * 1.5, color=WHITE)
        radius_label = Text("r", color=WHITE).scale(0.5)
        radius_label.next_to(radius_line, UP, buff=0.2)
        
        circle_group = VGroup(circle, center_dot, radius_line, radius_label)
        circle_group.shift(RIGHT * 3)

        self.play(FadeOut(title), run_time=0.5)
        self.play(Write(intro_text), run_time=2)
        self.play(
            Create(circle),
            FadeIn(center_dot),
            Create(radius_line),
            Write(radius_label),
            run_time=2
        )
        self.wait(17.9)

        # Section 2: Concept Explanation
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)

        concept_text = VGroup(
            Text("Key Circle Components:", color=WHITE).scale(0.55),
            Text("• Radius (r): distance from center to circle", color=WHITE).scale(0.55),
            Text("• Diameter (d): twice the radius (d = 2r)", color=WHITE).scale(0.55),
            Text("• Circumference (C): distance around circle", color=WHITE).scale(0.55),
            MathTex(r"C = 2\pi r", color=WHITE).scale(0.65)
        ).arrange(DOWN, buff=0.35)
        concept_text.to_edge(LEFT, buff=1)

        # Right side diagram
        circle2 = Circle(radius=2, color=BLUE)
        center_dot2 = Dot(color=YELLOW)
        radius_line2 = Line(ORIGIN, RIGHT * 2, color=RED)
        diameter_line = Line(LEFT * 2, RIGHT * 2, color=GREEN)
        
        labels = VGroup(
            Text("r", color=RED).scale(0.5),
            Text("d", color=GREEN).scale(0.5),
            Text("C", color=BLUE).scale(0.5)
        )
        
        labels[0].next_to(radius_line2, UP, buff=0.2)
        labels[1].next_to(diameter_line, DOWN, buff=0.2)
        labels[2].next_to(circle2, RIGHT, buff=0.2)

        diagram_group = VGroup(circle2, center_dot2, radius_line2, 
                             diameter_line, labels)
        diagram_group.shift(RIGHT * 3)

        self.play(Write(concept_text), run_time=2)
        self.play(
            Create(circle2),
            FadeIn(center_dot2),
            Create(radius_line2),
            Create(diameter_line),
            Write(labels),
            run_time=2
        )
        self.wait(21.2)

        # Section 3: Worked Example
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)

        example_text = VGroup(
            Text("Example:", color=WHITE).scale(0.55),
            Text("Find the circumference of a circle with", color=WHITE).scale(0.55),
            Text("radius = 4 cm", color=WHITE).scale(0.55),
            Text("Solution:", color=WHITE).scale(0.55),
            MathTex(r"C = 2\pi r", color=WHITE).scale(0.65),
            MathTex(r"C = 2\pi(4)", color=WHITE).scale(0.65),
            MathTex(r"C = 8\pi \text{ cm}", color=WHITE).scale(0.65)
        ).arrange(DOWN, buff=0.35)
        example_text.to_edge(LEFT, buff=1)

        # Right side example circle
        example_circle = Circle(radius=1.5, color=BLUE)
        example_radius = Line(ORIGIN, RIGHT * 1.5, color=RED)
        example_label = Text("r = 4 cm", color=WHITE).scale(0.5)
        example_label.next_to(example_radius, UP, buff=0.2)

        example_group = VGroup(example_circle, example_radius, example_label)
        example_group.shift(RIGHT * 3)

        # Answer box
        answer_box = SurroundingRectangle(example_text[-1], color=YELLOW)

        self.play(Write(example_text[:-1]), run_time=2)
        self.play(
            Create(example_circle),
            Create(example_radius),
            Write(example_label),
            run_time=2
        )
        self.play(Write(example_text[-1]), run_time=1)
        self.play(Create(answer_box), run_time=1)
        self.wait(26.3)