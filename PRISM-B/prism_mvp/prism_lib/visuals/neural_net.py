from typing import Sequence
import itertools as it

import numpy as np
from manim import *

from ..theme import *  # Reuse brand colors where appropriate


class PrismNeuralNetwork(VGroup):
    """Static neural network diagram as a reusable Manim VGroup.

    Parameters
    ----------
    layer_sizes
        List of neuron counts per layer (e.g. [3, 4, 2]).
    """

    def __init__(
        self,
        layer_sizes: Sequence[int],
        neuron_radius: float = 0.15,
        neuron_to_neuron_buff: float = MED_SMALL_BUFF,
        layer_to_layer_buff: float = LARGE_BUFF,
        neuron_stroke_color = PRIMARY_COLOR,
        neuron_stroke_width: float = 3.0,
        neuron_fill_color = ACCENT_COLOR,
        edge_color = GREY_B,
        edge_stroke_width: float = 2.0,
        max_shown_neurons: int = 16,
        brace_for_large_layers: bool = True,
        average_shown_activation_of_large_layer: bool = True,
        include_output_labels: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.layer_sizes = list(layer_sizes)
        self.neuron_radius = neuron_radius
        self.neuron_to_neuron_buff = neuron_to_neuron_buff
        self.layer_to_layer_buff = layer_to_layer_buff
        self.neuron_stroke_color = neuron_stroke_color
        self.neuron_stroke_width = neuron_stroke_width
        self.neuron_fill_color = neuron_fill_color
        self.edge_color = edge_color
        self.edge_stroke_width = edge_stroke_width
        self.edge_propogation_color = YELLOW
        self.edge_propogation_time = 1.0
        self.max_shown_neurons = max_shown_neurons
        self.brace_for_large_layers = brace_for_large_layers
        self.average_shown_activation_of_large_layer = (
            average_shown_activation_of_large_layer
        )
        self.include_output_labels = include_output_labels

        # Core structure
        self.layers: VGroup = VGroup()
        self.edge_groups: VGroup = VGroup()
        self.output_labels: VGroup | None = None

        self._add_neurons()
        self._add_edges()

        # Center the whole network for convenient placement
        self.move_to(ORIGIN)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    def _add_neurons(self) -> None:
        layers = VGroup(*[self._get_layer(size) for size in self.layer_sizes])
        layers.arrange(RIGHT, buff=self.layer_to_layer_buff)
        self.layers = layers
        self.add(self.layers)
        if self.include_output_labels:
            self._add_output_labels()

    def _get_layer(self, size: int) -> VGroup:
        layer = VGroup()
        n_neurons = size
        if n_neurons > self.max_shown_neurons:
            n_neurons = self.max_shown_neurons

        neurons = VGroup(*[
            Circle(
                radius=self.neuron_radius,
                stroke_color=self.neuron_stroke_color,
                stroke_width=self.neuron_stroke_width,
                fill_color=self.neuron_fill_color,
                fill_opacity=0.0,
            )
            for _ in range(n_neurons)
        ])
        neurons.arrange(DOWN, buff=self.neuron_to_neuron_buff)

        for neuron in neurons:
            neuron.edges_in = VGroup()
            neuron.edges_out = VGroup()

        layer.neurons = neurons
        layer.add(neurons)

        if size > n_neurons:
            # Collapsed large layer: show vertical dots and optional brace
            dots = Tex("\\vdots")
            dots.move_to(neurons)
            VGroup(*neurons[: len(neurons) // 2]).next_to(
                dots, UP, MED_SMALL_BUFF
            )
            VGroup(*neurons[len(neurons) // 2 :]).next_to(
                dots, DOWN, MED_SMALL_BUFF
            )
            layer.dots = dots
            layer.add(dots)

            if self.brace_for_large_layers:
                brace = Brace(layer, LEFT)
                brace_label = brace.get_tex(str(size))
                layer.brace = brace
                layer.brace_label = brace_label
                layer.add(brace, brace_label)

        return layer

    def _add_edges(self) -> None:
        self.edge_groups = VGroup()
        for l1, l2 in zip(self.layers[:-1], self.layers[1:]):
            edge_group = VGroup()
            for n1, n2 in it.product(l1.neurons, l2.neurons):
                edge = self._get_edge(n1, n2)
                edge_group.add(edge)
                n1.edges_out.add(edge)
                n2.edges_in.add(edge)
            self.edge_groups.add(edge_group)
        self.add_to_back(self.edge_groups)

    def _get_edge(self, neuron1: Mobject, neuron2: Mobject) -> Line:
        return Line(
            neuron1.get_center(),
            neuron2.get_center(),
            buff=self.neuron_radius,
            stroke_color=self.edge_color,
            stroke_width=self.edge_stroke_width,
        )

    def _add_output_labels(self) -> None:
        self.output_labels = VGroup()
        for n, neuron in enumerate(self.layers[-1].neurons):
            label = Tex(str(n))
            label.set_height(0.75 * neuron.get_height())
            label.move_to(neuron)
            label.shift(neuron.get_width() * RIGHT)
            self.output_labels.add(label)
        self.add(self.output_labels)

    # ------------------------------------------------------------------
    # Public animation interface
    # ------------------------------------------------------------------

    def create(self) -> AnimationGroup:
        """Intro animation for the network.

        Returns an AnimationGroup that first reveals neurons layer by
        layer, then draws all edges.
        """

        neuron_anims: list[Animation] = []
        for layer in self.layers:
            neuron_anims.append(
                LaggedStartMap(
                    GrowFromCenter,
                    layer.neurons,
                    lag_ratio=0.1,
                )
            )

        edge_anims: list[Animation] = []
        for edges in self.edge_groups:
            edge_anims.append(
                LaggedStartMap(
                    Create,
                    edges,
                    lag_ratio=0.01,
                )
            )

        return AnimationGroup(*neuron_anims, *edge_anims, lag_ratio=0.5)

    # ------------------------------------------------------------------
    # Optional helpers for more advanced usage
    # ------------------------------------------------------------------

    def deactivate_layers(self) -> "PrismNeuralNetwork":
        """Reset all neuron fills to zero opacity (no activation)."""
        all_neurons = VGroup(
            *it.chain.from_iterable(layer.neurons for layer in self.layers)
        )
        all_neurons.set_fill(opacity=0.0)
        return self

    # Public activation API ---------------------------------------------

    def set_activations(
        self, layer_values_per_layer: Sequence[Sequence[float]]
    ) -> "PrismNeuralNetwork":
        """Color neurons according to per-layer activation values.

        Parameters
        ----------
        layer_values_per_layer
            Iterable of activation vectors, one per layer. Each
            activation vector is a sequence of non-negative values,
            typically in [0, 1]. For layers with more neurons than
            values, the remaining neurons are set to zero; for layers
            with *fewer* visible neurons than values, the vector is
            downsampled using the same averaging logic as the legacy
            3b1b implementation.
        """

        for layer_index, (layer, values) in enumerate(
            zip(self.layers, layer_values_per_layer)
        ):
            self._activate_layer(layer, values)
        return self

    def _activate_layer(
        self,
        layer: VGroup,
        activation_vector: Sequence[float],
    ) -> VGroup:
        """Apply fills to a single layer of neurons.

        Mirrors the downsampling/averaging behavior of the original
        `NetworkMobject.activate_layer`, but works purely on the
        provided vector without needing a backing Network object.
        """

        n_neurons = len(layer.neurons)
        if n_neurons == 0:
            return layer

        av = np.asarray(activation_vector, dtype=float).flatten()

        # Helper: map a chunk of activations to a single display value
        def _arr_to_num(arr: np.ndarray) -> float:
            if arr.size == 0:
                return 0.0
            # Same heuristic as legacy: fraction above threshold, then
            # take a cube root to compress the range.
            return (np.sum(arr > 0.1) / float(len(arr))) ** (1.0 / 3.0)

        # Downsample large vectors when there are fewer visible neurons
        if len(av) > n_neurons:
            if self.average_shown_activation_of_large_layer:
                step = max(1, int(len(av) / n_neurons))
                indices = list(np.arange(n_neurons) * step)
                indices.append(len(av))
                av = np.array(
                    [
                        _arr_to_num(av[i1:i2])
                        for i1, i2 in zip(indices[:-1], indices[1:])
                    ]
                )
            else:
                half = n_neurons // 2
                av = np.append(av[:half], av[-half:])

        # If there are fewer activation values than neurons, pad with zeros
        if len(av) < n_neurons:
            av = np.append(av, np.zeros(n_neurons - len(av)))

        # Finally, apply to visible neurons
        for activation, neuron in zip(av, layer.neurons):
            neuron.set_fill(
                color=self.neuron_fill_color,
                opacity=float(max(0.0, activation)),
            )

        return layer

    def get_edge_propagation_animations(self, index: int) -> list[Animation]:
        """Return animations that flash edges between two consecutive layers.

        Parameters
        ----------
        index
            Index of the edge group (0 = between first and second layer).
        """
        edge_group_copy = self.edge_groups[index].copy()
        edge_group_copy.set_stroke(
            self.edge_propogation_color,
            width=1.5 * self.edge_stroke_width,
        )
        # Use Create + Uncreate instead of ShowCreationThenDestruction
        return [
            AnimationGroup(
                Create(edge_group_copy, run_time=self.edge_propogation_time),
                Uncreate(edge_group_copy, run_time=self.edge_propogation_time),
                lag_ratio=0.5,
            )
        ]


class PrismNeuralNetworkDemo(Scene):
    """Minimal demo scene to exercise PrismNeuralNetwork.

    Not used by the library directly, but helpful for quick previews:

        manim -pqh prism_lib.visuals.neural_net PrismNeuralNetworkDemo
    """

    def construct(self) -> None:
        network = PrismNeuralNetwork(layer_sizes=[3, 5, 4, 2])
        self.add(network)
        self.play(network.create())
        self.wait(1)
