"""bhresist conventions.

``to_bhresist(obj)`` gives keyword arguments for bhresist's ``Borehole.init_*_borehole``;
:func:`init_method` names the method for a pipe::

    bh = bhr.borehole.Borehole()
    getattr(bh, init_method(pipe))(**to_bhresist(pipe), **to_bhresist(grout), **to_bhresist(soil),
                                   **to_bhresist(borehole), fluid=fluid)

For a :class:`~bhtypes.Borehole` it gives ``length`` and ``borehole_diameter``.

bhresist has no series double U-tube model, so those are refused rather than computed as
parallel.
"""

from __future__ import annotations

from functools import singledispatch

from bhtypes.borehole import Borehole
from bhtypes.convert import _unsupported
from bhtypes.materials import Grout, Soil
from bhtypes.pipes import Coaxial, DoubleUTube, SingleUTube


@singledispatch
def to_bhresist(obj) -> dict:
    """Keyword arguments for bhresist (see the module docstring)."""
    raise _unsupported("bhresist", obj)


@to_bhresist.register(Borehole)
def _(borehole: Borehole) -> dict:
    return {"length": borehole.length_m, "borehole_diameter": borehole.diameter_m}


@to_bhresist.register(Soil)
def _(soil: Soil) -> dict:
    return {"soil_conductivity": soil.thermal_conductivity_w_per_m_k}


@to_bhresist.register(Grout)
def _(grout: Grout) -> dict:
    return {"grout_conductivity": grout.thermal_conductivity_w_per_m_k}


def _u_tube(pipe: SingleUTube | DoubleUTube) -> dict:
    return {
        "pipe_outer_diameter": pipe.outer_diameter_m,
        "pipe_dimension_ratio": pipe.dimension_ratio,
        "shank_space": pipe.leg_offset_m,  # bhresist: borehole axis to leg centre
        "pipe_conductivity": pipe.thermal_conductivity_w_per_m_k,
    }


@to_bhresist.register(SingleUTube)
def _(pipe: SingleUTube) -> dict:
    return _u_tube(pipe)


@to_bhresist.register(DoubleUTube)
def _(pipe: DoubleUTube) -> dict:
    if pipe.flow != "parallel":
        raise ValueError("bhresist models double U-tubes in parallel only")
    return {**_u_tube(pipe), "pipe_inlet_arrangement": pipe.inlets.upper()}


@to_bhresist.register(Coaxial)
def _(pipe: Coaxial) -> dict:
    return {
        "outer_pipe_outer_diameter": pipe.outer_pipe_outer_diameter_m,
        "outer_pipe_dimension_ratio": pipe.outer_pipe_dimension_ratio,
        "outer_pipe_conductivity": pipe.outer_pipe_thermal_conductivity_w_per_m_k,
        "inner_pipe_outer_diameter": pipe.inner_pipe_outer_diameter_m,
        "inner_pipe_dimension_ratio": pipe.inner_pipe_dimension_ratio,
        "inner_pipe_conductivity": pipe.inner_pipe_thermal_conductivity_w_per_m_k,
    }


@singledispatch
def init_method(pipe) -> str:
    """Name of the bhresist ``Borehole`` method that takes :func:`to_bhresist`'s keyword arguments."""
    raise _unsupported("bhresist", pipe)


@init_method.register(SingleUTube)
def _(pipe: SingleUTube) -> str:
    return "init_single_u_borehole"


@init_method.register(DoubleUTube)
def _(pipe: DoubleUTube) -> str:
    return "init_double_u_borehole"


@init_method.register(Coaxial)
def _(pipe: Coaxial) -> str:
    return "init_coaxial_borehole"
