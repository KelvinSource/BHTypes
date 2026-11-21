"""The borehole itself: its length and diameter, the same wherever it is drilled.

Where a borehole is placed -- its position, buried depth, tilt and orientation -- belongs to
the bore field, not to the borehole, and is out of scope here.

Plain data with validation. Conversions to other packages' conventions are in
:mod:`bhtypes.convert`.
"""

from __future__ import annotations

from dataclasses import dataclass

from bhtypes._checks import positive


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
