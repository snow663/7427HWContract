#!/usr/bin/env python3
"""
Interactive distributor / reluctor / rotor phasing simulator.

Purpose
-------
Visualize the separate angular relationships between:

    crankshaft <-> reluctor reference
    reluctor    <-> pickup coil
    shaft       <-> rotor
    housing     <-> cap terminals
    ECU spark   <-> actual rotor position when the coil fires

This is intentionally a geometry simulator, not a model of a specific GM
ignition algorithm.

Sign conventions
----------------
* Crank timing: positive = BTDC, negative = ATDC.
* Distributor physical angle: positive = clockwise (normal Chevy HEI rotor direction).
* Reluctor index error: positive = reluctor shifted clockwise/advanced relative
  to the shaft/rotor.
* Rotor index error: positive = rotor shifted clockwise relative to the shaft.
* Rotor/cap phase: positive = rotor has passed the cap terminal clockwise at
  the instant of spark; negative = rotor is lagging the terminal.

Core relationship
-----------------
For a nominal distributor designed around:

    design_base       = reference timing in crank degrees BTDC
    centered_spark    = crank timing where the rotor is designed to be centered
                        under the cap terminal

and an actual setup:

    set_base          = measured reference/base timing in crank degrees BTDC
    actual_spark      = actual ignition timing in crank degrees BTDC
    reluctor_error    = reluctor index error in distributor degrees
    rotor_error       = rotor index error in distributor degrees

the housing rotation relative to the nominal design is:

    housing = -(set_base - design_base)/2 + reluctor_error

and the rotor-to-cap phase at spark is:

    phase = (centered_spark - actual_spark)/2
            + (set_base - design_base)/2
            + rotor_error - reluctor_error

The factor of 1/2 appears because the distributor rotates once for every two
crankshaft revolutions.

Run:
    python distributor_phasing_sim.py

Self-test:
    python distributor_phasing_sim.py --self-test
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from matplotlib.widgets import Button, CheckButtons, Slider


@dataclass
class State:
    design_base: float = 4.0
    set_base: float = 4.0
    centered_spark: float = 20.0
    actual_spark: float = 20.0
    reluctor_error: float = 0.0
    rotor_error: float = 0.0
    terminal_half_width: float = 6.0


def housing_rotation_deg(s: State) -> float:
    """Housing rotation relative to nominal, distributor degrees, +CW."""
    return -(s.set_base - s.design_base) / 2.0 + s.reluctor_error


def rotor_cap_phase_deg(s: State) -> float:
    """Rotor position relative to #1 cap terminal at spark, distributor degrees."""
    return (
        (s.centered_spark - s.actual_spark) / 2.0
        + (s.set_base - s.design_base) / 2.0
        + s.rotor_error
        - s.reluctor_error
    )


def reference_rotor_cap_phase_deg(s: State) -> float:
    """
    Rotor/cap phase at the instant the reluctor reference occurs.

    Notice that set_base cancels. Rotating the distributor changes where the
    reference occurs relative to the crank, but does not change the hardware
    rotor/cap relationship at the reference event.
    """
    return -s.design_base / 2.0 + s.rotor_error - s.reluctor_error


def crank_to_distributor(crank_deg: float) -> float:
    return crank_deg / 2.0


def wrap_deg(a: float) -> float:
    """Wrap angle to [-180, 180)."""
    return (a + 180.0) % 360.0 - 180.0


def polar_xy(angle_deg: float, radius: float = 1.0):
    """0 deg = up, positive clockwise, matching distributor view."""
    a = math.radians(angle_deg)
    return radius * math.sin(a), radius * math.cos(a)


