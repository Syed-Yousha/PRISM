from manim import *

class GenScene(Scene):
    def construct(self):
        self.camera.background_color = "#1e1e1e"

        # PRISM INTRO
        title = Text("PRISM", font_size=60, color=WHITE)
        subtitle = Text("AI Generated Education", font_size=30).next_to(title, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait(2)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # TOPIC SLIDE
        topic_title = Text("Neural Network", font_size=44, color=WHITE).to_edge(UP)
        topic_subtitle = Text("Introduction to Artificial Intelligence", font_size=28).next_to(topic_title, DOWN, buff=0.5)
        self.play(Write(topic_title))
        self.play(FadeIn(topic_subtitle))
        self.wait(2)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 1
        section1_title = Text("What is a Neural Network?", font_size=40, color=WHITE).to_edge(UP)
        section1_content = Text("A neural network is a computer system inspired by the structure and function of the human brain.", font_size=26)
        section1_content.scale_to_fit_width(10)
        section1_content.next_to(section1_title, DOWN, buff=0.8)
        section1_visual = Circle(radius=1, color=BLUE).next_to(section1_content, DOWN, buff=0.5)
        self.play(Write(section1_title))
        self.play(FadeIn(section1_content))
        self.play(Create(section1_visual))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 2
        section2_title = Text("How Does it Work?", font_size=40, color=WHITE).to_edge(UP)
        section2_content = Text("A neural network consists of layers of interconnected nodes or 'neurons' that process and transmit information.", font_size=26)
        section2_content.scale_to_fit_width(10)
        section2_content.next_to(section2_title, DOWN, buff=0.8)
        section2_visual = VGroup(
            Circle(radius=0.5, color=BLUE),
            Circle(radius=0.5, color=YELLOW),
            Circle(radius=0.5, color=BLUE)
        ).arrange(DOWN, buff=0.3).next_to(section2_content, DOWN, buff=0.5)
        self.play(Write(section2_title))
        self.play(FadeIn(section2_content))
        self.play(Create(section2_visual))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 3
        section3_title = Text("Types of Neural Networks", font_size=40, color=WHITE).to_edge(UP)
        section3_content = Text("There are several types of neural networks, including feedforward, recurrent, and convolutional neural networks.", font_size=26)
        section3_content.scale_to_fit_width(10)
        section3_content.next_to(section3_title, DOWN, buff=0.8)
        section3_visual = VGroup(
            Rectangle(width=2, height=1, color=BLUE),
            Rectangle(width=2, height=1, color=YELLOW),
            Rectangle(width=2, height=1, color=BLUE)
        ).arrange(DOWN, buff=0.3).next_to(section3_content, DOWN, buff=0.5)
        self.play(Write(section3_title))
        self.play(FadeIn(section3_content))
        self.play(Create(section3_visual))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SECTION 4
        section4_title = Text("Applications of Neural Networks", font_size=40, color=WHITE).to_edge(UP)
        section4_content = Text("Neural networks are used in a variety of applications, including image recognition, natural language processing, and speech recognition.", font_size=26)
        section4_content.scale_to_fit_width(10)
        section4_content.next_to(section4_title, DOWN, buff=0.8)
        section4_visual = MathTex(r"y = \sigma(Wx + b)").next_to(section4_content, DOWN, buff=0.5)
        self.play(Write(section4_title))
        self.play(FadeIn(section4_content))
        self.play(Write(section4_visual))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])

        # SUMMARY
        summary_title = Text("Key Takeaways", font_size=40, color=WHITE).to_edge(UP)
        summary_points = VGroup(
            Text("• Neural networks are computer systems inspired by the human brain", font_size=24),
            Text("• They consist of layers of interconnected nodes or 'neurons'", font_size=24),
            Text("• They are used in a variety of applications, including image recognition and natural language processing", font_size=24)
        ).arrange(DOWN, buff=0.3).next_to(summary_title, DOWN, buff=0.8)
        thanks = Text("Thanks for watching!", font_size=24).next_to(summary_points, DOWN, buff=0.5)
        self.play(Write(summary_title))
        self.play(FadeIn(summary_points))
        self.play(FadeIn(thanks))
        self.wait(3)
        self.play(*[FadeOut(mob) for mob in self.mobjects])