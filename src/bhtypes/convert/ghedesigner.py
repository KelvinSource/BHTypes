"""GHEDesigner input-file conventions.

``to_ghedesigner(obj)`` writes a ``soil``, ``grout`` or ``pipe`` block; the
``*_from_ghedesigner`` functions read one. Blocks use the input-file keys
(``conductivity``, ``rho_cp``, ``inner_diameter``, ...). For soil and grout the readers also
accept GHEDesigner's newer unit-suffixed keys (``thermal_conductivity_w_per_m_k``, ...).

GHEDesigner cannot represent diagonal double U-tube inlets, an annulus-inlet coaxial
exchanger, or different heat capacities for the two coaxial pipes; those are refused.
Reading a GHEDesigner double U-tube gives adjacent inlets and a coaxial gives a centre
inlet -- what GHEDesigner itself assumes.

This module is a bridge until GHEDesigner reads and writes bhtypes itself.
"""

from __future__ import annotations

from functools import singledispatch

from bhtypes.convert import _unsupported
from bhtypes.materials import Grout, Soil
from bhtypes.pipes import DEFAULT_ROUGHNESS_M, Coaxial, DoubleUTube, Pipe, SingleUTube

_DOUBLE_U_FLOWS = {"DOUBLEUTUBEPARALLEL": "parallel", "DOUBLEUTUBESERIES": "series"}


@singledispatch
def to_ghedesigner(obj) -> dict:
    """A GHEDesigner input-file block for ``obj`` (see the module docstring)."""
    raise _unsupported("GHEDesigner", obj)


@to_ghedesigner.register(Soil)
def _(soil: Soil) -> dict:
    return {
        "conductivity": soil.thermal_conductivity_w_per_m_k,
        "rho_cp": soil.volumetric_heat_capacity_j_per_m3_k,
        "undisturbed_temp": soil.undisturbed_temperature_c,
    }


@to_ghedesigner.register(Grout)
def _(grout: Grout) -> dict:
    return {"conductivity": grout.thermal_conductivity_w_per_m_k, "rho_cp": grout.volumetric_heat_capacity_j_per_m3_k}


def _u_tube(pipe: SingleUTube | DoubleUTube) -> dict:
    return {
        "inner_diameter": pipe.inner_diameter_m,
        "outer_diameter": pipe.outer_diameter_m,
        "shank_spacing": pipe.shank_spacing_m,
        "roughness": pipe.roughness_m,
        "conductivity": pipe.thermal_conductivity_w_per_m_k,
        "rho_cp": pipe.volumetric_heat_capacity_j_per_m3_k,
    }


@to_ghedesigner.register(SingleUTube)
def _(pipe: SingleUTube) -> dict:
    return {"arrangement": "SINGLEUTUBE", **_u_tube(pipe)}


@to_ghedesigner.register(DoubleUTube)
def _(pipe: DoubleUTube) -> dict:
    if pipe.inlets != "adjacent":
        raise ValueError("GHEDesigner models double U-tubes with adjacent inlets only")
    return {"arrangement": f"DOUBLEUTUBE{pipe.flow.upper()}", **_u_tube(pipe)}


@to_ghedesigner.register(Coaxial)
def _(pipe: Coaxial) -> dict:
    if pipe.inner_pipe_volumetric_heat_capacity_j_per_m3_k != pipe.outer_pipe_volumetric_heat_capacity_j_per_m3_k:
        raise ValueError("GHEDesigner takes one rho_cp for both coaxial pipes")
    if pipe.inlet != "centre":
        raise ValueError("GHEDesigner models coaxial exchangers with the centre pipe as the inlet only")
    return {
        "arrangement": "COAXIAL",
        "inner_pipe_d_in": pipe.inner_pipe_inner_diameter_m,
        "inner_pipe_d_out": pipe.inner_pipe_outer_diameter_m,
        "outer_pipe_d_in": pipe.outer_pipe_inner_diameter_m,
        "outer_pipe_d_out": pipe.outer_pipe_outer_diameter_m,
        "roughness": pipe.roughness_m,
        "conductivity_inner": pipe.inner_pipe_thermal_conductivity_w_per_m_k,
        "conductivity_outer": pipe.outer_pipe_thermal_conductivity_w_per_m_k,
        "rho_cp": pipe.inner_pipe_volumetric_heat_capacity_j_per_m3_k,
    }


def _key(block: dict, short: str, long: str) -> float:
    """A value under GHEDesigner's input-file key (``conductivity``) or its unit-suffixed key."""
    if short in block and long in block:
        raise ValueError(f"give {short!r} or {long!r}, not both")
    try:
        return block[short] if short in block else block[long]
    except KeyError:
        raise KeyError(f"missing {short!r} (or {long!r})") from None


def soil_from_ghedesigner(block: dict) -> Soil:
    return Soil(
        _key(block, "conductivity", "thermal_conductivity_w_per_m_k"),
        _key(block, "rho_cp", "volumetric_heat_capacity_j_per_m3_k"),
        _key(block, "undisturbed_temp", "undisturbed_ground_temperature_c"),
    )


def grout_from_ghedesigner(block: dict) -> Grout:
    return Grout(
        _key(block, "conductivity", "thermal_conductivity_w_per_m_k"),
        _key(block, "rho_cp", "volumetric_heat_capacity_j_per_m3_k"),
    )


def _u_tube_fields(block: dict) -> dict:
    return {
        "inner_diameter_m": block["inner_diameter"],
        "outer_diameter_m": block["outer_diameter"],
        "shank_spacing_m": block["shank_spacing"],
        "thermal_conductivity_w_per_m_k": block["conductivity"],
        "volumetric_heat_capacity_j_per_m3_k": block["rho_cp"],
        "roughness_m": block.get("roughness", DEFAULT_ROUGHNESS_M),
    }


def pipe_from_ghedesigner(block: dict) -> Pipe:
    """A GHEDesigner ``pipe`` block as the bhtypes pipe its ``arrangement`` names."""
    arrangement = str(block.get("arrangement", "")).upper()
    if arrangement == "SINGLEUTUBE":
        if block.get("num_pipes", 1) != 1:
            raise ValueError(f"SingleUTube holds one U-tube; got num_pipes={block['num_pipes']!r}")
        return SingleUTube(**_u_tube_fields(block))
    if arrangement in _DOUBLE_U_FLOWS:
        return DoubleUTube(**_u_tube_fields(block), inlets="adjacent", flow=_DOUBLE_U_FLOWS[arrangement])
    if arrangement == "COAXIAL":
        return Coaxial(
            inner_pipe_inner_diameter_m=block["inner_pipe_d_in"],
            inner_pipe_outer_diameter_m=block["inner_pipe_d_out"],
            outer_pipe_inner_diameter_m=block["outer_pipe_d_in"],
            outer_pipe_outer_diameter_m=block["outer_pipe_d_out"],
            inner_pipe_thermal_conductivity_w_per_m_k=block["conductivity_inner"],
            outer_pipe_thermal_conductivity_w_per_m_k=block["conductivity_outer"],
            inner_pipe_volumetric_heat_capacity_j_per_m3_k=block["rho_cp"],
            outer_pipe_volumetric_heat_capacity_j_per_m3_k=block["rho_cp"],
            roughness_m=block.get("roughness", DEFAULT_ROUGHNESS_M),
            inlet="centre",
        )
    raise ValueError(f"unknown GHEDesigner pipe arrangement {block.get('arrangement')!r}")
