"""The data types: validation and derived geometry."""

import dataclasses
from math import hypot, isclose

import pytest

from bhtypes import Coaxial, DoubleUTube, Grout, SingleUTube, Soil, Tube

TUBE = Tube(
    inner_diameter_m=0.03398,
    outer_diameter_m=0.04216,
    thermal_conductivity_w_per_m_k=0.4,
    volumetric_heat_capacity_j_per_m3_k=2.07e6,
)
SHANK = 0.03404
CENTRE = Tube(0.0442, 0.050, 0.4, 1.5e6)
OUTER = Tube(0.0974, 0.110, 0.4, 1.5e6)


def test_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        TUBE.outer_diameter_m = 0.05
    with pytest.raises(dataclasses.FrozenInstanceError):
        SingleUTube(TUBE, SHANK).shank_spacing_m = 0.05


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("inner_diameter_m", 0.05, "must be smaller than"),
        ("outer_diameter_m", -1.0, "finite positive"),
        ("thermal_conductivity_w_per_m_k", 0.0, "finite positive"),
        ("volumetric_heat_capacity_j_per_m3_k", float("nan"), "finite positive"),
        ("roughness_m", -1e-6, "non-negative"),
    ],
)
def test_tube_validation(field, value, message):
    with pytest.raises(ValueError, match=message):
        dataclasses.replace(TUBE, **{field: value})


def test_derived_tube_geometry():
    assert TUBE.inner_radius_m == 0.03398 / 2
    assert TUBE.outer_radius_m == 0.04216 / 2
    wall = (0.04216 - 0.03398) / 2
    assert isclose(TUBE.wall_thickness_m, wall, rel_tol=1e-12)
    assert isclose(TUBE.dimension_ratio, 0.04216 / wall, rel_tol=1e-12)


def test_u_tube_validation():
    with pytest.raises(ValueError, match="non-negative"):
        SingleUTube(TUBE, -0.01)
    with pytest.raises(TypeError, match="tube must be a bhtypes Tube"):
        SingleUTube({"outer_diameter_m": 0.04}, SHANK)


def test_double_u_options_validated():
    with pytest.raises(ValueError, match="inlets must be one of"):
        DoubleUTube(TUBE, SHANK, inlets="opposite")
    with pytest.raises(ValueError, match="flow must be one of"):
        DoubleUTube(TUBE, SHANK, flow="mixed")


def test_coaxial_validation():
    with pytest.raises(ValueError, match="fit inside"):
        Coaxial(Tube(0.0442, 0.098, 0.4, 1.5e6), OUTER)
    with pytest.raises(ValueError, match="inlet must be one of"):
        Coaxial(CENTRE, OUTER, inlet="outer")
    with pytest.raises(TypeError, match="outer must be a bhtypes Tube"):
        Coaxial(CENTRE, 0.1)


def test_materials():
    soil = Soil(2.6, 2.5e6)
    assert soil.thermal_diffusivity_m2_per_s == 2.6 / 2.5e6
    with pytest.raises(ValueError, match="finite positive"):
        Grout(0.0, 3.4e6)
    assert Grout(2.4, 3.4e6).thermal_diffusivity_m2_per_s == 2.4 / 3.4e6


def test_leg_offset():
    assert SingleUTube(TUBE, SHANK).leg_offset_m == SHANK / 2 + 0.04216 / 2


def test_single_u_legs_are_opposite():
    pipe = SingleUTube(TUBE, SHANK)
    (x0, y0), (x1, _y1) = pipe.leg_positions()
    assert isclose(x0, -x1, rel_tol=1e-15)
    assert isclose(hypot(x0, y0), pipe.leg_offset_m)


def _angle_deg(a, b):
    from math import acos, degrees

    return degrees(acos((a[0] * b[0] + a[1] * b[1]) / (hypot(*a) * hypot(*b))))


@pytest.mark.parametrize(("inlets", "angle"), [("adjacent", 90.0), ("diagonal", 180.0)])
def test_double_u_inlets_lead_the_leg_list(inlets, angle):
    pipe = DoubleUTube(TUBE, SHANK, inlets=inlets)
    legs = pipe.leg_positions()
    assert all(isclose(hypot(*xy), pipe.leg_offset_m, rel_tol=1e-12) for xy in legs)
    assert isclose(_angle_deg(legs[0], legs[1]), angle, abs_tol=1e-9)  # the two inlets
    assert isclose(_angle_deg(legs[2], legs[3]), angle, abs_tol=1e-9)  # the two outlets


def test_coaxial_annulus():
    assert Coaxial(CENTRE, OUTER).annulus_radii_m == (0.050 / 2, 0.0974 / 2)


def test_one_tube_in_several_arrangements():
    """A Tube is a value: the same pipe size can be used in different arrangements."""
    assert SingleUTube(TUBE, SHANK).tube is DoubleUTube(TUBE, SHANK).tube


def test_types_know_nothing_about_other_packages():
    """Package-specific details live in bhtypes.convert, not on the types."""
    for cls in (Soil, Grout, Tube, SingleUTube, DoubleUTube, Coaxial):
        names = {n.lower() for n in dir(cls)}
        assert not any(target in n for n in names for target in ("pygfunction", "bhresist", "ghedesigner"))


def test_leg_positions_are_ghedesigners():
    """Leg centers use GHEDesigner's Pipe.place_pipes arithmetic, so they match it bit for bit.

    Recorded from GHEDesigner 2.1.1 for these dimensions (legs 0.0381 m from the axis).
    """
    single = [(-0.0381, 4.665904304751416e-18), (0.0381, -9.331808609502833e-18)]
    double = [
        (-0.0381, 4.665904304751416e-18),
        (-6.998856457127124e-18, -0.0381),
        (0.0381, -9.331808609502833e-18),
        (1.166476076187854e-17, 0.0381),
    ]
    assert SingleUTube(TUBE, SHANK).leg_positions() == single
    assert DoubleUTube(TUBE, SHANK).leg_positions() == double  # adjacent inlets: GHEDesigner's double U-tube