class DistributorSimulator:
    def __init__(self):
        self.state = State()
        self.follow_base = False
        self.follow_offset = self.state.actual_spark - self.state.set_base
        self._updating = False

        self.fig = plt.figure(figsize=(13.5, 8.4))
        self.fig.canvas.manager.set_window_title("Distributor / Reluctor / Rotor Phasing Simulator")

        self.ax_ref = self.fig.add_axes([0.04, 0.35, 0.29, 0.58])
        self.ax_spark = self.fig.add_axes([0.355, 0.35, 0.29, 0.58])
        self.ax_text = self.fig.add_axes([0.67, 0.35, 0.30, 0.58])
        self.ax_text.axis("off")

        self._make_controls()
        self.redraw()

    def _make_controls(self):
        slider_left = 0.07
        slider_width = 0.53
        y0 = 0.285
        dy = 0.041

        def add_slider(label, lo, hi, init, row, step=0.1):
            ax = self.fig.add_axes([slider_left, y0 - row * dy, slider_width, 0.025])
            sl = Slider(ax, label, lo, hi, valinit=init, valstep=step)
            sl.on_changed(self.on_slider)
            return sl

        self.sl_design = add_slider("Design base (crank °BTDC)", -10, 20, self.state.design_base, 0)
        self.sl_set = add_slider("Set/measured base (crank °BTDC)", -15, 20, self.state.set_base, 1)
        self.sl_center = add_slider("Rotor centered at spark (crank °BTDC)", -5, 50, self.state.centered_spark, 2)
        self.sl_spark = add_slider("Actual spark (crank °BTDC)", -10, 55, self.state.actual_spark, 3)
        self.sl_rel = add_slider("Reluctor index error (dist °, +CW)", -15, 15, self.state.reluctor_error, 4)
        self.sl_rot = add_slider("Rotor index error (dist °, +CW)", -15, 15, self.state.rotor_error, 5)

        ax_check = self.fig.add_axes([0.65, 0.245, 0.30, 0.055])
        self.check = CheckButtons(
            ax_check,
            ["Spark follows base (keep spark-base offset constant)"],
            [self.follow_base],
        )
        self.check.on_clicked(self.on_check)

        ax_factory = self.fig.add_axes([0.65, 0.19, 0.10, 0.04])
        ax_zero = self.fig.add_axes([0.76, 0.19, 0.10, 0.04])
        ax_minus6 = self.fig.add_axes([0.87, 0.19, 0.10, 0.04])
        self.btn_factory = Button(ax_factory, "Factory")
        self.btn_zero = Button(ax_zero, "Base 0°")
        self.btn_minus6 = Button(ax_minus6, "Base -6°")
        self.btn_factory.on_clicked(lambda evt: self.apply_preset("factory"))
        self.btn_zero.on_clicked(lambda evt: self.apply_preset("zero"))
        self.btn_minus6.on_clicked(lambda evt: self.apply_preset("minus6"))

        ax_relp5 = self.fig.add_axes([0.65, 0.135, 0.15, 0.04])
        ax_relm5 = self.fig.add_axes([0.81, 0.135, 0.16, 0.04])
        self.btn_relp5 = Button(ax_relp5, "Reluctor +5°")
        self.btn_relm5 = Button(ax_relm5, "Reluctor -5°")
        self.btn_relp5.on_clicked(lambda evt: self.set_slider(self.sl_rel, 5.0))
        self.btn_relm5.on_clicked(lambda evt: self.set_slider(self.sl_rel, -5.0))

        ax_reset = self.fig.add_axes([0.65, 0.08, 0.32, 0.04])
        self.btn_reset = Button(ax_reset, "Reset all")
        self.btn_reset.on_clicked(lambda evt: self.reset())

        self.fig.text(
            0.67,
            0.025,
            "Positive crank timing = BTDC.  Negative = ATDC.  "
            "Positive distributor geometry = clockwise.",
            fontsize=9,
        )

    def set_slider(self, slider, value):
        slider.set_val(value)

    def reset(self):
        self._updating = True
        defaults = State()
        self.sl_design.set_val(defaults.design_base)
        self.sl_set.set_val(defaults.set_base)
        self.sl_center.set_val(defaults.centered_spark)
        self.sl_spark.set_val(defaults.actual_spark)
        self.sl_rel.set_val(defaults.reluctor_error)
        self.sl_rot.set_val(defaults.rotor_error)
        self.follow_offset = defaults.actual_spark - defaults.set_base
        self._updating = False
        self.redraw()

    def apply_preset(self, name):
        if name == "factory":
            target = 4.0
        elif name == "zero":
            target = 0.0
        elif name == "minus6":
            target = -6.0
        else:
            return

        if self.follow_base:
            self._updating = True
            self.sl_set.set_val(target)
            self.sl_spark.set_val(target + self.follow_offset)
            self._updating = False
            self.redraw()
        else:
            self.sl_set.set_val(target)

    def on_check(self, _label):
        self.follow_base = not self.follow_base
        self.follow_offset = self.sl_spark.val - self.sl_set.val
        self.redraw()

    def on_slider(self, _value):
        if self._updating:
            return

        # If base timing moves while "follow base" is enabled, make actual spark
        # move by the same crank-angle delta. This reproduces the condition where
        # ignition timing simply follows the distributor reference and therefore
        # rotor/cap phase stays unchanged from that base movement alone.
        if self.follow_base:
            desired = self.sl_set.val + self.follow_offset
            if abs(self.sl_spark.val - desired) > 1e-9:
                self._updating = True
                self.sl_spark.set_val(desired)
                self._updating = False

        self.redraw()

    def read_state(self):
        self.state = State(
            design_base=self.sl_design.val,
            set_base=self.sl_set.val,
            centered_spark=self.sl_center.val,
            actual_spark=self.sl_spark.val,
            reluctor_error=self.sl_rel.val,
            rotor_error=self.sl_rot.val,
        )
        return self.state

    def setup_disc_axis(self, ax, title):
        ax.clear()
        ax.set_aspect("equal")
        ax.set_xlim(-1.35, 1.35)
        ax.set_ylim(-1.35, 1.35)
        ax.axis("off")
        ax.set_title(title, fontsize=12, pad=8)

        ax.add_patch(Circle((0, 0), 1.04, fill=False, linewidth=1.5))
        ax.add_patch(Circle((0, 0), 0.12, fill=False, linewidth=1.0))
        ax.text(0, -1.22, "+ angle = clockwise", ha="center", va="center", fontsize=8)

    def draw_cap(self, ax, housing, active_terminal=0):
        for i in range(8):
            a = housing + i * 45.0
            x1, y1 = polar_xy(a, 0.90)
            x2, y2 = polar_xy(a, 1.07)
            ax.plot([x1, x2], [y1, y2], linewidth=4 if i == active_terminal else 2)
            xt, yt = polar_xy(a, 1.17)
            ax.text(xt, yt, "#1" if i == 0 else str(i + 1), ha="center", va="center", fontsize=8)

    def draw_terminal_window(self, ax, housing, half_width):
        center_std = 90.0 - housing
        ax.add_patch(
            Wedge(
                (0, 0),
                1.01,
                center_std - half_width,
                center_std + half_width,
                width=0.11,
                alpha=0.18,
            )
        )

    def draw_rotor(self, ax, angle, label="rotor"):
        x, y = polar_xy(angle, 0.84)
        ax.plot([0, x], [0, y], linewidth=5)
        xl, yl = polar_xy(angle, 0.58)
        ax.text(xl, yl, label, fontsize=8, ha="center", va="center")

    def draw_reference_view(self, s):
        ax = self.ax_ref
        self.setup_disc_axis(ax, "At reluctor reference event")

        H = housing_rotation_deg(s)
        q_ref = -s.set_base / 2.0
        rotor = q_ref + s.rotor_error
        pickup_nominal = -s.design_base / 2.0
        pickup = H + pickup_nominal
        reluctor_tooth = q_ref + s.reluctor_error

        self.draw_cap(ax, H)
        self.draw_terminal_window(ax, H, s.terminal_half_width)
        self.draw_rotor(ax, rotor)

        xp1, yp1 = polar_xy(pickup, 0.46)
        xp2, yp2 = polar_xy(pickup, 0.64)
        ax.plot([xp1, xp2], [yp1, yp2], linewidth=6)
        xt, yt = polar_xy(pickup, 0.72)
        ax.text(xt, yt, "pickup", fontsize=8, ha="center", va="center")

        xr1, yr1 = polar_xy(reluctor_tooth, 0.29)
        xr2, yr2 = polar_xy(reluctor_tooth, 0.47)
        ax.plot([xr1, xr2], [yr1, yr2], linewidth=3)
        xt, yt = polar_xy(reluctor_tooth, 0.22)
        ax.text(xt, yt, "reluctor\n tooth", fontsize=7, ha="center", va="center")

        phase_ref = reference_rotor_cap_phase_deg(s)
        ax.text(
            0,
            -0.98,
            f"Rotor/cap phase at reference = {phase_ref:+.2f} dist°",
            ha="center",
            fontsize=9,
        )

    def draw_spark_view(self, s):
        ax = self.ax_spark
        self.setup_disc_axis(ax, "At actual spark event")

        H = housing_rotation_deg(s)
        phase = rotor_cap_phase_deg(s)
        rotor = H + phase

        self.draw_cap(ax, H)
        self.draw_terminal_window(ax, H, s.terminal_half_width)
        self.draw_rotor(ax, rotor)

        ax.text(
            0,
            -0.98,
            f"Rotor/cap phase = {phase:+.2f} dist°",
            ha="center",
            fontsize=10,
        )

        if abs(phase) <= s.terminal_half_width:
            msg = "inside illustrative terminal window"
        else:
            msg = "outside illustrative terminal window"
        ax.text(0, -1.10, msg, ha="center", fontsize=8)

    def draw_text(self, s):
        ax = self.ax_text
        ax.clear()
        ax.axis("off")

        H = housing_rotation_deg(s)
        phase = rotor_cap_phase_deg(s)
        ref_phase = reference_rotor_cap_phase_deg(s)
        base_delta = s.set_base - s.design_base
        crank_ref_shift = base_delta
        physical_from_base = -base_delta / 2.0

        lines = [
            "CURRENT GEOMETRY",
            "",
            f"Design reference:        {s.design_base:+7.2f} crank° BTDC",
            f"Set/measured reference:  {s.set_base:+7.2f} crank° BTDC",
            f"Reference change:        {crank_ref_shift:+7.2f} crank°",
            f"Base-setting housing move:{physical_from_base:+7.2f} dist°",
            "",
            f"Reluctor index error:    {s.reluctor_error:+7.2f} dist°",
            f"Rotor index error:       {s.rotor_error:+7.2f} dist°",
            f"Total housing position:  {H:+7.2f} dist°",
            "",
            f"Actual spark:             {s.actual_spark:+7.2f} crank° BTDC",
            f"Design center spark:      {s.centered_spark:+7.2f} crank° BTDC",
            "",
            f"Phase at reference:       {ref_phase:+7.2f} dist°",
            f"Phase at spark:           {phase:+7.2f} dist°",
            f"Equivalent crank angle:   {2.0*phase:+7.2f} crank°",
            "",
            "CORE EQUATION",
            "phase = (center - spark)/2",
            "      + (set base - design base)/2",
            "      + rotor error - reluctor error",
            "",
            "Key test:",
            "Change set base by 4 crank°.",
            "• If actual spark is held fixed,",
            "  rotor/cap phase moves 2 dist°.",
            "• If actual spark follows base by",
            "  the same 4 crank°, those terms",
            "  cancel and phase does not move.",
        ]

        ax.text(
            0.0,
            1.0,
            "\n".join(lines),
            va="top",
            ha="left",
            family="monospace",
            fontsize=9.5,
        )

    def redraw(self):
        s = self.read_state()
        self.draw_reference_view(s)
        self.draw_spark_view(s)
        self.draw_text(s)
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


