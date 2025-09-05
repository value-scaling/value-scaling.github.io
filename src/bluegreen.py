%%manim -v WARNING -qm BlueToGreenSinglePath
from manim import *
import numpy as np

class BlueToGreenSinglePath(Scene):
    def construct(self):
        # Parametric path
        def gamma(u):
            return np.array([3*np.cos(2*np.pi*u), 2*np.sin(2*np.pi*u), 0.0])

        # For reference
        base = ParametricFunction(lambda u: gamma(u), t_range=[0, 1], color=BLACK)
        self.add(base)

        # Progress tracker
        alpha = ValueTracker(0.0)

        # Moving dot whose color matches the path end (blue -> green)
        dot = Dot(gamma(0.0), radius=0.08, color=BLUE)
        def update_dot(m):
            a = alpha.get_value()
            m.move_to(gamma(a))
            m.set_fill(interpolate_color(BLUE, GREEN, a), opacity=1.0)
            m.set_stroke(interpolate_color(BLUE, GREEN, a), width=2)
        dot.add_updater(update_dot)
        self.add(dot)

        # One single trail object that grows with alpha and has a stroke gradient
        def make_trail(a: float) -> VMobject:
            a = np.clip(a, 0.0, 1.0)
            # Sample the curve from 0..a
            us = np.linspace(0.0, a, max(2, int(300 * a) + 2))
            pts = [gamma(u) for u in us]
            trail = VMobject()
            trail.set_points_smoothly(pts)
            # Consistent width, gradient along the path (start=BLUE, end=GREEN)
            trail.set_stroke(color=[BLUE, GREEN], width=6)
            return trail

        trail = always_redraw(lambda: make_trail(alpha.get_value()))
        self.add(trail)

        # Animate progress
        self.play(alpha.animate.set_value(1.0), run_time=4, rate_func=linear)

        # Freeze
        dot.clear_updaters()
        self.wait(0.5)
