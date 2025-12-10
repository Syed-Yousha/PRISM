import sys
import os
import numpy as np

from manim import *

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

for path in (SCRIPT_DIR, PROJECT_ROOT):
    if path not in sys.path:
        sys.path.append(path)

from prism_lib.visuals.neural_net import PrismNeuralNetwork
from prism_lib.theme import BACKGROUND_COLOR, PRIMARY_COLOR, ACCENT_COLOR, TEXT_COLOR


class PrismInteractiveNeuralScene(MovingCameraScene):
    """Advanced neural animation inspired by 3Blue1Brown pacing."""

    def construct(self) -> None:
        self.camera.background_color = BACKGROUND_COLOR

        # Ambient grid + glow -------------------------------------------------
        plane = NumberPlane(
            background_line_style={"stroke_width": 1, "stroke_opacity": 0.1},
            x_range=(-10, 10, 1),
            y_range=(-6, 6, 1),
        )
        plane.fade(0.5)
        glow = Circle(radius=3).set_stroke(ACCENT_COLOR, 0, opacity=0)
        glow.set_fill(ACCENT_COLOR, opacity=0.2)
        glow.scale(0.01)

        # Hero texts ----------------------------------------------------------
        title = Text("Interactive Neural Narrative", font_size=54, color=ACCENT_COLOR)
        subtitle = Text("Signals bloom as the user explores", font_size=30, color=TEXT_COLOR)
        header = VGroup(title, subtitle).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        header.set_max_width(5.6)
        narrative = Paragraph(
            "Signals sweep from left to right,", "spotlighting how each layer refines",
            "what the previous one discovered.",
            alignment="left",
            line_spacing=0.7,
            font_size=26,
        )
        narrative.set_color(TEXT_COLOR)
        narrative.set_width(5.6)

        # Network board -------------------------------------------------------
        network = PrismNeuralNetwork([4, 7, 7, 4, 2], layer_to_layer_buff=1.2)
        network.scale(1.1)
        board = RoundedRectangle(corner_radius=0.35)
        board.set_width(network.width + 1.4)
        board.set_height(network.height + 1.4)
        board.set_stroke(PRIMARY_COLOR, width=2.5, opacity=0.5)
        board.set_fill(PRIMARY_COLOR, opacity=0.08)
        network.move_to(board)

        cue_box = RoundedRectangle(corner_radius=0.2, width=4.2, height=1.4)
        cue_box.set_fill(color=PRIMARY_COLOR, opacity=0.2)
        cue_box.set_stroke(PRIMARY_COLOR, width=2)
        cue_text = Text("Tap nodes to inspect", font_size=26, color=TEXT_COLOR)
        cue = VGroup(cue_box, cue_text)
        cue.next_to(board, DOWN, buff=0.4)

        left_column = VGroup(header, narrative).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        board_column = VGroup(board, cue).arrange(DOWN, buff=0.4)
        layout = VGroup(left_column, board_column).arrange(RIGHT, buff=1.5, aligned_edge=UP)
        layout.to_edge(UP, buff=0.6)

        self.play(FadeIn(plane, run_time=1.2))
        self.play(
            FadeIn(glow, scale=20),
            glow.animate.scale(35).set_opacity(0),
            run_time=2,
            rate_func=there_and_back_with_pause,
        )
        self.play(Write(title), FadeIn(subtitle, shift=UP))
        self.play(FadeIn(narrative, shift=UP * 0.2))

        self.play(FadeIn(board, shift=DOWN), FadeIn(cue, shift=UP), run_time=1.5)
        self.play(network.create(), run_time=3)

        # Helper functions ----------------------------------------------------
        def pulse_edges(edge_group: VGroup, color=ACCENT_COLOR, run_time=1.2):
            packets = VGroup(
                *[
                    Dot(color=color, radius=0.05).move_to(edge.get_start())
                    for edge in edge_group
                ]
            )
            self.add(packets)
            self.play(
                LaggedStart(
                    *[
                        MoveAlongPath(packet, edge, rate_func=linear)
                        for packet, edge in zip(packets, edge_group)
                    ],
                    lag_ratio=0.015,
                    run_time=run_time,
                )
            )
            self.play(FadeOut(packets), run_time=0.2)

        def highlight_layer(layer: VGroup, tint=PRIMARY_COLOR):
            return LaggedStart(
                *[Indicate(neuron, color=tint, scale_factor=1.08) for neuron in layer.neurons],
                lag_ratio=0.15,
                run_time=1.2,
            )

        # Spotlight each layer -----------------------------------------------
        for idx, layer in enumerate(network.layers):
            callout = Text(f"Layer {idx+1}", font_size=24, color=TEXT_COLOR)
            callout.next_to(layer, LEFT if idx % 2 == 0 else RIGHT, buff=0.4)
            bubble = SurroundingRectangle(callout, color=PRIMARY_COLOR, buff=0.2)
            label = VGroup(bubble, callout)
            self.play(FadeIn(label, shift=UP))
            self.play(highlight_layer(layer))
            self.play(FadeOut(label, shift=DOWN))

        # Sequential pulses through the network ------------------------------
        for edge_group in network.edge_groups:
            pulse_edges(edge_group)

        # Camera move to outputs ---------------------------------------------
        self.play(
            self.camera.frame.animate.scale(0.7).move_to(network.layers[-1]),
            run_time=2,
        )

        # Activation sweep ----------------------------------------------------
        activation_vectors = []
        rng = np.random.default_rng(3)
        for layer in network.layers:
            values = rng.uniform(0.15, 0.95, len(layer.neurons))
            activation_vectors.append(values.tolist())
        network.set_activations(activation_vectors)

        output_glow = SurroundingRectangle(network.layers[-1], color=ACCENT_COLOR, buff=0.3)
        self.play(Create(output_glow), Flash(network.layers[-1], color=ACCENT_COLOR))

        # Final zoom out -----------------------------------------------------
        self.play(
            self.camera.frame.animate.scale(1.6).move_to(board),
            FadeOut(output_glow),
            run_time=2,
        )
        self.wait(1.5)
