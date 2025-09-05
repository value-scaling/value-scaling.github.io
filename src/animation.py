%%manim -v WARNING -r 640,1080 -qm HparamEstimation3D
from manim import *
import numpy as np

config.background_color = WHITE  # black on white

class HparamEstimation3D(ThreeDScene):
    def construct(self):
        # ---------- Title (screen-aligned) ----------
        title = Tex(r"Estimate budget-optimal\\hyperparameters", color=BLACK).scale(1.35)
        title.to_edge(UP * 2)
        self.add_fixed_in_frame_mobjects(title)  # keep title in screen space
        self.remove(title)
        self.play(Write(title))
        self.wait(0.2)

        # ---------- Camera ----------
        phi = 65 * DEGREES
        theta = 30 * DEGREES
        self.set_camera_orientation(phi=phi, theta=theta, zoom=1)

        # ---------- Screen-space basis (FOLLOW EXACTLY) ----------
        # forward points from camera toward scene
        fwd = np.array([
            -np.cos(theta) * np.sin(phi),
            -np.sin(theta) * np.sin(phi),
            -np.cos(phi),
        ])
        world_up = np.array([0.0, 0.0, 1.0])  # FOLLOW EXACTLY
        screen_right = np.cross(fwd, world_up)
        screen_right = screen_right / np.linalg.norm(screen_right)
        screen_up = np.cross(screen_right, fwd)
        screen_up = screen_up  / np.linalg.norm(screen_up)
        screen_left = -screen_right
        screen_down = -screen_up
        screen_out = np.array([0.0, 0.0, 1.0])  # FOLLOW EXACTLY

        def screen_shift(dx, dy):
            return dx * screen_right + dy * screen_up

        # ---------- Curve and ranges ----------
        # x(t), y(t) as before; z(t) changed to a smooth bump with similar magnitude.
        def c(t):
            x = 3.0 * (t**-0.5) - 1
            y = t**2
            z = 1 - 0.5 * np.sin(np.pi * (t - 1.2))   # lower amplitude; peak not at 1.5
            return np.array([x, y, z])

        t_start, t_end = 1.0, 2.0
        xs = [c(t)[0] for t in (t_start, t_end)]
        ys = [c(t)[1] for t in (t_start, t_end)]
        zs = [c(t)[2] for t in (t_start, t_end)]

        x_max = max(xs) + 0.2
        y_max = max(ys) + 0.2
        z_max = max(zs) + 0.2

        # ---------- Axes (long, black) ----------
        axes = ThreeDAxes(
            x_range=[0, x_max, x_max / 5],
            y_range=[0, y_max, y_max / 5],
            z_range=[0, z_max, z_max / 5],
            x_length=7.0,
            y_length=7.0,
            z_length=7.0,
            axis_config=dict(include_ticks=False, color=BLACK, stroke_width=2),
        )
        HOW_FAR_DOWN = 6.0
        axes.shift(HOW_FAR_DOWN * screen_down)  # initial down shift in screen space
        self.play(Create(axes), run_time=0.8)

        # ---------- Axis labels (black; follow your rotations/offsets) ----------
        x_label = Tex(r"Optimal hyperparameter $x$", color=BLACK).scale(1.3)
        y_label = Tex(r"Optimal hyperparameter $y$", color=BLACK).scale(1.3)
        z_label = Tex("Budget", color=BLACK).scale(1.5)

        x_label.move_to(axes.coords_to_point(0.55 * x_max, 0, 0)).rotate(PI, axis=OUT).rotate(-PI/2, axis=RIGHT).shift(-0.3*UP+0.3*OUT)
        y_label.move_to(axes.coords_to_point(0, 0.55 * y_max, 0)).rotate(PI / 2, axis=OUT).rotate(PI/2, axis=UP).shift(-0.3*RIGHT+0.3*OUT)
        z_label.move_to(axes.coords_to_point(0, 0, 0.55 * z_max)).rotate(PI / 2, axis=UP).shift(0.6*UP)

        self.play(
            FadeIn(x_label, shift=RIGHT),
            FadeIn(y_label, shift=UP),
            FadeIn(z_label, shift=OUT),
            run_time=0.6,
        )

        # ---------- Helpers ----------
        def axes_point(t):
            x, y, z = c(t)
            return axes.coords_to_point(x, y, z)

        # Start at t=1
        p0 = axes_point(t_start)
        dot = Dot3D(point=p0, radius=0.1, color=BLUE)
        z_dot = Dot3D(point=(0, 0, p0[2]), radius=0.1, color=BLUE)

        # Static dashed guides at t=1 (black)
        x0, y0, z0 = c(t_start)
        p0_xy = axes.coords_to_point(x0, y0, 0)
        p0_xaxis = axes.coords_to_point(x0, 0, 0)
        p0_yaxis = axes.coords_to_point(0, y0, 0)

        static_drop = DashedLine(p0, p0_xy, dash_length=0.18, color=BLACK, stroke_width=2)
        static_to_x = DashedLine(p0_xy, p0_xaxis, dash_length=0.18, color=BLACK, stroke_width=2)
        static_to_y = DashedLine(p0_xy, p0_yaxis, dash_length=0.18, color=BLACK, stroke_width=2)

        self.play(FadeIn(dot, scale=0.5), run_time=0.5)
        self.wait(0.2)
        self.play(Create(static_drop), Create(static_to_x), Create(static_to_y), run_time=0.8)
        self.wait(0.3)

        # ---------- Moving dashed guides (black) ----------
        def current_point():
            return dot.get_center()

        def current_xy():
            p = current_point()
            x, y, _ = axes.point_to_coords(p)
            return axes.coords_to_point(x, y, 0)

        moving_drop = always_redraw(
            lambda: DashedLine(current_point(), current_xy(), dash_length=0.16, color=BLACK, stroke_width=2)
        )
        moving_to_x = always_redraw(
            lambda: DashedLine(
                current_xy(),
                axes.coords_to_point(axes.point_to_coords(current_xy())[0], 0, 0),
                dash_length=0.16, color=BLACK, stroke_width=2
            )
        )
        moving_to_y = always_redraw(
            lambda: DashedLine(
                current_xy(),
                axes.coords_to_point(0, axes.point_to_coords(current_xy())[1], 0),
                dash_length=0.16, color=BLACK, stroke_width=2
            )
        )
        self.add(moving_drop, moving_to_x, moving_to_y)

        # ---------- Traces (black) ----------
        trace_3d = TracedPath(lambda: current_point(), stroke_color=BLUE, stroke_width=6)
        trace_xy_live = TracedPath(lambda: current_xy(), stroke_color=BLACK, stroke_width=4)
        trace_z_live = TracedPath(
            lambda: axes.coords_to_point(0, 0, axes.point_to_coords(current_point())[2]),
            stroke_color=BLUE, stroke_width=4,
        )
        self.add(trace_3d, trace_xy_live, trace_z_live)

        # Motion path
        path = ParametricFunction(lambda u: axes_point(u), t_range=[t_start, t_end], color=BLACK)
        z_path = ParametricFunction(lambda u: axes.coords_to_point(0, 0, axes.point_to_coords(axes_point(u))[2]), t_range=[t_start, t_end], color=BLACK)

        self.play(
            MoveAlongPath(dot, path), MoveAlongPath(z_dot, z_path),
            run_time=4, rate_func=linear
        )

        self.wait(1.0)

        # ---------- STATIC traces from samples (black) ----------
        ts = np.linspace(t_start, t_end, 220)
        pts_3d = [axes_point(t) for t in ts]
        pts_xy = [axes.coords_to_point(c(t)[0], c(t)[1], 0) for t in ts]
        pts_z  = [axes.coords_to_point(0, 0, c(t)[2]) for t in ts]

        trace_3d_static = VMobject(stroke_color=BLUE, stroke_width=6).set_points_smoothly(pts_3d)
        trace_xy_static = VMobject(stroke_color=BLACK, stroke_width=4).set_points_smoothly(pts_xy)
        trace_z_static  = VMobject(stroke_color=BLUE, stroke_width=4).set_points_smoothly(pts_z)

        # Replace live with static; freeze end guides as dashed VMobjects (black)
        self.remove(trace_3d, trace_xy_live, trace_z_live, moving_drop, moving_to_x, moving_to_y)
        self.add(trace_3d_static, trace_xy_static, trace_z_static)

        x_end, y_end, z_end = c(t_end)
        p_end    = axes_point(t_end)
        p_end_xy = axes.coords_to_point(x_end, y_end, 0)
        p_end_xax= axes.coords_to_point(x_end, 0, 0)
        p_end_yax= axes.coords_to_point(0, y_end, 0)

        drop_seg = Line(p_end,    p_end_xy)
        to_x_seg = Line(p_end_xy, p_end_xax)
        to_y_seg = Line(p_end_xy, p_end_yax)

        frozen_drop = DashedVMobject(drop_seg, num_dashes=21).set_color(BLACK).set_stroke(width=2)
        frozen_to_x = DashedVMobject(to_x_seg, num_dashes=21).set_color(BLACK).set_stroke(width=2)
        frozen_to_y = DashedVMobject(to_y_seg, num_dashes=21).set_color(BLACK).set_stroke(width=2)
        self.add(frozen_drop, frozen_to_x, frozen_to_y)

        # ---------- Group and duplicate ----------
        plot_group = VGroup(
            axes, x_label, y_label, z_label, dot, z_dot,
            static_drop, static_to_x, static_to_y,
            trace_3d_static, trace_xy_static, trace_z_static,
            frozen_drop, frozen_to_x, frozen_to_y
        )
        self.wait(1.0)

        self.play(
            FadeOut(title),
            *[FadeOut(x) for x in plot_group]
        )

        self.wait(1.0)
        
        # PHASE 2
        title = Tex(r"Extrapolate hyperparameters\\to unseen budgets", color=BLACK).scale(1.35)
        title.to_edge(UP * 2)
        self.add_fixed_in_frame_mobjects(title)  # keep title in screen space
        self.remove(title)
        self.play(Write(title))
        self.wait(0.2)

        self.play(*[FadeIn(x, shift=screen_right) for x in plot_group])
        self.wait(1)

        # Midpoint between endpoints (x,y,z)
        cx = 0.5 * (c(t_start)[0] + c(t_end)[0])
        cy = 0.5 * (c(t_start)[1] + c(t_end)[1])
        cz = 0.5 * (c(t_start)[2] + c(t_end)[2])

        center_world = axes.coords_to_point(cx, cy, cz)

        # Face along -normal to the original XY projection **chord** (align x-axis with XY projection)
        # Chord direction in XY between endpoints:
        dx = c(t_end)[0] - c(t_start)[0]
        dy = c(t_end)[1] - c(t_start)[1]
        # Normal to chord in XY is (dy, -dx); face along its negative:
        theta_face = np.arctan2(-dx, dy)

        HOW_FAR_DOWN = 6.0

        # Move camera: face XY plane (phi=π/2), center on midpoint
        self.move_camera(
            phi=PI / 2,
            theta=theta_face,
            frame_center=axes.coords_to_point(cx, cy, 0),
            added_anims=[x.animate.shift(HOW_FAR_DOWN * screen_down) for x in plot_group],
            run_time=1.6,
            rate_func=smooth
        )

        self.wait(1.0)

        self.play(
            *[FadeOut(x) for x in VGroup(
                axes, x_label, y_label, z_label, dot, z_dot,
                static_drop, static_to_x, static_to_y,
                trace_z_static,
                frozen_drop, frozen_to_x, frozen_to_y     
            )]
        )

        self.wait(1.0)


        # ---------- Build 2D projection plane for right plot ----------
        # Local 3D basis from axes_right (world steps for 1 unit in x,y,z)
        origin_w = axes.coords_to_point(0, 0, 0)
        x_step_w = axes.coords_to_point(1, 0, 0) - origin_w
        y_step_w = axes.coords_to_point(0, 1, 0) - origin_w
        z_step_w = axes.coords_to_point(0, 0, 1) - origin_w

        e1_xy = np.array([dx, dy]); e1_xy = e1_xy / np.linalg.norm(e1_xy)
        e1_world = e1_xy[0] * x_step_w + e1_xy[1] * y_step_w

        # Unit directions for the new axes
        x_dir = e1_world / np.linalg.norm(e1_world)          # along original XY projection
        y_dir = screen_up / np.linalg.norm(screen_up)        # extend in screen-up direction
        z_dir = np.cross(x_dir, y_dir); z_dir /= np.linalg.norm(z_dir)  # complete a right-handed frame
        
        # Measure extent of the XY projection along x_dir to size/position the axes
        # (assumes pts_xy is the list of points used to build trace_xy_static)
        s_along = [np.dot(p - pts_xy[0], x_dir) for p in pts_xy]
        s_min, s_max = min(s_along), max(s_along)
        x_extent = (s_max - s_min)
        x_len = 1.05 * x_extent
        y_len = 0.6 * x_len  # choose a sensible height; you can tie to dz extent if you computed it
        
        # Origin: a bit left of the left edge of the blue curve, on the projection line
        left_margin = 0.08 * x_extent
        axes_origin = pts_xy[0] + (s_min - left_margin) * x_dir
        
        # Create canonical 3D axes, then rotate to align with (x_dir, y_dir, z_dir)
        y_len = 7.0
        axes2d3 = ThreeDAxes(
            x_range=[0, x_len, x_len / 5],
            y_range=[0, y_len, y_len / 5],
            z_range=[0, 1, 1],
            x_length=x_len,
            y_length=y_len,
            z_length=1.0,                         # will be hidden
            axis_config=dict(include_ticks=False, color=BLACK, stroke_width=3),
        )
        
        # Build rotation matrix whose columns are the target basis vectors
        R = np.column_stack([x_dir, y_dir, z_dir])  # maps local (1,0,0),(0,1,0),(0,0,1) to world x_dir,y_dir,z_dir
        axes2d3.apply_matrix(R)
        
        # Move the axes so that their origin coincides with axes_origin (in world coords)
        delta_to_origin = axes_origin - axes2d3.get_origin() + HOW_FAR_DOWN * screen_down
        axes2d3.shift(delta_to_origin)
        
        # Hide Z axis (keep object 3D, but visually 2D)
        axes2d3.z_axis.set_stroke(width=0)
        axes2d3.z_axis.set_opacity(0)

        
        
        # Animate: fade out the old right-side axes & dashed guides (grouped in elements_to_fade),
        # fade in the new oriented 3D axes that act as the "2D" plotting frame.
        self.play(
            # FadeOut(elements_to_fade, lag_ratio=0.05),
            Create(axes2d3),
            run_time=1.0
        )

        
        x_label = Tex(r"Optimal hyperparameters", color=BLACK).scale(1.3)
        y_label = Tex(r"Budget", color=BLACK).scale(1.3)
        # z_label = Tex("Budget", color=BLACK).scale(1.5)

        x_label.move_to(axes2d3.coords_to_point(0.55 * x_len, -0.3, 0).rotate(PI/2, screen_right))
        y_label.move_to(axes2d3.coords_to_point(-0.3, 0.55 * y_len, 0).rotate(PI/2, screen_up))

        # angle_x = np.arctan2(screen_right[1], screen_right[0])
        # angle_y = np.arctan2(screen_up[1],    screen_up[0])
        # x_label.rotate(angle_x, axis=OUT)
        # y_label.rotate(angle_y, axis=OUT)
        # z_label.move_to(axes.coords_to_point(0, 0, 0.55 * z_max))

        self.play(
            FadeIn(x_label, shift=screen_up),
            FadeIn(y_label, shift=screen_right),
            # FadeIn(z_label, shift=OUT),
            run_time=0.6,
        )

        self.wait(1.0)

        # # 2D x-axis along original XY projection chord (FOLLOW REQUEST)
        # e1_xy = np.array([dx, dy]); e1_xy = e1_xy / np.linalg.norm(e1_xy)
        # e1_world = e1_xy[0] * x_step_w + e1_xy[1] * y_step_w

        # # Build projected 2D points in the (tangent, Z) plane
        # ts_dense = np.linspace(t_start, t_end, 240)
        # s_vals, dz_vals, pts_plane = [], [], []
        # for t in ts_dense:
        #     x, y, z = c(t)
        #     s = np.dot(np.array([x - cx, y - cy]), e1_xy)  # along tangent
        #     dz = z - cz                                    # along Z
        #     s_vals.append(s); dz_vals.append(dz)
        #     pts_plane.append(center_world + s * e1_world + dz * z_step_w)

        # # Curve on the plane (black)
        # # curve_2d = VMobject(stroke_color=BLUE, stroke_width=6).set_points_smoothly(pts_plane)

        # # Determine extents along tangent (s) and z-offset (dz)
        # s_min, s_max = min(s_vals), max(s_vals)
        # # dz_min, dz_max = min(dz_vals), max(dz_vals)
        # dz_min = HOW_FAR_DOWN * screen_down[2]
        # dz_max = max(dz_vals) + HOW_FAR_DOWN * screen_down[2]
        # # New 2D axes in that plane:
        # # x-axis must coincide in direction with the original XY projection (along e1_world)
        # # y-axis placed a bit left of the left edge of the BLUE traced curve
        # left_margin = 0.08 * (s_max - s_min if s_max > s_min else 1.0)
        # axes_origin_2d = center_world + (s_min - left_margin) * e1_world + dz_min * 0 * z_step_w

        # # Positive-side only with arrow tips (BLUE, to match style)
        # x_len_pos = (s_max - (s_min - left_margin)) * 1.05
        # y_len_pos = (dz_max - dz_min) * 1.05 if dz_max > dz_min else (abs(dz_max) + 1.0) + 2 * screen_up[2]

        # axis2d_y = Line(axes_origin_2d, axes_origin_2d + y_len_pos * z_step_w, color=BLACK, stroke_width=3).add_tip(tip_length=0.2)
        # axis2d_x = Line(axes_origin_2d, axes_origin_2d + x_len_pos * e1_world, color=BLACK, stroke_width=3).add_tip(tip_length=0.2)

        # # Axis label rotations aligned to axes directions (rotate in screen plane around OUT)
        # angle_x = np.arctan2(e1_world[1], e1_world[0])
        # angle_y = np.arctan2(z_step_w[1], z_step_w[0])
        # lbl_h = Tex("Hyperparameters", color=BLACK).scale(1.5)
        # lbl_b = Tex("Budget",           color=BLACK).scale(1.5)
        # lbl_h.rotate(angle_x, axis=OUT).move_to(axis2d_x.get_end() + 0.2 * e1_world)
        # lbl_b.rotate(angle_y, axis=OUT).move_to(axis2d_y.get_end() + 0.2 * z_step_w)
        

        # ---------- STATIC traces from samples (black) ----------
        # ts = np.linspace(t_start, t_end, 220)
        # pts_3d = [axes_point(t) for t in ts]
        # pts_xy = [axes.coords_to_point(c(t)[0], c(t)[1], 0) for t in ts]
        # pts_z  = [axes.coords_to_point(0, 0, c(t)[2]) for t in ts]

        # trace_3d_static = VMobject(stroke_color=BLUE, stroke_width=6).set_points_smoothly(pts_3d)
        # trace_xy_static = VMobject(stroke_color=BLACK, stroke_width=4).set_points_smoothly(pts_xy)
        # trace_z_static  = VMobject(stroke_color=BLUE, stroke_width=4).set_points_smoothly(pts_z)

        # # Replace live with static; freeze end guides as dashed VMobjects (black)
        # self.remove(trace_3d, trace_xy_live, trace_z_live, moving_drop, moving_to_x, moving_to_y)
        # self.add(trace_3d_static, trace_xy_static, trace_z_static)

        # x_end, y_end, z_end = c(t_end)
        # p_end    = axes_point(t_end)
        # p_end_xy = axes.coords_to_point(x_end, y_end, 0)
        # p_end_xax= axes.coords_to_point(x_end, 0, 0)
        # p_end_yax= axes.coords_to_point(0, y_end, 0)

        # drop_seg = Line(p_end,    p_end_xy)
        # to_x_seg = Line(p_end_xy, p_end_xax)
        # to_y_seg = Line(p_end_xy, p_end_yax)

        # frozen_drop = DashedVMobject(drop_seg, num_dashes=21).set_color(BLACK).set_stroke(width=2)
        # frozen_to_x = DashedVMobject(to_x_seg, num_dashes=21).set_color(BLACK).set_stroke(width=2)
        # frozen_to_y = DashedVMobject(to_y_seg, num_dashes=21).set_color(BLACK).set_stroke(width=2)
        # self.add(frozen_drop, frozen_to_x, frozen_to_y)

        # # ---------- Group and duplicate ----------
        # plot_group = VGroup(
        #     axes, x_label, y_label, z_label, dot,
        #     static_drop, static_to_x, static_to_y,
        #     trace_3d_static, trace_xy_static, trace_z_static,
        #     frozen_drop, frozen_to_x, frozen_to_y
        # )

        # # Place left and right in screen space
        # left_group = plot_group
        # self.play(
        #     title.animate.scale(0.6).shift(3.2 * LEFT),  # fixed-in-frame: use LEFT/UP
        #     left_group.animate.scale(0.6).shift(screen_shift(-3.5, -1.5)),
        #     run_time=0.9
        # )
        # self.wait(0.3)

        # right_group = left_group.copy()
        # self.add(right_group)
        # self.play(
        #     right_group.animate.shift(screen_shift(7.0, 0.0)),
        #     run_time=0.7, rate_func=smooth
        # )
        # self.wait(0.3)

        # # ---------- Freeze LEFT relative to the camera (should not move during transition) ----------
        # self.add_fixed_in_frame_mobjects(left_group)
        # left_group_fixed = left_group.copy()
        # # left_group.set_opacity(0)
        # self.add_fixed_in_frame_mobjects(left_group_fixed)
        # self.remove(left_group_fixed)
        # self.remove(left_group)
        # self.add(left_group_fixed)

        # # ---------- Compute camera target & facing for right plot (parallel to XY; normal-aligned) ----------
        # # Midpoint between endpoints (x,y,z)
        # cx = 0.5 * (c(t_start)[0] + c(t_end)[0])
        # cy = 0.5 * (c(t_start)[1] + c(t_end)[1])
        # cz = 0.5 * (c(t_start)[2] + c(t_end)[2])

        # axes_right = next(m for m in right_group.submobjects if isinstance(m, ThreeDAxes))
        # center_world = axes_right.coords_to_point(cx, cy, cz)

        # # Face along -normal to the original XY projection **chord** (align x-axis with XY projection)
        # # Chord direction in XY between endpoints:
        # dx = c(t_end)[0] - c(t_start)[0]
        # dy = c(t_end)[1] - c(t_start)[1]
        # # Normal to chord in XY is (dy, -dx); face along its negative:
        # theta_face = np.arctan2(-dx, dy)

        # # Move camera: face XY plane (phi=π/2), center on midpoint
        # self.move_camera(
        #     phi=PI / 2,
        #     theta=theta_face,
        #     frame_center=center_world,
        #     run_time=1.6,
        #     rate_func=smooth
        # )

        # # ---------- Build 2D projection plane for right plot ----------
        # # Local 3D basis from axes_right (world steps for 1 unit in x,y,z)
        # origin_w = axes_right.coords_to_point(0, 0, 0)
        # x_step_w = axes_right.coords_to_point(1, 0, 0) - origin_w
        # y_step_w = axes_right.coords_to_point(0, 1, 0) - origin_w
        # z_step_w = axes_right.coords_to_point(0, 0, 1) - origin_w

        # # 2D x-axis along original XY projection chord (FOLLOW REQUEST)
        # e1_xy = np.array([dx, dy]); e1_xy = e1_xy / np.linalg.norm(e1_xy)
        # e1_world = e1_xy[0] * x_step_w + e1_xy[1] * y_step_w

        # # Build projected 2D points in the (tangent, Z) plane
        # ts_dense = np.linspace(t_start, t_end, 240)
        # s_vals, dz_vals, pts_plane = [], [], []
        # for t in ts_dense:
        #     x, y, z = c(t)
        #     s = np.dot(np.array([x - cx, y - cy]), e1_xy)  # along tangent
        #     dz = z - cz                                    # along Z
        #     s_vals.append(s); dz_vals.append(dz)
        #     pts_plane.append(center_world + s * e1_world + dz * z_step_w)

        # # Curve on the plane (black)
        # curve_2d = VMobject(stroke_color=BLUE, stroke_width=6).set_points_smoothly(pts_plane)

        # # Determine extents along tangent (s) and z-offset (dz)
        # s_min, s_max = min(s_vals), max(s_vals)
        # # dz_min, dz_max = min(dz_vals), max(dz_vals)
        # dz_min = 2 * screen_down[2]
        # dz_max = max(dz_vals) + 2 * screen_down[2]
        # # New 2D axes in that plane:
        # # x-axis must coincide in direction with the original XY projection (along e1_world)
        # # y-axis placed a bit left of the left edge of the BLUE traced curve
        # left_margin = 0.08 * (s_max - s_min if s_max > s_min else 1.0)
        # axes_origin_2d = center_world + (s_min - left_margin) * e1_world + dz_min * 0 * z_step_w

        # # Positive-side only with arrow tips (BLUE, to match style)
        # x_len_pos = (s_max - (s_min - left_margin)) * 1.05
        # y_len_pos = (dz_max - dz_min) * 1.05 if dz_max > dz_min else (abs(dz_max) + 1.0) + 2 * screen_up[2]

        # axis2d_y = Line(axes_origin_2d, axes_origin_2d + y_len_pos * z_step_w, color=BLACK, stroke_width=3).add_tip(tip_length=0.2)
        # axis2d_x = Line(axes_origin_2d, axes_origin_2d + x_len_pos * e1_world, color=BLACK, stroke_width=3).add_tip(tip_length=0.2)

        # # Axis label rotations aligned to axes directions (rotate in screen plane around OUT)
        # angle_x = np.arctan2(e1_world[1], e1_world[0])
        # angle_y = np.arctan2(z_step_w[1], z_step_w[0])
        # lbl_h = Tex("hyperparameters", color=BLUE).scale(0.7)
        # lbl_b = Tex("budget",           color=BLUE).scale(0.7)
        # lbl_h.rotate(angle_x, axis=OUT).move_to(axis2d_x.get_end() + 0.2 * e1_world)
        # lbl_b.rotate(angle_y, axis=OUT).move_to(axis2d_y.get_end() + 0.2 * z_step_w)

        # # Fade out axes & dashed guides together; keep only BLUE curve and BLACK XY projection
        # elements_to_fade = VGroup(
        #     # 3D axes and labels on the right
        #     *[m for m in right_group.submobjects if isinstance(m, (ThreeDAxes, DashedVMobject, Tex))],
        #     # any axis labels and static guides included in right_group
        #     x_label, y_label, z_label,
        #     static_drop, static_to_x, static_to_y,
        #     frozen_drop, frozen_to_x, frozen_to_y,
        #     trace_z_static,
        #     dot,
        # )

        # self.play(
        #     FadeOut(elements_to_fade),
        #     run_time=0.6
        # )
        # self.play(
        #     FadeIn(axis2d_x), FadeIn(axis2d_y),
        #     FadeIn(lbl_h),    FadeIn(lbl_b),
        #     # FadeIn(curve_2d),
        #     run_time=0.6
        # )

        # self.wait(1.0)