from __future__ import annotations

from typing import Sequence, Callable
import itertools as it
from functools import reduce
import operator as op

import numpy as np
from manim import *

from ..theme import *  # PRISM colors


class PrismFourierCircles(VGroup):
    """Epicycle / Fourier-circles visual as a reusable VGroup.

    This component is adapted from the legacy ``FourierCirclesScene``.
    It builds a chain of rotating vectors, ambient circles around each
    vector, and a drawn path traced by the vector sum.

    Parameters
    ----------
    n_vectors
        Number of epicycles (Fourier terms) to use.
    coefficients
        Optional explicit list of complex Fourier coefficients. If
        omitted, a simple default set is used so the widget animates
        out-of-the-box.
    base_frequency
        Base angular frequency multiplier for all integer frequencies.
    slow_factor
        Scales how fast time passes for the rotating vectors.
    center_point
        Where the first vector is rooted in scene coordinates.
    colors
        Cycle of colors for circles corresponding to each vector.
    parametric_function_step_size
        Step size for sampling the analytic vector-sum path.
    drawn_path_color, drawn_path_stroke_width
        Style for the traced path.
    """

    def __init__(
        self,
        n_vectors: int = 10,
        coefficients: Sequence[complex] | None = None,
        *,
        base_frequency: float = 1.0,
        slow_factor: float = 0.25,
        center_point: np.ndarray = ORIGIN,
        colors: Sequence = (BLUE_D, BLUE_C, BLUE_E, GREY_BROWN),
        parametric_function_step_size: float = 0.01,
        drawn_path_color = YELLOW,
        drawn_path_stroke_width: float = 2.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.n_vectors = int(n_vectors)
        self.base_frequency = float(base_frequency)
        self.center_point = np.array(center_point, dtype=float)
        self.colors = list(colors)
        self.parametric_function_step_size = float(parametric_function_step_size)
        self.drawn_path_color = drawn_path_color
        self.drawn_path_stroke_width = float(drawn_path_stroke_width)

        # Time control ----------------------------------------------------
        self.slow_factor_tracker = ValueTracker(float(slow_factor))
        self.vector_clock = ValueTracker(0.0)
        self.vector_clock.add_updater(
            lambda m, dt: m.increment_value(
                self.get_slow_factor() * dt
            )
        )

        # Fourier data ----------------------------------------------------
        self.freqs = self._get_freqs(self.n_vectors)
        if coefficients is None:
            # Simple default: constant term 1, others zero
            self.coefficients = [
                1.0 + 0j if k == 0 else 0.0 + 0j
                for k in range(self.n_vectors)
            ]
        else:
            if len(coefficients) != self.n_vectors:
                raise ValueError("coefficients must have length n_vectors")
            self.coefficients = list(coefficients)

        # Core geometric objects -----------------------------------------
        self.center_tracker = VectorizedPoint(self.center_point)
        self.vectors: VGroup = self._get_rotating_vectors(
            freqs=self.freqs,
            coefficients=self.coefficients,
        )
        self.circles: VGroup = self._get_circles(self.vectors)
        self.path: VMobject = self._get_drawn_path(self.vectors)

        # Assemble group
        self.add(
            self.vector_clock,
            self.slow_factor_tracker,
            self.center_tracker,
            self.circles,
            self.vectors,
            self.path,
        )
        self.move_to(ORIGIN)

    # ------------------------------------------------------------------
    # Time helpers
    # ------------------------------------------------------------------

    def get_slow_factor(self) -> float:
        return float(self.slow_factor_tracker.get_value())

    def get_vector_time(self) -> float:
        return float(self.vector_clock.get_value())

    # ------------------------------------------------------------------
    # Fourier construction helpers (ported from legacy scene)
    # ------------------------------------------------------------------

    def _get_freqs(self, n: int) -> list[int]:
        all_freqs = list(range(n // 2, -n // 2, -1))
        all_freqs.sort(key=abs)
        return all_freqs

    def _get_color_iterator(self):
        return it.cycle(self.colors)

    def _get_rotating_vectors(
        self,
        *,
        freqs: Sequence[int],
        coefficients: Sequence[complex],
    ) -> VGroup:
        vectors = VGroup()
        last_vector: Vector | None = None

        for freq, coefficient in zip(freqs, coefficients):
            if last_vector is not None:
                center_func: Callable[[], np.ndarray] = last_vector.get_end
            else:
                center_func = self.center_tracker.get_location
            vector = self._get_rotating_vector(
                coefficient=coefficient,
                freq=freq,
                center_func=center_func,
            )
            vectors.add(vector)
            last_vector = vector

        return vectors

    def _get_rotating_vector(
        self,
        *,
        coefficient: complex,
        freq: int,
        center_func: Callable[[], np.ndarray],
    ) -> Vector:
        vector = Vector(RIGHT, buff=0, max_tip_length_to_length_ratio=0.35)
        vector.scale(abs(coefficient))

        if abs(coefficient) == 0:
            phase = 0.0
        else:
            phase = np.angle(coefficient)

        vector.rotate(phase, about_point=ORIGIN)
        vector.freq = freq
        vector.coefficient = coefficient
        vector.center_func = center_func
        vector.add_updater(self._update_vector)
        return vector

    def _update_vector(self, vector: Vector, dt: float) -> Vector:
        time = self.get_vector_time()
        coef: complex = vector.coefficient
        freq: int = vector.freq
        phase = np.angle(coef) if abs(coef) > 0 else 0.0

        length = abs(coef)
        vector.set_length(length)
        vector.set_angle(phase + time * freq * self.base_frequency * TAU)
        vector.shift(vector.center_func() - vector.get_start())
        return vector

    def _get_circles(self, vectors: VGroup) -> VGroup:
        return VGroup(
            *[
                self._get_circle(vector, color=color)
                for vector, color in zip(vectors, self._get_color_iterator())
            ]
        )

    def _get_circle(self, vector: Vector, color=BLUE) -> Circle:
        circle = Circle(color=color, stroke_width=1, stroke_opacity=0.75)
        circle.center_func = vector.get_start
        circle.radius_func = vector.get_length
        circle.add_updater(self._update_circle)
        return circle

    def _update_circle(self, circle: Circle) -> Circle:
        circle.set_width(2 * circle.radius_func())
        circle.move_to(circle.center_func())
        return circle

    def _complex_to_R3(self, z: complex) -> np.ndarray:
        return np.array([z.real, z.imag, 0.0])

    def _get_vector_sum_path(self, vectors: VGroup, *, color=YELLOW) -> ParametricFunction:
        coefs = [v.coefficient for v in vectors]
        freqs = [v.freq for v in vectors]
        center = np.array(self.center_point)

        def func(t: float) -> np.ndarray:
            return center + reduce(
                op.add,
                [
                    self._complex_to_R3(
                        coef * np.exp(TAU * 1j * freq * t)
                    )
                    for coef, freq in zip(coefs, freqs)
                ],
                np.zeros(3),
            )

        path = ParametricFunction(
            func,
            t_min=0.0,
            t_max=1.0,
            step_size=self.parametric_function_step_size,
            color=color,
        )
        return path

    def _get_drawn_path(
        self,
        vectors: VGroup,
        *,
        stroke_width: float | None = None,
        fade_rate: float = 0.2,
    ) -> VMobject:
        if stroke_width is None:
            stroke_width = self.drawn_path_stroke_width

        path = self._get_vector_sum_path(vectors)
        path.set_stroke(self.drawn_path_color, stroke_width)
        self._add_path_fader(path, fade_rate)
        return path

    def _add_path_fader(self, path: VMobject, fade_rate: float = 0.2) -> VMobject:
        stroke_width = float(np.max(path.get_stroke_width()))
        stroke_opacity = float(np.max(path.get_stroke_opacity()))

        def update_path(path_: VMobject, dt: float) -> VMobject:
            alpha = self.get_vector_time()
            n = path_.get_num_points()
            if n == 0:
                return path_
            fade_factors = (np.linspace(0.0, 1.0, n) - alpha) % 1.0
            fade_factors = fade_factors ** fade_rate
            path_.set_stroke(
                width=stroke_width * fade_factors,
                opacity=stroke_opacity * fade_factors,
            )
            return path_

        path.add_updater(update_path)
        return path

    # ------------------------------------------------------------------
    # Public animation interface
    # ------------------------------------------------------------------

    def create(self) -> AnimationGroup:
        """Intro animation: grow vectors, circles, and traced path."""
        vector_growth = LaggedStartMap(
            GrowArrow,
            self.vectors,
            lag_ratio=0.05,
            run_time=3.0,
        )
        circle_fade = FadeIn(self.circles, run_time=2.0)
        path_draw = Create(self.path, run_time=3.0)

        return AnimationGroup(vector_growth, circle_fade, path_draw, lag_ratio=0.3)


class PrismFourierCirclesDemo(Scene):
    """Minimal demo scene for PrismFourierCircles.

    Example::

        manim -pqh prism_mvp/prism_lib/visuals/fourier_circles.py \\
              PrismFourierCirclesDemo
    """

    def construct(self) -> None:
        widget = PrismFourierCircles(n_vectors=7)
        self.add(widget)
        self.play(widget.create())
        self.wait(1)
