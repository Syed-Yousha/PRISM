import sys
import os
import json
import numpy as np

from manim import *

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

for path in (SCRIPT_DIR, PROJECT_ROOT):
    if path not in sys.path:
        sys.path.append(path)

from prism_lib.visuals.neural_net import PrismNeuralNetwork
from prism_lib.components import PrismSlide
from prism_lib.theme import BACKGROUND_COLOR, ACCENT_COLOR, TEXT_COLOR

# Load Data
DATA_PATH = os.path.join(PROJECT_ROOT, "data.json")
with open(DATA_PATH, "r") as f:
    SCENE_DATA = json.load(f)

class ConceptScene(MovingCameraScene): # Note: MovingCameraScene for zooms!
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        
        # 1. SETUP: Read Data
        title_text = SCENE_DATA.get("title", "Neural Network")
        layers = SCENE_DATA.get("layer_sizes", [3, 5, 2])
        inputs = SCENE_DATA.get("inputs", [1.0] * layers[0])
        expected_output = SCENE_DATA.get("expected_output", [0.0] * layers[-1])
        
        # 2. INTRO SLIDE
        slide = PrismSlide(title_text, "Simulating the flow of information.")
        self.play(slide.animate_intro())
        self.wait(0.5)

        # Slide floats to the left to clear space for the diagram
        self.play(
            slide.animate.scale(0.8).to_corner(UL, buff=0.8),
            run_time=1.2
        )

        overview = Paragraph(
            "Inputs fan out as we inject signals,",
            "hidden layers refine the message,",
            "and the outputs condense the story.",
            alignment="left",
            line_spacing=0.8,
            font_size=24,
        )
        overview.set_color(TEXT_COLOR)
        overview.set_width(slide.width * 0.85)
        overview.next_to(slide, DOWN, aligned_edge=LEFT, buff=0.3)
        self.play(FadeIn(overview, shift=UP * 0.2))

        # 3. SUMMON NETWORK WITH BACKDROP
        nn_panel = RoundedRectangle(corner_radius=0.3, width=7.5, height=5.5)
        nn_panel.set_stroke(ACCENT_COLOR, width=2, opacity=0.4)
        nn_panel.set_fill(ACCENT_COLOR, opacity=0.12)
        nn_panel.to_edge(RIGHT, buff=0.8)

        nn = PrismNeuralNetwork(layer_sizes=layers, layer_to_layer_buff=1.3)
        nn.scale(1.2)
        nn.move_to(nn_panel)

        network_label = Text("Neural Flow Diagram", font_size=28, color=TEXT_COLOR)
        network_label.next_to(nn_panel, UP, buff=0.3)

        self.play(FadeIn(nn_panel, shift=DOWN), FadeIn(network_label, shift=UP))
        self.play(nn.create(), run_time=2.5)

        # 4. ADD LABELS (The "Professional" Touch)
        input_label = Text("Input", font_size=22, color=GRAY).next_to(nn.layers[0], UP)
        output_label = Text("Output", font_size=22, color=GRAY).next_to(nn.layers[-1], UP)
        self.play(FadeIn(input_label), FadeIn(output_label))

        # 5. CAMERA ZOOM (Focus on the brain)
        self.play(
            self.camera.frame.animate.scale(0.9).move_to(nn_panel),
            run_time=2
        )

        # 6. SIMULATE DATA FLOW ACROSS ALL LAYERS
        def pulse_edges(edge_group: VGroup):
            packets = VGroup(*[
                Dot(color=ACCENT_COLOR, radius=0.06).move_to(edge.get_start())
                for edge in edge_group
            ])
            self.add(packets)
            self.play(
                LaggedStart(
                    *[MoveAlongPath(packet, edge, rate_func=linear) for packet, edge in zip(packets, edge_group)],
                    lag_ratio=0.01,
                    run_time=1.2,
                )
            )
            self.play(FadeOut(packets), run_time=0.3)

        for edge_group in nn.edge_groups:
            pulse_edges(edge_group)

        # 7. FINAL ACTIVATION HIGHLIGHT
        def fit_values(values, size):
            values = list(values)
            if len(values) >= size:
                return values[:size]
            return values + [0.2] * (size - len(values))

        activation_vectors = [fit_values(inputs, layers[0])]
        for size in layers[1:-1]:
            gradient = np.linspace(0.15, 0.9, size)
            activation_vectors.append(list(gradient))
        activation_vectors.append(fit_values(expected_output, layers[-1]))

        nn.set_activations(activation_vectors)

        highlight = SurroundingRectangle(nn.layers[-1], color=ACCENT_COLOR, buff=0.2)
        self.play(Create(highlight), run_time=1)
        self.wait(2)