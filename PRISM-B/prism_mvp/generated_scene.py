from manim import *

class GenScene(Scene):
    def construct(self):
        self.camera.background_color = "#1e1e1e"

        # PRISM INTRO (5 sec)
        title = Text("PRISM", font_size=60, color=WHITE)
        subtitle = Text("AI Generated Education", font_size=30, color="#ece6e2").next_to(title, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait(2)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # TOPIC SLIDE (5 sec)
        title = Text("Black Holes", font_size=48, color=WHITE).to_edge(UP)
        subtitle = Text("A Cosmic Enigma", font_size=30, color="#ece6e2").next_to(title, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait(2)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 1 (12 sec)
        title = Text("What is a Black Hole?", font_size=40, color=WHITE).to_edge(UP)
        explanation = Text("A black hole is a region in space where the gravitational pull is so strong that nothing, not even light, can escape.", font_size=26, color="#ece6e2")
        explanation.scale_to_fit_width(10)
        explanation.next_to(title, DOWN, buff=0.8)
        visual = Circle(radius=1, color=BLUE).next_to(explanation, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(FadeIn(explanation))
        self.play(Create(visual))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 2 (12 sec)
        title = Text("Formation of Black Holes", font_size=40, color=WHITE).to_edge(UP)
        explanation = Text("Black holes are formed when a massive star collapses in on itself.", font_size=26, color="#ece6e2")
        explanation.scale_to_fit_width(10)
        explanation.next_to(title, DOWN, buff=0.8)
        diagram = VGroup(
            Circle(radius=1, color=YELLOW),
            Circle(radius=0.5, color=BLUE).next_to(Circle(radius=1, color=YELLOW), IN, buff=0)
        ).next_to(explanation, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(FadeIn(explanation))
        self.play(Create(diagram))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 3 (12 sec)
        title = Text("Properties of Black Holes", font_size=40, color=WHITE).to_edge(UP)
        explanation = Text("Black holes have three main properties: mass, charge, and angular momentum.", font_size=26, color="#ece6e2")
        explanation.scale_to_fit_width(10)
        explanation.next_to(title, DOWN, buff=0.8)
        visual = VGroup(
            Text("Mass", font_size=24, color=YELLOW),
            Text("Charge", font_size=24, color=BLUE),
            Text("Angular Momentum", font_size=24, color=YELLOW)
        ).arrange(DOWN, buff=0.3).next_to(explanation, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(FadeIn(explanation))
        self.play(FadeIn(visual))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 4 (10 sec)
        title = Text("Event Horizon", font_size=40, color=WHITE).to_edge(UP)
        equation = MathTex(r"r = \frac{2GM}{c^2}").next_to(title, DOWN, buff=0.8)
        explanation = Text("The event horizon is the point of no return around a black hole.", font_size=26, color="#ece6e2").next_to(equation, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(Write(equation))
        self.play(FadeIn(explanation))
        self.wait(2)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SUMMARY (8 sec)
        title = Text("Key Takeaways", font_size=40, color=WHITE).to_edge(UP)
        bullets = VGroup(
            Text("• Black holes are regions with strong gravitational pull", font_size=24, color="#ece6e2"),
            Text("• Formed by massive star collapse", font_size=24, color="#ece6e2"),
            Text("• Have mass, charge, and angular momentum properties", font_size=24, color="#ece6e2")
        ).arrange(DOWN, buff=0.3).next_to(title, DOWN, buff=0.8)
        thanks = Text("Thanks for watching!", font_size=24, color=YELLOW).next_to(bullets, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(FadeIn(bullets))
        self.play(FadeIn(thanks))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])