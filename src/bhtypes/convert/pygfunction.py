"""pygfunction conventions.

``to_pygfunction(obj)`` gives keyword arguments for pygfunction's pipe models::

    gt.pipes.MultipleUTube(**to_pygfunction(pipe), **to_pygfunction(soil), **to_pygfunction(grout),
                           borehole=borehole, R_fp=R_fp)

Pass ``soil.thermal_diffusivity_m2_per_s`` as ``alpha`` to pygfunction's g-functions, and
:func:`pipe_type` as ``pipe_type_str`` to ``gFunction.from_static_params``.
"""

from __future__ import annotations

from functools import singledispatch

from bhtypes.convert import _unsupported
from bhtypes.materials import Grout, Soil
from bhtypes.pipes import Coaxial, DoubleUTube, SingleUTube


@singledispatch
def to_pygfunction(obj) -> dict:
    """Keyword arguments for pygfunction (see the module docstring)."""
    raise _unsupported("pygfunction", obj)


@to_pygfunction.register(Soil)
def _(soil: Soil) -> dict:
    return {"k_s": soil.thermal_conductivity_w_per_m_k}


@to_pygfunction.register(Grout)
def _(grout: Grout) -> dict:
    return {"k_g": grout.thermal_conductivity_w_per_m_k}


@to_pygfunction.register(SingleUTube)
def _(pipe: SingleUTube) -> dict:
    """``pos``, ``r_in``, ``r_out`` for ``pygfunction.pipes.SingleUTube``."""
    return {"pos": pipe.leg_positions(), "r_in": pipe.inner_radius_m, "r_out": pipe.outer_radius_m}


@to_pygfunction.register(DoubleUTube)
def _(pipe: DoubleUTube) -> dict:
    """``pos`` (inlets first), ``r_in``, ``r_out``, ``nPipes``, ``config`` for ``pygfunction.pipes.MultipleUTube``."""
    return {
        "pos": pipe.leg_positions(),
        "r_in": pipe.inner_radius_m,
        "r_out": pipe.outer_radius_m,
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
    """``(r_in, r_out)`` in pygfunction's order: the inlet pipe first, then the outlet pipe."""
    first, second = (
        (pipe.inner_pipe_radii_m, pipe.outer_pipe_radii_m)
        if pipe.inlet == "centre"
        else (pipe.outer_pipe_radii_m, pipe.inner_pipe_radii_m)
    )
    return (first[0], second[0]), (first[1], second[1])


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
    return "COAXIAL_ANNULAR_OUT" if pipe.inlet == "centre" else "COAXIAL_ANNULAR_IN"
