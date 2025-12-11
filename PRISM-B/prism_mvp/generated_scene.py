from manim import *

class GenScene(Scene):
    def construct(self):
        # PRISM Branding
        branding = Text("PRISM", font_size=48, color=WHITE)
        ai_gen = Text("AI Generated", font_size=28, color=WHITE)
        branding.to_edge(UP)
        ai_gen.next_to(branding, DOWN)
        self.play(Write(branding), Write(ai_gen))
        self.wait(2)
        self.play(FadeOut(branding), FadeOut(ai_gen))

        # Title
        title = Text("Binary Language", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(2)

        # Content
        binary_text = Text("Binary: 0s and 1s", font_size=28, color="#ece6e2")
        binary_text.next_to(title, DOWN)
        self.play(Write(binary_text))

        zero = Circle(radius=0.2, color=BLUE, fill_opacity=1)
        one = Circle(radius=0.2, color=BLUE, fill_opacity=1)
        zero.next_to(binary_text, DOWN)
        one.next_to(zero, RIGHT)
        self.play(Create(zero), Create(one))

        arrow = Arrow(start=zero.get_center(), end=one.get_center(), color=BLUE)
        self.play(Create(arrow))

        binary_code = Text("101010", font_size=28, color="#ece6e2")
        binary_code.next_to(arrow, DOWN)
        self.play(Write(binary_code))

        self.wait(2)

        # Summary
        summary = Text("Binary Language: 0s and 1s", font_size=28, color="#ece6e2")
        summary.to_edge(DOWN)
        self.play(FadeIn(summary))
        self.wait(2)
        self.play(FadeOut(summary), FadeOut(title), FadeOut(binary_text), FadeOut(zero), FadeOut(one), FadeOut(arrow), FadeOut(binary_code))