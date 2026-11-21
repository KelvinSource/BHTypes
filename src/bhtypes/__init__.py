"""bhtypes: plain data types for a borehole heat exchanger's cross-section.

``Soil``, ``Grout`` and the pipe geometries ``SingleUTube``, ``DoubleUTube`` and ``Coaxial``,
as frozen dataclasses with units in their field names. No dependencies.

Conversions to and from the conventions of pygfunction, bhresist and GHEDesigner live in
:mod:`bhtypes.convert`, one module per package, kept apart from the types so other packages
can supply their own.

Deliberately out of scope: fluids -- use SecondaryCoolantProps (``scp``), which
pygfunction, bhresist and GHEDesigner already share -- and borehole geometry -- use
``pygfunction.boreholes.Borehole``.
"""

from bhtypes.materials import Grout, Soil
from bhtypes.pipes import (
    COAXIAL_INLETS,
    DEFAULT_ROUGHNESS_M,
    DOUBLE_U_FLOWS,
    DOUBLE_U_INLETS,
    Coaxial,
    DoubleUTube,
    Pipe,
    SingleUTube,
)

__all__ = [
    "COAXIAL_INLETS",
    "DEFAULT_ROUGHNESS_M",
    "DOUBLE_U_FLOWS",
    "DOUBLE_U_INLETS",
    "Coaxial",
    "DoubleUTube",
    "Grout",
    "Pipe",
    "SingleUTube",
    "Soil",
]
