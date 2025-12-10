from __future__ import annotations

from typing import Callable, Iterable, Sequence
import itertools as it

import numpy as np
from manim import *

from ..theme import *  # Use PRISM brand colors


class PrismVectorField(VGroup):
    """2D vector field widget, designed for phase-space style visuals.

    By default this implements the damped pendulum vector field used in
    3Blue1Brown's differential equations series, but you can also pass a
    custom field function.

    Parameters
    ----------
    field_func
        Callable taking a NumPy array ``[x, y]`` in coordinate space and
        returning a 2- or 3-vector ``[dx/dt, dy/dt, 0]``. If omitted, a
        damped pendulum field is used.
    plane
        Optional pre-constructed `NumberPlane`. If not provided, one is
        created using ``plane_config``.
    plane_config
        Keyword arguments passed to ``NumberPlane`` when ``plane`` is not
        supplied.
    x_range, y_range
        Ranges in coordinate space over which to sample the field, of the
        form ``(min, max, step)``.
    max_vector_length
        Maximum on-screen length of any vector arrow (in scene units).
    mu, g, L
        Physical parameters for the default pendulum vector field:
        damping ``mu``, gravitational constant ``g``, and length ``L``.
    """

    def __init__(
        self,
        field_func: Callable[[np.ndarray], np.ndarray] | None = None,
        *,
        plane: NumberPlane | None = None,
        plane_config: dict | None = None,
        x_range: tuple[float, float, float] = (-4.0, 4.0, 0.75),
        y_range: tuple[float, float, float] = (-4.0, 4.0, 0.75),
        max_vector_length: float = 0.6,
        arrow_color = TEXT_COLOR,
        arrow_stroke_width: float = 2.0,
        arrow_tip_length: float = 0.2,
        mu: float = 0.2,
        g: float = 4.9,
        L: float = 1.6,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.mu = mu
        self.g = g
        self.L = L

        self._user_field_func = field_func
        self._max_vector_length = max_vector_length
        self._arrow_color = arrow_color
        self._arrow_stroke_width = arrow_stroke_width
        self._arrow_tip_length = arrow_tip_length

        # Plane setup -----------------------------------------------------
        default_plane_config = {
            "y_line_frequency": PI / 2,
            "x_line_frequency": 1,
            "y_axis_config": {"unit_size": 1},
            "y_max": 4,
            "faded_line_ratio": 4,
            "background_line_style": {"stroke_width": 1},
        }
        cfg = dict(default_plane_config)
        if plane_config:
            cfg.update(plane_config)

        self.plane: NumberPlane = plane or NumberPlane(**cfg)
        self._add_axis_labels()

        # Core vector field structure ------------------------------------
        self.vectors: VGroup = VGroup()
        self._build_vectors(x_range=x_range, y_range=y_range)

        self.add(self.plane, self.vectors)
        self.move_to(ORIGIN)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    def _add_axis_labels(self) -> None:
        """Attach standard θ, θ̇ labels like the legacy scene."""
        theta_label = self.plane.get_x_axis_label("\\theta", RIGHT, UL, buff=SMALL_BUFF)
        omega_label = self.plane.get_y_axis_label("\\dot \\theta", UP, DR, buff=SMALL_BUFF)
        omega_label.set_color(ACCENT_COLOR)

        axis_labels = VGroup(theta_label, omega_label)
        for label in axis_labels:
            label.add_background_rectangle(color=BACKGROUND_COLOR, buff=0.05)

        self.plane.axis_labels = axis_labels
        self.plane.add(axis_labels)

    def _effective_field_func(self, coords: np.ndarray) -> np.ndarray:
        """Return the vector field value at (x, y) in coordinate space."""
        if self._user_field_func is not None:
            return np.asarray(self._user_field_func(coords), dtype=float)
        return self._pendulum_vector_field(coords)

    def _build_vectors(
        self,
        *,
        x_range: tuple[float, float, float],
        y_range: tuple[float, float, float],
    ) -> None:
        x_min, x_max, x_step = x_range
        y_min, y_max, y_step = y_range

        arrows: list[Vector] = []
        for x in np.arange(x_min, x_max + 1e-6, x_step):
            for y in np.arange(y_min, y_max + 1e-6, y_step):
                coord = np.array([x, y])
                base_point = self.plane.coords_to_point(x, y)
                vec = self._effective_field_func(coord)
                # Only care about in-plane part
                vx, vy = vec[:2]
                if vx == 0 and vy == 0:
                    continue

                end_point = self.plane.coords_to_point(x + vx, y + vy)
                direction = end_point - base_point
                norm = np.linalg.norm(direction)
                if norm == 0:
                    continue

                scale = min(self._max_vector_length / norm, 1.0)
                direction *= scale

                arrow = Vector(
                    direction,
                    color=self._arrow_color,
                    stroke_width=self._arrow_stroke_width,
                    max_tip_length_to_length_ratio=self._arrow_tip_length / max(norm * scale, 1e-6),
                )
                arrow.shift(base_point)
                arrows.append(arrow)

        # Sort small-to-large so longer vectors draw on top (like get_norm)
        arrows.sort(key=lambda a: np.linalg.norm(a.get_vector()))
        self.vectors.add(*arrows)

    # ------------------------------------------------------------------
    # Public animation interface
    # ------------------------------------------------------------------

    def create(self) -> AnimationGroup:
        """Intro animation: draw vectors over the existing plane.

        The plane is already part of this VGroup; this method returns an
        `AnimationGroup` suitable for `Scene.play(self.play(field.create()))`.
        """

        # Grow all vectors with a small lag
        vector_growth = LaggedStartMap(
            GrowArrow,
            self.vectors,
            lag_ratio=0.02,
            run_time=3.0,
        )

        return AnimationGroup(vector_growth, lag_ratio=0.0)

    # ------------------------------------------------------------------
    # Helper methods for downstream scenes
    # ------------------------------------------------------------------

    def get_vector_at_point(self, point: np.ndarray) -> Vector:
        """Return a single vector arrow at a given *scene* point.

        This mirrors the legacy ``vector_field.get_vector(dot.get_center())``
        behavior, and is useful for showing the local derivative at the
        position of some moving object.
        """
        x, y = self.plane.point_to_coords(point)
        coords = np.array([x, y])
        vec = self._effective_field_func(coords)
        vx, vy = vec[:2]
        base_point = self.plane.coords_to_point(x, y)
        end_point = self.plane.coords_to_point(x + vx, y + vy)
        direction = end_point - base_point
        norm = np.linalg.norm(direction)
        if norm == 0:
            direction = RIGHT * 0.001
            norm = 0.001
        scale = min(self._max_vector_length / norm, 1.0)
        direction *= scale

        arrow = Vector(
            direction,
            color=self._arrow_color,
            stroke_width=self._arrow_stroke_width,
            max_tip_length_to_length_ratio=self._arrow_tip_length / max(norm * scale, 1e-6),
        )
        arrow.shift(base_point)
        return arrow

    # ------------------------------------------------------------------
    # Private math helpers (copied from legacy, made self-contained)
    # ------------------------------------------------------------------

    def _pendulum_vector_field(self, point: np.ndarray) -> np.ndarray:
        """Damped pendulum vector field.

        Given coordinates ``[theta, omega]``, returns
        ``[omega, -sqrt(g/L) * sin(theta) - mu * omega, 0]``.
        """
        theta, omega = point[:2]
        return np.array([
            omega,
            -np.sqrt(self.g / self.L) * np.sin(theta) - self.mu * omega,
            0.0,
        ])


class PrismVectorFieldDemo(Scene):
    """Quick demo harness for PrismVectorField.

    Run from the project root (adjust module path if needed):

        python -m manim prism_mvp/prism_lib/visuals/vector_field.py PrismVectorFieldDemo -pqh
    """

    def construct(self) -> None:
        field = PrismVectorField()
        self.add(field)
        self.play(field.create())
        self.wait(1)