def self_test():
    s = State()
    assert abs(housing_rotation_deg(s)) < 1e-9
    assert abs(rotor_cap_phase_deg(s)) < 1e-9

    s.set_base = 0.0
    assert abs(rotor_cap_phase_deg(s) - (-2.0)) < 1e-9

    s.actual_spark = 16.0
    assert abs(rotor_cap_phase_deg(s)) < 1e-9

    s = State(reluctor_error=5.0)
    assert abs(housing_rotation_deg(s) - 5.0) < 1e-9
    assert abs(rotor_cap_phase_deg(s) - (-5.0)) < 1e-9

    a = State(set_base=4.0, reluctor_error=2.0)
    b = State(set_base=-6.0, reluctor_error=2.0)
    assert abs(reference_rotor_cap_phase_deg(a) - reference_rotor_cap_phase_deg(b)) < 1e-9

    print("Self-test passed.")
    print("Example: design +4 BTDC -> set 0 BTDC, actual spark held fixed")
    print(f"  housing movement from base = {-((0.0 - 4.0) / 2.0):+.1f} distributor deg")
    print(f"  rotor/cap phase change      = {(0.0 - 4.0) / 2.0:+.1f} distributor deg")
    print("Example: design +4 BTDC -> set -6 ATDC, actual spark held fixed")
    print(f"  rotor/cap phase change      = {(-6.0 - 4.0) / 2.0:+.1f} distributor deg")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run geometry assertions without opening the interactive window",
    )
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    DistributorSimulator().show()


if __name__ == "__main__":
    main()
