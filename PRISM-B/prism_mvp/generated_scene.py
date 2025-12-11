from manim import *

class GenScene(Scene):
    def construct(self):
        # Set background color
        self.camera.background_color = "#1e1e1e"

        # PRISM INTRO (5 sec)
        title = Text("PRISM", font_size=60, color=WHITE)
        subtitle = Text("AI Generated Education", font_size=30, color="#ece6e2").next_to(title, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait(2)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # TOPIC SLIDE (5 sec)
        topic_title = Text("Photosynthesis", font_size=48, color=WHITE).to_edge(UP)
        topic_subtitle = Text("The Process of Plant Growth", font_size=28, color="#ece6e2").next_to(topic_title, DOWN, buff=0.5)
        self.play(Write(topic_title))
        self.play(FadeIn(topic_subtitle))
        self.wait(2)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 1 (12 sec)
        section1_title = Text("Introduction to Photosynthesis", font_size=40, color=WHITE).to_edge(UP)
        section1_content = Text("Photosynthesis is the process by which plants, algae, and some bacteria convert light energy from the sun into chemical energy in the form of organic compounds.", font_size=24, color="#ece6e2")
        section1_content.scale_to_fit_width(10)
        section1_content.next_to(section1_title, DOWN, buff=0.8)
        section1_visual = Circle(radius=1, color=BLUE).next_to(section1_content, DOWN, buff=0.5)
        self.play(Write(section1_title))
        self.play(FadeIn(section1_content))
        self.play(Create(section1_visual))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 2 (12 sec)
        section2_title = Text("The Photosynthetic Equation", font_size=40, color=WHITE).to_edge(UP)
        section2_equation = MathTex(r"6CO_2 + 6H_2O + light\ energy \rightarrow C_6H_{12}O_6 + 6O_2", font_size=24)
        section2_equation.next_to(section2_title, DOWN, buff=0.8)
        section2_visual = VGroup(
            Circle(radius=0.5, color=YELLOW),
            Circle(radius=0.5, color=BLUE)
        ).arrange(RIGHT, buff=0.5).next_to(section2_equation, DOWN, buff=0.5)
        self.play(Write(section2_title))
        self.play(Write(section2_equation))
        self.play(Create(section2_visual))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 3 (12 sec)
        section3_title = Text("The Role of Chlorophyll", font_size=40, color=WHITE).to_edge(UP)
        section3_content = Text("Chlorophyll is a green pigment found in the chloroplasts of plants, algae, and cyanobacteria. It plays a crucial role in absorbing light energy for photosynthesis.", font_size=24, color="#ece6e2")
        section3_content.scale_to_fit_width(10)
        section3_content.next_to(section3_title, DOWN, buff=0.8)
        section3_visual = Rectangle(width=2, height=1, color=GREEN).next_to(section3_content, DOWN, buff=0.5)
        self.play(Write(section3_title))
        self.play(FadeIn(section3_content))
        self.play(Create(section3_visual))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 4 (10 sec)
        section4_title = Text("The Importance of Water", font_size=40, color=WHITE).to_edge(UP)
        section4_equation = MathTex(r"H_2O + CO_2 \rightarrow glucose + O_2", font_size=24)
        section4_equation.next_to(section4_title, DOWN, buff=0.8)
        section4_visual = Circle(radius=0.5, color=BLUE).next_to(section4_equation, DOWN, buff=0.5)
        self.play(Write(section4_title))
        self.play(Write(section4_equation))
        self.play(Create(section4_visual))
        self.wait(2)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SUMMARY (8 sec)
        summary_title = Text("Key Takeaways", font_size=40, color=WHITE).to_edge(UP)
        summary_bullets = VGroup(
            Text("• Photosynthesis is the process of converting light energy into chemical energy", font_size=24, color="#ece6e2"),
            Text("• Chlorophyll plays a crucial role in absorbing light energy", font_size=24, color="#ece6e2"),
            Text("• Water is essential for photosynthesis", font_size=24, color="#ece6e2")
        ).arrange(DOWN, buff=0.4).next_to(summary_title, DOWN, buff=0.8)
        thanks = Text("Thanks for watching!", font_size=24, color="#ece6e2").next_to(summary_bullets, DOWN, buff=0.5)
        self.play(Write(summary_title))
        self.play(FadeIn(summary_bullets))
        self.play(FadeIn(thanks))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])