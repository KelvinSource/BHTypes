"""The borehole, and the borehole heat exchanger built in it.

:class:`Borehole` is the hole itself: its length and diameter, the same wherever it is drilled.
Where a borehole is placed -- its position, buried depth, tilt and orientation -- belongs to
the bore field, not to the borehole, and is out of scope here.

:class:`BoreholeHeatExchanger` is the static description of one borehole heat exchanger: the
borehole, its pipe and grout, in the soil -- what the models of its thermal resistance and
short-time response take, apart from the operating conditions (fluid, flow rate, temperature),
which change during operation and are passed to those models separately.  It checks what none
of its parts can on its own: that the pipe fits inside the borehole.

Plain data with validation. Conversions to other packages' conventions are in
:mod:`bhtypes.convert`.
"""

from __future__ import annotations

from dataclasses import dataclass

from bhtypes._checks import positive
from bhtypes.materials import Grout, Soil
from bhtypes.pipes import Coaxial, DoubleUTube, Pipe, SingleUTube


@dataclass(frozen=True, slots=True)
class Borehole:
    """The borehole itself, independent of where it is placed.

    Attributes
    ----------
    length_m : float
        Active length, along the borehole axis.
    diameter_m : float
        Borehole (drilled) diameter.
    """

    length_m: float
    diameter_m: float

    def __post_init__(self) -> None:
        positive("length_m", self.length_m)
        positive("diameter_m", self.diameter_m)

    @property
    def radius_m(self) -> float:
        return self.diameter_m / 2.0


_PIPES = (SingleUTube, DoubleUTube, Coaxial)


@dataclass(frozen=True, slots=True)
class BoreholeHeatExchanger:
    """A borehole with its pipe and grout, in the soil.

    Attributes
    ----------
    borehole : Borehole
    pipe : SingleUTube, DoubleUTube or Coaxial
    grout : Grout
    soil : Soil
    """

    borehole: Borehole
    pipe: Pipe
    grout: Grout
    soil: Soil

    def __post_init__(self) -> None:
        for name, value, kind in (
            ("borehole", self.borehole, Borehole),
            ("pipe", self.pipe, _PIPES),
            ("grout", self.grout, Grout),
            ("soil", self.soil, Soil),
        ):
            if not isinstance(value, kind):
                expected = " or ".join(k.__name__ for k in kind) if isinstance(kind, tuple) else kind.__name__
                raise TypeError(f"{name} must be a bhtypes {expected}, got {type(value).__name__}")
        _check_fit(self.pipe, self.borehole)


def _check_fit(pipe: Pipe, borehole: Borehole) -> None:
    """The pipe lies inside the borehole wall (it may touch it)."""
    if isinstance(pipe, Coaxial):
        extent, what = pipe.outer.outer_radius_m, "the outer tube's outer radius"
    else:
        extent, what = pipe.leg_offset_m + pipe.tube.outer_radius_m, "the legs (leg_offset_m + tube outer radius)"
    if extent > borehole.radius_m * (1.0 + 1e-12):
        raise ValueError(
            f"the pipe does not fit in the borehole: {what} is {extent:.6g} m, "
            f"more than the borehole radius {borehole.radius_m:.6g} m"
        )
