from __future__ import annotations

from typing import Sequence, Tuple

import math
import random

import numpy as np
from manim import *

from ..theme import *  # PRISM colors


class PrismGaltonBoard(VGroup):
    """2D Galton board (peg board) as a reusable VGroup.

    This ports the core geometric + probabilistic layout from the
    legacy `_2023/clt/galton_board.py` into a self-contained Manim CE
    component, suitable for use in any scene.

    Parameters
    ----------
    pegs_per_row
        Number of pegs in the top row.
    n_rows
        Number of rows of pegs.
    spacing
        Horizontal spacing between adjacent pegs.
    top_buff
        Distance from the top of the frame to the top peg row.
    peg_radius
        Radius of each peg (drawn as a 2D dot).
    ball_radius
        Radius of each falling ball (drawn as a 2D dot).
    bucket_floor_buff
        Vertical margin between bottom of buckets and bottom of frame.
    stack_ratio
        How much each ball lifts the bucket floor for stacking.
    """

    def __init__(
        self,
        pegs_per_row: int = 15,
        n_rows: int = 5,
        spacing: float = 1.0,
        top_buff: float = 1.0,
        peg_radius: float = 0.08,
        ball_radius: float = 0.08,
        bucket_floor_buff: float = 1.0,
        stack_ratio: float = 1.0,
        fall_factor: float = 0.6,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.pegs_per_row = int(pegs_per_row)
        self.n_rows = int(n_rows)
        self.spacing = float(spacing)
        self.top_buff = float(top_buff)
        self.peg_radius = float(peg_radius)
        self.ball_radius = float(ball_radius)
        self.bucket_floor_buff = float(bucket_floor_buff)
        self.stack_ratio = float(stack_ratio)
        self.fall_factor = float(fall_factor)

        # Core static geometry -------------------------------------------
        self.pegs: VGroup = self._build_pegs()
        self.buckets: VGroup = self._build_buckets(self.pegs)

        self.add(self.pegs, self.buckets)
        self.move_to(ORIGIN)

    # ------------------------------------------------------------------
    # Construction helpers (adapted from GaltonBoard methods)
    # ------------------------------------------------------------------

    def _build_pegs(self) -> VGroup:
        """Create the triangular peg lattice."""
        row_template = VGroup(*[
            Dot(radius=self.peg_radius, color=GREY_C)
            .shift(x * self.spacing * RIGHT)
            for x in range(self.pegs_per_row)
        ])
        rows = VGroup(*[
            row_template.copy().shift(
                y * self.spacing * DOWN * math.sqrt(3) / 2
            )
            for y in range(self.n_rows)
        ])
        # Offset every other row by half a spacing (staggered grid)
        rows[1::2].shift(0.5 * self.spacing * LEFT)

        rows.center()
        rows.to_edge(UP, buff=self.top_buff)
        return rows

    def _build_buckets(self, pegs: VGroup) -> VGroup:
        """Construct buckets beneath the last row of pegs.

        Each bucket is a VGroup with a left/right wall, a floor, and a
        ``bottom`` reference point used for stacking balls. A ``balls``
        VGroup is also attached for convenience.
        """
        last_row = pegs[-1]
        points = [dot.get_center() for dot in last_row]
        height = 0.5 * FRAME_HEIGHT + last_row.get_y() - self.bucket_floor_buff

        buckets = VGroup()
        for point in points:
            width = 0.5 * self.spacing - self.ball_radius
            buff = 0.7
            p0 = point + 0.5 * self.spacing * DOWN + buff * width * RIGHT
            p1 = p0 + height * DOWN
            p2 = p1 + (1 - buff) * width * RIGHT
            y = (
                point[1]
                - 0.5 * self.spacing * math.sqrt(3)
                + self.ball_radius
            )
            p3 = p2[0] * RIGHT + y * UP

            side1 = VMobject().set_points_as_corners([p0, p1, p2, p3, p0])
            side1.set_stroke(WHITE, 0)
            side1.set_fill(GREY_D, opacity=1.0)

            side2 = side1.copy()
            side2.flip(about_point=point)
            side2.reverse_points()
            side2.shift(self.spacing * RIGHT)

            floor = Line(side1.get_corner(DR), side2.get_corner(DL))
            floor.set_stroke(GREY_D, 2)

            bucket = VGroup(side1, side2, floor)

            # Bottom reference point for stacking
            bucket.bottom = VectorizedPoint(floor.get_center())
            bucket.add(bucket.bottom)

            # Track balls stacked into this bucket
            bucket.balls = VGroup()

            buckets.add(bucket)

        self.add(buckets)
        return buckets

    # ------------------------------------------------------------------
    # Ball and trajectory helpers
    # ------------------------------------------------------------------

    def _make_ball(self, color=YELLOW) -> Dot:
        ball = Dot(radius=self.ball_radius, color=color)
        return ball

    def _single_bounce_trajectory(
        self,
        ball: Mobject,
        peg: Mobject,
        direction: np.ndarray,
    ) -> VMobject:
        """Parabolic arc from top of peg to midway towards left/right."""
        sgn = np.sign(direction[0]) or 1.0
        curve = FunctionGraph(
            lambda x: -x * (x - 1),
            x_range=(0, 2, 0.2),
        )
        p1 = peg.get_top()
        p2 = p1 + self.spacing * np.array(
            [sgn * 0.5, -0.5 * math.sqrt(3), 0.0]
        )
        base_vect = curve.get_end() - curve.get_start()
        for i in (0, 1):
            if abs(base_vect[i]) > 1e-6:
                curve.stretch((p2 - p1)[i] / base_vect[i], i)
        curve.shift(
            p1
            - curve.get_start()
            + 0.5 * ball.get_height() * UP
        )
        return curve

    def _random_trajectory(
        self,
        ball: Mobject,
        pegs: VGroup,
        buckets: VGroup,
        bits: Sequence[int] | None = None,
    ) -> Tuple[VMobject, VGroup]:
        """Compute a full path for one ball through the board.

        Returns (full_path, pieces), where pieces is a VGroup containing
        the initial drop, each bounce arc, and the final straight line
        into a bucket.
        """
        index = len(pegs[0]) // 2
        radius = ball.get_height() / 2
        peg = pegs[0][index]

        # Initial vertical drop
        top_line = ParametricFunction(lambda t: t * t * DOWN)
        top_line.move_to(peg.get_top() + radius * UP, DOWN)

        if bits is None:
            bits = np.random.randint(0, 2, self.n_rows)

        bounces: list[VMobject] = []
        for row, bit in enumerate(bits):
            peg = pegs[row][index]
            direction = [LEFT, RIGHT][bit]
            bounces.append(
                self._single_bounce_trajectory(ball, peg, direction)
            )
            index += bit
            if row % 2 == 1:
                index -= 1

        # Choose bucket under final peg column
        bucket_index = index + (0 if self.n_rows % 2 == 0 else -1)
        bucket = buckets[bucket_index]
        final_line = Line(
            bounces[-1].get_end(),
            bucket.bottom.get_center() + self.ball_radius * UP,
        )
        final_line.insert_n_curves(int(8 * final_line.get_length()))
        bucket.bottom.shift(2 * self.ball_radius * self.stack_ratio * UP)
        bucket.balls.add(ball)

        # Concatenate pieces into one VMobject
        result = VMobject()
        pieces = VGroup(top_line, *bounces, final_line)
        for vmob in pieces:
            if result.get_num_points() > 0:
                vmob.shift(result.get_end() - vmob.get_start())
            result.append_vectorized_mobject(vmob)

        return result, pieces

    def _falling_animation(self, ball: Mobject, trajectory: VMobject) -> Animation:
        return MoveAlongPath(
            ball,
            trajectory,
            rate_func=linear,
            run_time=self.fall_factor * trajectory.get_arc_length(),
        )

    def get_drop_animation(
        self,
        n_balls: int = 50,
        *,
        lr_factor: float = 1.0,
        seed: int | None = None,
        color=YELLOW,
    ) -> AnimationGroup:
        """Return an animation that drops ``n_balls`` through the board.

        This method does not call ``play``; it merely constructs a set of
        ``MoveAlongPath`` animations (one per ball) and wraps them in a
        ``LaggedStart`` inside an ``AnimationGroup``. A typical usage is::

            board = PrismGaltonBoard()
            self.add(board)
            self.play(board.create())
            self.play(board.get_drop_animation(200))
        """
        if seed is not None:
            np.random.seed(seed)

        balls = VGroup(*(self._make_ball(color=color) for _ in range(n_balls)))
        self.add(balls)

        trajectories = [
            self._random_trajectory(ball, self.pegs, self.buckets)[0]
            for ball in balls
        ]

        anims = [
            self._falling_animation(ball, traj)
            for ball, traj in zip(balls, trajectories)
        ]
        if n_balls > 0:
            lag = lr_factor / n_balls
        else:
            lag = 0.0

        return AnimationGroup(
            LaggedStart(*anims, lag_ratio=lag),
            lag_ratio=0.0,
        )

    # ------------------------------------------------------------------
    # Intro animation interface (Prism standard)
    # ------------------------------------------------------------------

    def create(self) -> AnimationGroup:
        """Introduce the static board (pegs + buckets)."""
        peg_anim = LaggedStartMap(
            FadeIn,
            self.pegs,
            lag_ratio=0.05,
        )
        bucket_anim = LaggedStartMap(
            Create,
            self.buckets,
            lag_ratio=0.05,
        )
        return AnimationGroup(bucket_anim, peg_anim, lag_ratio=0.3)


class PrismGaltonBoardDemo(Scene):
    """Minimal demo harness for PrismGaltonBoard.

    Run, for example::

        manim -pqh prism_mvp/prism_lib/visuals/galton_board.py \
              PrismGaltonBoardDemo
    """

    def construct(self) -> None:
        board = PrismGaltonBoard(pegs_per_row=15, n_rows=7, spacing=0.7)
        self.add(board)
        self.play(board.create())
        self.wait(0.5)
        self.play(board.get_drop_animation(150, lr_factor=2.0, seed=1))
        self.wait(1)
