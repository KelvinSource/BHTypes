"""Pipes: a :class:`Tube`, and the arrangements of tubes in a borehole.

A :class:`Tube` is one pipe: its diameters and wall material.  The arrangements place tubes
in the borehole: :class:`SingleUTube` and :class:`DoubleUTube` (a tube bent into one or two
U-tubes, with the gap between the legs), and :class:`Coaxial` (a center tube inside an outer
tube).

Plain data: every dimension is stored once, under a name that says what it is and in what
unit, with validation and derived geometry. Conversions to other packages' conventions are
in :mod:`bhtypes.convert`.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin

from bhtypes._checks import choice, non_negative, positive, wall

#: pygfunction's default pipe roughness [m] (smooth plastic pipe).
DEFAULT_ROUGHNESS_M = 1.0e-6

DOUBLE_U_INLETS = ("adjacent", "diagonal")
DOUBLE_U_FLOWS = ("parallel", "series")
COAXIAL_INLETS = ("center", "annulus")


@dataclass(frozen=True, slots=True)
class Tube:
    """One pipe: its wall and material.

    Attributes
    ----------
    inner_diameter_m, outer_diameter_m : float
    thermal_conductivity_w_per_m_k : float
        Of the pipe wall.
    volumetric_heat_capacity_j_per_m3_k : float
        Of the pipe wall.
    roughness_m : float
        Absolute roughness of the inner surface.
    """

    inner_diameter_m: float
    outer_diameter_m: float
    thermal_conductivity_w_per_m_k: float
    volumetric_heat_capacity_j_per_m3_k: float
    roughness_m: float = DEFAULT_ROUGHNESS_M

    def __post_init__(self) -> None:
        wall("inner_diameter_m", self.inner_diameter_m, "outer_diameter_m", self.outer_diameter_m)
        positive("thermal_conductivity_w_per_m_k", self.thermal_conductivity_w_per_m_k)
        positive("volumetric_heat_capacity_j_per_m3_k", self.volumetric_heat_capacity_j_per_m3_k)
        non_negative("roughness_m", self.roughness_m)

    @property
    def inner_radius_m(self) -> float:
        return self.inner_diameter_m / 2.0

    @property
    def outer_radius_m(self) -> float:
        return self.outer_diameter_m / 2.0

    @property
    def wall_thickness_m(self) -> float:
        return (self.outer_diameter_m - self.inner_diameter_m) / 2.0

    @property
    def dimension_ratio(self) -> float:
        """Outer diameter over wall thickness (DR / SDR)."""
        r_in, r_out = self.inner_radius_m, self.outer_radius_m
        return (2.0 * r_out) / (r_out - r_in)  # the 0.1-0.2 arithmetic, so converted values do not change


def _check_tube(name: str, tube) -> None:
    if not isinstance(tube, Tube):
        raise TypeError(f"{name} must be a bhtypes Tube, got {type(tube).__name__}")


def _ring(radius: float, n_tubes: int) -> list[tuple[float, float]]:
    """Leg centers around the borehole axis, in GHEDesigner's ``Pipe.place_pipes`` order and arithmetic.

    For each U-tube ``i``: its first leg at angle ``2 i dt + pi``, its second at ``2 i dt + pi + dt``,
    with ``dt = pi / n_tubes``. Using the same arithmetic keeps positions identical to GHEDesigner's.
    """
    dt = pi / float(n_tubes)
    legs = []
    for i in range(n_tubes):
        legs.append((radius * cos(2.0 * i * dt + pi), radius * sin(2.0 * i * dt + pi)))
        legs.append((radius * cos(2.0 * i * dt + pi + dt), radius * sin(2.0 * i * dt + pi + dt)))
    return legs


@dataclass(frozen=True, slots=True)
class _UTube:
    """A tube bent into U-tubes; fields and derived geometry shared by single and double U-tubes."""

    tube: Tube
    shank_spacing_m: float  # gap between the outer walls of the two legs of a U-tube: o<-- s -->o

    def __post_init__(self) -> None:
        _check_tube("tube", self.tube)
        non_negative("shank_spacing_m", self.shank_spacing_m)

    @property
    def leg_offset_m(self) -> float:
        """Distance from the borehole axis to each leg's center."""
        return self.shank_spacing_m / 2.0 + self.tube.outer_radius_m


@dataclass(frozen=True, slots=True)
class SingleUTube(_UTube):
    """One U-tube: two legs either side of the borehole axis."""

    def leg_positions(self) -> list[tuple[float, float]]:
        """``[(x, y) inlet, (x, y) outlet]`` [m], relative to the borehole axis."""
        return _ring(self.leg_offset_m, 1)


@dataclass(frozen=True, slots=True)
class DoubleUTube(_UTube):
    """Two U-tubes at the same distance from the borehole axis, 90 degrees apart.

    Attributes
    ----------
    inlets : {'adjacent', 'diagonal'}
        Whether the two downward (inlet) legs sit next to each other or opposite.
    flow : {'parallel', 'series'}
        Whether the U-tubes share the flow or carry it one after the other.
    """

    inlets: str = "adjacent"
    flow: str = "parallel"

    def __post_init__(self) -> None:
        _UTube.__post_init__(self)
        choice("inlets", self.inlets, DOUBLE_U_INLETS)
        choice("flow", self.flow, DOUBLE_U_FLOWS)

    def leg_positions(self) -> list[tuple[float, float]]:
        """``[inlet, inlet, outlet, outlet]`` (x, y) [m], relative to the borehole axis."""
        first_in, first_out, second_in, second_out = _ring(self.leg_offset_m, 2)
        if self.inlets == "adjacent":
            # the second leg of each U-tube in GHEDesigner's ring sits 90 degrees from the first
            return [first_in, first_out, second_in, second_out]
        return [first_in, second_in, first_out, second_out]


@dataclass(frozen=True, slots=True)
class Coaxial:
    """A center tube inside an outer tube; the fluid goes down one channel and up the other.

    Attributes
    ----------
    center, outer : Tube
        The center tube, and the outer tube around it; the annulus lies between them.
    inlet : {'center', 'annulus'}
        Which channel carries the fluid down.
    """

    center: Tube
    outer: Tube
    inlet: str = "center"

    def __post_init__(self) -> None:
        _check_tube("center", self.center)
        _check_tube("outer", self.outer)
        if not self.center.outer_diameter_m < self.outer.inner_diameter_m:
            raise ValueError(
                "the center tube must fit inside the outer tube (center.outer_diameter_m < outer.inner_diameter_m)"
            )
        choice("inlet", self.inlet, COAXIAL_INLETS)

    @property
    def annulus_radii_m(self) -> tuple[float, float]:
        """``(inner, outer)`` radius of the annulus: the center tube's outer wall, the outer tube's inner wall."""
        return self.center.outer_radius_m, self.outer.inner_radius_m


Pipe = SingleUTube | DoubleUTube | Coaxial
