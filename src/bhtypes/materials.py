"""Ground and grout thermal properties.

Plain data with validation. Conversions to other packages' conventions are in
:mod:`bhtypes.convert`.
"""

from __future__ import annotations

from dataclasses import dataclass

from bhtypes._checks import positive


@dataclass(frozen=True, slots=True)
class Soil:
    """The ground around the borehole.

    Attributes
    ----------
    thermal_conductivity_w_per_m_k : float
    volumetric_heat_capacity_j_per_m3_k : float
    undisturbed_temperature_c : float
        Far-field (undisturbed) ground temperature.
    """

    thermal_conductivity_w_per_m_k: float
    volumetric_heat_capacity_j_per_m3_k: float
    undisturbed_temperature_c: float

    def __post_init__(self) -> None:
        positive("thermal_conductivity_w_per_m_k", self.thermal_conductivity_w_per_m_k)
        positive("volumetric_heat_capacity_j_per_m3_k", self.volumetric_heat_capacity_j_per_m3_k)

    @property
    def thermal_diffusivity_m2_per_s(self) -> float:
        return self.thermal_conductivity_w_per_m_k / self.volumetric_heat_capacity_j_per_m3_k


@dataclass(frozen=True, slots=True)
class Grout:
    """The backfill between the pipes and the borehole wall."""

    thermal_conductivity_w_per_m_k: float
    volumetric_heat_capacity_j_per_m3_k: float

    def __post_init__(self) -> None:
        positive("thermal_conductivity_w_per_m_k", self.thermal_conductivity_w_per_m_k)
        positive("volumetric_heat_capacity_j_per_m3_k", self.volumetric_heat_capacity_j_per_m3_k)

    @property
    def thermal_diffusivity_m2_per_s(self) -> float:
        return self.thermal_conductivity_w_per_m_k / self.volumetric_heat_capacity_j_per_m3_k
