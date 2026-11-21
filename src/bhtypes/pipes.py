"""Borehole pipe geometries: single U-tube, double U-tube and coaxial.

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
COAXIAL_INLETS = ("centre", "annulus")


def _ring(radius: float, n_tubes: int) -> list[tuple[float, float]]:
    """Leg centres around the borehole axis, in GHEDesigner's ``Pipe.place_pipes`` order and arithmetic.

    For each U-tube ``i``: its first leg at angle ``2 i dt + pi``, its second at ``2 i dt + pi + dt``,
    with ``dt = pi / n_tubes``. Using the same arithmetic keeps positions identical to GHEDesigner's.
    """
    dt = pi / float(n_tubes)
    legs = []
    for i in range(n_tubes):
        legs.append((radius * cos(2.0 * i * dt + pi), radius * sin(2.0 * i * dt + pi)))
        legs.append((radius * cos(2.0 * i * dt + pi + dt), radius * sin(2.0 * i * dt + pi + dt)))
    return legs


def _dimension_ratio(inner_diameter: float, outer_diameter: float) -> float:
    """Outer diameter over wall thickness (DR / SDR)."""
    r_in, r_out = inner_diameter / 2.0, outer_diameter / 2.0
    return (2.0 * r_out) / (r_out - r_in)


@dataclass(frozen=True, slots=True)
class _UTube:
    """Fields and derived geometry shared by single and double U-tubes."""

    inner_diameter_m: float
    outer_diameter_m: float
    shank_spacing_m: float  # gap between the outer walls of the two legs of a U-tube: o<-- s -->o
    thermal_conductivity_w_per_m_k: float
    volumetric_heat_capacity_j_per_m3_k: float
    roughness_m: float = DEFAULT_ROUGHNESS_M

    def __post_init__(self) -> None:
        wall("inner_diameter_m", self.inner_diameter_m, "outer_diameter_m", self.outer_diameter_m)
        non_negative("shank_spacing_m", self.shank_spacing_m)
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
    def dimension_ratio(self) -> float:
        """Outer diameter over wall thickness (DR / SDR)."""
        return _dimension_ratio(self.inner_diameter_m, self.outer_diameter_m)

    @property
    def leg_offset_m(self) -> float:
        """Distance from the borehole axis to each leg's centre."""
        return self.shank_spacing_m / 2.0 + self.outer_radius_m


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
    """A centre pipe inside an outer pipe; the fluid goes down one channel and up the other.

    Attributes
    ----------
    inlet : {'centre', 'annulus'}
        Which channel carries the fluid down.
    """

    inner_pipe_inner_diameter_m: float
    inner_pipe_outer_diameter_m: float
    outer_pipe_inner_diameter_m: float
    outer_pipe_outer_diameter_m: float
    inner_pipe_thermal_conductivity_w_per_m_k: float
    outer_pipe_thermal_conductivity_w_per_m_k: float
    inner_pipe_volumetric_heat_capacity_j_per_m3_k: float
    outer_pipe_volumetric_heat_capacity_j_per_m3_k: float
    roughness_m: float = DEFAULT_ROUGHNESS_M
    inlet: str = "centre"

    def __post_init__(self) -> None:
        wall(
            "inner_pipe_inner_diameter_m",
            self.inner_pipe_inner_diameter_m,
            "inner_pipe_outer_diameter_m",
            self.inner_pipe_outer_diameter_m,
        )
        wall(
            "outer_pipe_inner_diameter_m",
            self.outer_pipe_inner_diameter_m,
            "outer_pipe_outer_diameter_m",
            self.outer_pipe_outer_diameter_m,
        )
        if not self.inner_pipe_outer_diameter_m < self.outer_pipe_inner_diameter_m:
            raise ValueError(
                "the inner pipe must fit inside the outer pipe "
                "(inner_pipe_outer_diameter_m < outer_pipe_inner_diameter_m)"
            )
        for name in (
            "inner_pipe_thermal_conductivity_w_per_m_k",
            "outer_pipe_thermal_conductivity_w_per_m_k",
            "inner_pipe_volumetric_heat_capacity_j_per_m3_k",
            "outer_pipe_volumetric_heat_capacity_j_per_m3_k",
        ):
            positive(name, getattr(self, name))
        non_negative("roughness_m", self.roughness_m)
        choice("inlet", self.inlet, COAXIAL_INLETS)

    @property
    def inner_pipe_radii_m(self) -> tuple[float, float]:
        """``(inner, outer)`` radius of the centre pipe."""
        return self.inner_pipe_inner_diameter_m / 2.0, self.inner_pipe_outer_diameter_m / 2.0

    @property
    def outer_pipe_radii_m(self) -> tuple[float, float]:
        """``(inner, outer)`` radius of the outer pipe."""
        return self.outer_pipe_inner_diameter_m / 2.0, self.outer_pipe_outer_diameter_m / 2.0

    @property
    def inner_pipe_dimension_ratio(self) -> float:
        return _dimension_ratio(self.inner_pipe_inner_diameter_m, self.inner_pipe_outer_diameter_m)

    @property
    def outer_pipe_dimension_ratio(self) -> float:
        return _dimension_ratio(self.outer_pipe_inner_diameter_m, self.outer_pipe_outer_diameter_m)


Pipe = SingleUTube | DoubleUTube | Coaxial
