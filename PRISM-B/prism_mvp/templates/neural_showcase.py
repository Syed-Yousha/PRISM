import sys
import os

from manim import *

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

for path in (SCRIPT_DIR, PROJECT_ROOT):
    if path not in sys.path:
        sys.path.append(path)

from prism_lib.visuals.neural_net import PrismNeuralNetwork
from prism_lib.theme import BACKGROUND_COLOR, ACCENT_COLOR, PRIMARY_COLOR, TEXT_COLOR


class NeuralShowcase(Scene):
    """A focused neural-network animation for automated testing."""

    def construct(self) -> None:
        self.camera.background_color = BACKGROUND_COLOR

        title = Text("Neural Pulse Test", font_size=54, color=ACCENT_COLOR)
        subtitle = Text("Signals cascading through each layer", font_size=28, color=TEXT_COLOR)
        header = VGroup(title, subtitle).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        header.to_edge(UP, buff=0.6)

        network = PrismNeuralNetwork([4, 6, 6, 3], layer_to_layer_buff=1.4)
        network.scale(1.15)
        board = RoundedRectangle(corner_radius=0.3)
        board.set_width(network.width + 1.2)
        board.set_height(network.height + 1.2)
        board.set_stroke(PRIMARY_COLOR, width=2, opacity=0.4)
        board.set_fill(PRIMARY_COLOR, opacity=0.1)
        board.to_edge(DOWN, buff=0.8)
        network.move_to(board)

        caption = Text("Layer Diagnostics", font_size=30, color=TEXT_COLOR)
        caption.next_to(board, UP)

        self.play(Write(title), FadeIn(subtitle, shift=UP))
        self.play(FadeIn(board, shift=DOWN), FadeIn(caption, shift=UP))
        self.play(network.create(), run_time=2.5)

        # Highlight neurons in each layer for a lively effect
        for layer in network.layers:
            indicators = [Indicate(neuron, color=ACCENT_COLOR, scale_factor=1.1) for neuron in layer.neurons]
            self.play(LaggedStart(*indicators, lag_ratio=0.2), run_time=1.2)

        # Send pulses through the edges from left to right
        for idx in range(len(network.edge_groups)):
            anims = network.get_edge_propagation_animations(idx)
            self.play(*anims)

        # Final activation state + celebratory flash
        network.set_activations([
            [0.9, 0.6, 0.3, 0.7],
            [0.2, 0.4, 0.6, 0.8, 0.5, 0.3],
            [0.3, 0.7, 0.2, 0.9, 0.4, 0.6],
            [1.0, 0.2, 0.1],
        ])
        self.play(Flash(network.layers[-1], color=ACCENT_COLOR), run_time=1.2)
        self.wait(1.5)
