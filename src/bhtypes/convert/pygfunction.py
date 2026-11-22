"""pygfunction conventions.

``to_pygfunction(obj)`` gives keyword arguments for pygfunction's pipe models::

    gt.pipes.MultipleUTube(**to_pygfunction(pipe), **to_pygfunction(soil), **to_pygfunction(grout),
                           borehole=borehole, R_fp=R_fp)

For a :class:`~bhtypes.Borehole` it gives the ``H`` and ``r_b`` of pygfunction's ``Borehole`` and
field constructors; the buried depth and positions are given there::

    field = gt.borefield.Borefield.rectangle_field(4, 3, 6.0, 6.0, D=4.0, **to_pygfunction(borehole))

Pass ``soil.thermal_diffusivity_m2_per_s`` as ``alpha`` to pygfunction's g-functions, and
:func:`pipe_type` as ``pipe_type_str`` to ``gFunction.from_static_params``.
"""

from __future__ import annotations

from functools import singledispatch

from bhtypes.borehole import Borehole
from bhtypes.convert import _unsupported
from bhtypes.materials import Grout, Soil
from bhtypes.pipes import Coaxial, DoubleUTube, SingleUTube


@singledispatch
def to_pygfunction(obj) -> dict:
    """Keyword arguments for pygfunction (see the module docstring)."""
    raise _unsupported("pygfunction", obj)


@to_pygfunction.register(Borehole)
def _(borehole: Borehole) -> dict:
    """``H`` and ``r_b`` for pygfunction's ``Borefield`` constructors and ``Borehole`` (give ``D`` there)."""
    return {"H": borehole.length_m, "r_b": borehole.radius_m}


@to_pygfunction.register(Soil)
def _(soil: Soil) -> dict:
    return {"k_s": soil.thermal_conductivity_w_per_m_k}


@to_pygfunction.register(Grout)
def _(grout: Grout) -> dict:
    return {"k_g": grout.thermal_conductivity_w_per_m_k}


@to_pygfunction.register(SingleUTube)
def _(pipe: SingleUTube) -> dict:
    """``pos``, ``r_in``, ``r_out`` for ``pygfunction.pipes.SingleUTube``."""
    return {"pos": pipe.leg_positions(), "r_in": pipe.tube.inner_radius_m, "r_out": pipe.tube.outer_radius_m}


@to_pygfunction.register(DoubleUTube)
def _(pipe: DoubleUTube) -> dict:
    """``pos`` (inlets first), ``r_in``, ``r_out``, ``nPipes``, ``config`` for ``pygfunction.pipes.MultipleUTube``."""
    return {
        "pos": pipe.leg_positions(),
        "r_in": pipe.tube.inner_radius_m,
        "r_out": pipe.tube.outer_radius_m,
        "nPipes": 2,
        "config": pipe.flow,
    }


@to_pygfunction.register(Coaxial)
def _(pipe: Coaxial) -> dict:
    """``pos``, ``r_in``, ``r_out`` for ``pygfunction.pipes.Coaxial``, radii ordered inlet pipe first.

    pygfunction's ``Coaxial`` needs the radii as numpy arrays. numpy is imported here only;
    wherever pygfunction is installed, so is numpy. :func:`coaxial_radii` gives plain tuples.
    """
    import numpy as np

    r_in, r_out = coaxial_radii(pipe)
    return {"pos": (0.0, 0.0), "r_in": np.array(r_in), "r_out": np.array(r_out)}


def coaxial_radii(pipe: Coaxial) -> tuple[tuple[float, float], tuple[float, float]]:
    """``(r_in, r_out)`` in pygfunction's order: the inlet tube first, then the outlet tube."""
    first, second = (pipe.center, pipe.outer) if pipe.inlet == "center" else (pipe.outer, pipe.center)
    return (first.inner_radius_m, second.inner_radius_m), (first.outer_radius_m, second.outer_radius_m)


@singledispatch
def pipe_type(pipe) -> str:
    """pygfunction's ``pipe_type_str`` for ``gFunction.from_static_params``."""
    raise _unsupported("pygfunction pipe type", pipe)


@pipe_type.register(SingleUTube)
def _(pipe: SingleUTube) -> str:
    return "SINGLE_UTUBE"


@pipe_type.register(DoubleUTube)
def _(pipe: DoubleUTube) -> str:
    return f"DOUBLE_UTUBE_{pipe.flow.upper()}"


@pipe_type.register(Coaxial)
def _(pipe: Coaxial) -> str:
    return "COAXIAL_ANNULAR_OUT" if pipe.inlet == "center" else "COAXIAL_ANNULAR_IN"
