from __future__ import annotations

from typing import Sequence

import numpy as np
from manim import *

from ..theme import *  # PRISM colors and font sizes


class PrismLinearTransform(VGroup):
    """Linear transformation visual as a reusable VGroup.

    This component is inspired by 3Blue1Brown's linear algebra visuals.
    It shows a coordinate grid, basis vectors, and a matrix; the
    ``create()`` method animates applying the linear transformation.

    Parameters
    ----------
    matrix
        2x2 array-like representing the linear transformation.
    show_grid
        Whether to show a background ``NumberPlane`` grid.
    show_basis_vectors
        Whether to draw the basis vectors e1 and e2 from the origin.
    basis_vector_colors
        Colors for e1 and e2.
    plane_config
        Optional keyword overrides passed to ``NumberPlane``.
    """

    def __init__(
        self,
        matrix: Sequence[Sequence[float]] | np.ndarray,
        *,
        show_grid: bool = True,
        show_basis_vectors: bool = True,
        basis_vector_colors: Sequence = (BLUE, GREEN),
        plane_config: dict | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        # Store and normalize matrix
        arr = np.array(matrix, dtype=float)
        if arr.shape != (2, 2):
            raise ValueError("PrismLinearTransform expects a 2x2 matrix")
        self.matrix = arr

        self.show_grid = show_grid
        self.show_basis_vectors = show_basis_vectors
        self.basis_vector_colors = list(basis_vector_colors)[:2]

        # Coordinate plane ------------------------------------------------
        default_plane_config = dict(
            x_range=(-5, 5, 1),
            y_range=(-3, 3, 1),
            background_line_style={"stroke_width": 1, "stroke_opacity": 0.5},
        )
        cfg = {**default_plane_config, **(plane_config or {})}
        self.plane: NumberPlane = NumberPlane(**cfg)

        # Grid / axes label styling (optional to tweak later)
        self.plane.set_stroke(color=GREY_B, width=1, opacity=0.5)

        # Basis vectors ---------------------------------------------------
        self.basis_vectors = VGroup()
        self.basis_labels = VGroup()
        if show_basis_vectors:
            e1 = self._make_basis_vector(RIGHT, color=self.basis_vector_colors[0])
            e2 = self._make_basis_vector(UP, color=self.basis_vector_colors[1])
            self.basis_vectors.add(e1, e2)
            self.basis_labels.add(
                self._vector_coordinate_label(e1, color=self.basis_vector_colors[0]),
                self._vector_coordinate_label(e2, color=self.basis_vector_colors[1]),
            )

        # Matrix and determinant display ---------------------------------
        self.matrix_mob = self._matrix_to_mobject(self.matrix)
        self.matrix_mob.scale(0.8)
        self.matrix_mob.to_corner(UR, buff=MED_SMALL_BUFF)

        det_val = float(np.linalg.det(self.matrix))
        self.det_group = self._get_det_text(self.matrix_mob, determinant=det_val)
        self.det_group.next_to(self.matrix_mob, DOWN, buff=SMALL_BUFF)

        # Group everything
        if self.show_grid:
            self.add(self.plane)
        self.add(self.basis_vectors, self.basis_labels, self.matrix_mob, self.det_group)

        # Center for convenience
        self.move_to(ORIGIN)

    # ------------------------------------------------------------------
    # Construction helpers (ported / adapted from legacy code)
    # ------------------------------------------------------------------

    def _matrix_to_tex_string(self, matrix: np.ndarray) -> str:
        mat = np.array(matrix).astype("str")
        if mat.ndim == 1:
            mat = mat.reshape((mat.size, 1))
        n_rows, n_cols = mat.shape
        prefix = r"\\left[ \\begin{array}{%s}" % ("c" * n_cols)
        suffix = r"\\end{array} \\right]"
        rows = [" & ".join(row) for row in mat]
        return prefix + r" \\ ".join(rows) + suffix

    def _matrix_to_mobject(self, matrix: np.ndarray) -> Tex:
        tex_string = self._matrix_to_tex_string(matrix)
        return Tex(tex_string)

    def _make_basis_vector(self, direction: np.ndarray, color) -> Arrow:
        arrow = Arrow(ORIGIN, direction, buff=0, color=color)
        arrow.set_stroke(width=4)
        return arrow

    def _vector_coordinate_label(
        self,
        vector_mob: Arrow,
        *,
        integer_labels: bool = True,
        n_dim: int = 2,
        color = WHITE,
    ) -> Matrix:
        # Get endpoint in plane coordinates (so labels match numeric grid)
        if self.show_grid:
            x, y = self.plane.point_to_coords(vector_mob.get_end())
        else:
            x, y, _ = vector_mob.get_end()
        vect = np.array([x, y])
        if integer_labels:
            vect = np.round(vect).astype(int)
        vect = vect[:n_dim].reshape((n_dim, 1))

        label = Matrix(vect, add_background_rectangles_to_entries=True)
        label.scale(0.6)

        # Position label relative to arrow direction
        shift_dir = vector_mob.get_end() - vector_mob.get_start()
        if shift_dir[0] >= 0:
            label.next_to(vector_mob.get_end(), RIGHT, buff=0.1)
        else:
            label.next_to(vector_mob.get_end(), LEFT, buff=0.1)

        label.set_color(color)
        rect = BackgroundRectangle(label, fill_opacity=0.8, buff=0.1)
        label.add_to_back(rect)
        return label

    def _get_det_text(
        self,
        matrix_mob: Mobject,
        determinant: float | int | str | None = None,
        *,
        background_rect: bool = True,
        initial_scale_factor: float = 1.0,
    ) -> VGroup:
        parens = Tex("()")
        parens.scale(initial_scale_factor)
        parens.stretch_to_fit_height(matrix_mob.get_height())
        l_paren, r_paren = parens.split()
        l_paren.next_to(matrix_mob, LEFT, buff=0.1)
        r_paren.next_to(matrix_mob, RIGHT, buff=0.1)

        det = Tex("det")
        det.scale(initial_scale_factor)
        det.next_to(l_paren, LEFT, buff=0.1)
        if background_rect:
            det.add_background_rectangle(color=BACKGROUND_COLOR, buff=0.05)
        det_text = VGroup(det, l_paren, r_paren)

        if determinant is not None:
            # Round nicely for display
            if isinstance(determinant, (int, float)):
                determinant_str = f"{determinant:.2f}".rstrip("0").rstrip(".")
            else:
                determinant_str = str(determinant)
            eq = Tex("=")
            eq.next_to(r_paren, RIGHT, buff=0.1)
            result = Tex(determinant_str)
            result.next_to(eq, RIGHT, buff=0.2)
            det_text.add(eq, result)

        return det_text

    # ------------------------------------------------------------------
    # Public animation interface
    # ------------------------------------------------------------------

    def create(self) -> AnimationGroup:
        """Intro + transform animation.

        - Draw the grid (if enabled)
        - Grow basis vectors and show their coordinate labels
        - Fade in the matrix and determinant
        - Apply the linear transformation to grid and basis
        """

        animations: list[Animation] = []

        if self.show_grid:
            animations.append(Create(self.plane))

        if len(self.basis_vectors) > 0:
            animations.append(
                LaggedStartMap(
                    GrowArrow,
                    self.basis_vectors,
                    lag_ratio=0.2,
                )
            )
            animations.append(FadeIn(self.basis_labels))

        animations.append(FadeIn(self.matrix_mob, shift=DOWN * 0.3))
        animations.append(FadeIn(self.det_group, shift=DOWN * 0.3))

        # Apply matrix to all geometric objects (grid + vectors + labels)
        geom_group = VGroup()
        if self.show_grid:
            geom_group.add(self.plane)
        geom_group.add(self.basis_vectors, self.basis_labels)

        if len(geom_group) > 0:
            animations.append(
                ApplyMatrix(
                    self.matrix,
                    geom_group,
                    run_time=3.0,
                )
            )

        return AnimationGroup(*animations, lag_ratio=0.3)


class PrismLinearTransformDemo(Scene):
    """Minimal demo scene for PrismLinearTransform.

    Example usage::

        manim -pqh prism_mvp/prism_lib/visuals/linear_transform.py \\
              PrismLinearTransformDemo
    """

    def construct(self) -> None:
        # Simple shear
        A = [[1, 1], [0, 1]]
        widget = PrismLinearTransform(A)
        self.add(widget)
        self.play(widget.create())
        self.wait(1)
