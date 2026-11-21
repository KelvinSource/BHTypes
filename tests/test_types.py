"""The data types: validation and derived geometry."""

import dataclasses
from math import hypot, isclose

import pytest

from bhtypes import Coaxial, DoubleUTube, Grout, SingleUTube, Soil

U = {
    "inner_diameter_m": 0.03398,
    "outer_diameter_m": 0.04216,
    "shank_spacing_m": 0.03404,
    "thermal_conductivity_w_per_m_k": 0.4,
    "volumetric_heat_capacity_j_per_m3_k": 2.07e6,
}
COAX = {
    "inner_pipe_inner_diameter_m": 0.0442,
    "inner_pipe_outer_diameter_m": 0.050,
    "outer_pipe_inner_diameter_m": 0.0974,
    "outer_pipe_outer_diameter_m": 0.110,
    "inner_pipe_thermal_conductivity_w_per_m_k": 0.4,
    "outer_pipe_thermal_conductivity_w_per_m_k": 0.4,
    "inner_pipe_volumetric_heat_capacity_j_per_m3_k": 1.5e6,
    "outer_pipe_volumetric_heat_capacity_j_per_m3_k": 1.5e6,
}


def test_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        SingleUTube(**U).outer_diameter_m = 0.05


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("inner_diameter_m", 0.05, "must be smaller than"),
        ("outer_diameter_m", -1.0, "finite positive"),
        ("shank_spacing_m", -0.01, "non-negative"),
        ("thermal_conductivity_w_per_m_k", 0.0, "finite positive"),
        ("volumetric_heat_capacity_j_per_m3_k", float("nan"), "finite positive"),
        ("roughness_m", -1e-6, "non-negative"),
    ],
)
def test_u_tube_validation(field, value, message):
    with pytest.raises(ValueError, match=message):
        SingleUTube(**{**U, field: value})


def test_double_u_options_validated():
    with pytest.raises(ValueError, match="inlets must be one of"):
        DoubleUTube(**U, inlets="opposite")
    with pytest.raises(ValueError, match="flow must be one of"):
        DoubleUTube(**U, flow="mixed")


def test_coaxial_validation():
    with pytest.raises(ValueError, match="fit inside"):
        Coaxial(**{**COAX, "inner_pipe_outer_diameter_m": 0.098})
    with pytest.raises(ValueError, match="inlet must be one of"):
        Coaxial(**COAX, inlet="outer")


def test_materials():
    soil = Soil(2.6, 2.5e6, 12.0)
    assert soil.thermal_diffusivity_m2_per_s == 2.6 / 2.5e6
    with pytest.raises(ValueError, match="finite positive"):
        Grout(0.0, 3.4e6)
    assert Grout(2.4, 3.4e6).thermal_diffusivity_m2_per_s == 2.4 / 3.4e6


def test_derived_u_tube_geometry():
    pipe = SingleUTube(**U)
    assert pipe.outer_radius_m == 0.04216 / 2
    assert pipe.leg_offset_m == 0.03404 / 2 + 0.04216 / 2
    wall = (0.04216 - 0.03398) / 2
    assert isclose(pipe.dimension_ratio, 0.04216 / wall, rel_tol=1e-12)


def test_single_u_legs_are_opposite():
    (x0, y0), (x1, _y1) = SingleUTube(**U).leg_positions()
    assert isclose(x0, -x1, rel_tol=1e-15)
    assert isclose(hypot(x0, y0), SingleUTube(**U).leg_offset_m)


def _angle_deg(a, b):
    from math import acos, degrees

    return degrees(acos((a[0] * b[0] + a[1] * b[1]) / (hypot(*a) * hypot(*b))))


@pytest.mark.parametrize(("inlets", "angle"), [("adjacent", 90.0), ("diagonal", 180.0)])
def test_double_u_inlets_lead_the_leg_list(inlets, angle):
    legs = DoubleUTube(**U, inlets=inlets).leg_positions()
    offset = DoubleUTube(**U).leg_offset_m
    assert all(isclose(hypot(*xy), offset, rel_tol=1e-12) for xy in legs)
    assert isclose(_angle_deg(legs[0], legs[1]), angle, abs_tol=1e-9)  # the two inlets
    assert isclose(_angle_deg(legs[2], legs[3]), angle, abs_tol=1e-9)  # the two outlets


def test_coaxial_derived_geometry():
    pipe = Coaxial(**COAX)
    assert pipe.inner_pipe_radii_m == (0.0442 / 2, 0.050 / 2)
    assert pipe.outer_pipe_radii_m == (0.0974 / 2, 0.110 / 2)
    assert isclose(pipe.outer_pipe_dimension_ratio, 0.110 / ((0.110 - 0.0974) / 2), rel_tol=1e-12)


def test_types_know_nothing_about_other_packages():
    """Package-specific details live in bhtypes.convert, not on the types."""
    for cls in (Soil, Grout, SingleUTube, DoubleUTube, Coaxial):
        names = {n.lower() for n in dir(cls)}
        assert not any(target in n for n in names for target in ("pygfunction", "bhresist", "ghedesigner"))
