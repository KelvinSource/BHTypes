"""Borehole and BoreholeHeatExchanger: validation and conversions, without the target packages installed."""

import dataclasses
from math import sqrt

import pytest

from bhtypes import Borehole, BoreholeHeatExchanger, Coaxial, DoubleUTube, Grout, SingleUTube, Soil, Tube
from bhtypes.convert.bhresist import init_method, to_bhresist
from bhtypes.convert.pygfunction import pipe_type, to_pygfunction

BOREHOLE = Borehole(length_m=210.31, diameter_m=0.1524)


def test_borehole():
    assert BOREHOLE.radius_m == pytest.approx(0.0762)
    with pytest.raises(dataclasses.FrozenInstanceError):
        BOREHOLE.length_m = 100.0


@pytest.mark.parametrize(("field", "value"), [("length_m", 0.0), ("diameter_m", float("nan")), ("length_m", -1.0)])
def test_borehole_validation(field, value):
    with pytest.raises(ValueError, match="finite positive"):
        dataclasses.replace(BOREHOLE, **{field: value})


def test_pygfunction():
    assert to_pygfunction(BOREHOLE) == {"H": 210.31, "r_b": pytest.approx(0.0762)}


def test_bhresist():
    assert to_bhresist(BOREHOLE) == {"length": 210.31, "borehole_diameter": 0.1524}


# --- BoreholeHeatExchanger ----------------------------------------------------------------

TUBE = Tube(0.0274, 0.0334, 0.4, 1.5e6)
BHE_BOREHOLE, GROUT, SOIL = Borehole(150.0, 0.15), Grout(1.5, 3.9e6), Soil(2.5, 2.5e6)
PIPES = {
    "single": SingleUTube(TUBE, 0.032),
    "double": DoubleUTube(TUBE, 0.0266, inlets="diagonal"),
    "coaxial": Coaxial(Tube(0.044, 0.050, 0.4, 1.5e6), Tube(0.097, 0.110, 0.4, 1.5e6)),
}


def bhe(pipe, borehole=BHE_BOREHOLE):
    return BoreholeHeatExchanger(borehole, pipe, GROUT, SOIL)


@pytest.mark.parametrize("name", list(PIPES))
def test_holds_its_parts(name):
    exchanger = bhe(PIPES[name])
    assert (exchanger.borehole, exchanger.pipe, exchanger.grout, exchanger.soil) == (
        BHE_BOREHOLE,
        PIPES[name],
        GROUT,
        SOIL,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        exchanger.grout = Grout(2.0, 3.9e6)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [("borehole", 150.0, "Borehole"), ("pipe", TUBE, "SingleUTube or DoubleUTube or Coaxial"), ("soil", GROUT, "Soil")],
)
def test_parts_are_type_checked(field, value, expected):
    with pytest.raises(TypeError, match=f"{field} must be a bhtypes {expected}"):
        dataclasses.replace(bhe(PIPES["single"]), **{field: value})


@pytest.mark.parametrize("name", ["single", "double"])
def test_u_tube_legs_must_fit(name):
    pipe = PIPES[name]
    edge = pipe.leg_offset_m + TUBE.outer_radius_m  # the legs' outer edge, from the axis
    bhe(pipe, Borehole(150.0, 2 * edge))  # touching the wall is allowed
    with pytest.raises(ValueError, match="does not fit in the borehole"):
        bhe(pipe, Borehole(150.0, 2 * edge * 0.99))


def test_coaxial_must_fit():
    pipe = PIPES["coaxial"]
    bhe(pipe, Borehole(150.0, 0.110))
    with pytest.raises(ValueError, match="outer tube's outer radius"):
        bhe(pipe, Borehole(150.0, 0.105))


def test_double_u_neighbouring_legs_must_not_overlap():
    """Legs 90 degrees apart: centers sqrt(2) leg_offset_m apart, at least 2 outer radii."""
    minimum = 2 * (sqrt(2) - 1) * TUBE.outer_radius_m
    DoubleUTube(TUBE, minimum)
    with pytest.raises(ValueError, match="neighbouring legs overlap"):
        DoubleUTube(TUBE, 0.9 * minimum)
    SingleUTube(TUBE, 0.0)  # a single U-tube's legs are opposite: any non-negative spacing


@pytest.mark.parametrize("name", list(PIPES))
def test_converts_as_its_parts(name):
    pipe = PIPES[name]
    exchanger = bhe(pipe)
    parts = {**to_bhresist(pipe), **to_bhresist(BHE_BOREHOLE), **to_bhresist(GROUT), **to_bhresist(SOIL)}
    assert to_bhresist(exchanger) == parts
    assert init_method(exchanger) == init_method(pipe)
    pygfunction = to_pygfunction(exchanger)
    assert pygfunction.keys() == {**to_pygfunction(pipe), **to_pygfunction(SOIL), **to_pygfunction(GROUT)}.keys()
    assert "H" not in pygfunction  # the borehole needs the field's depth and position too
    assert pipe_type(exchanger) == pipe_type(pipe)
