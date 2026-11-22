"""Conversions, without the target packages installed, and how converters are extended."""

import dataclasses

import pytest

from bhtypes import Coaxial, DoubleUTube, Grout, SingleUTube, Soil, Tube
from bhtypes.convert.bhresist import init_method, to_bhresist
from bhtypes.convert.pygfunction import coaxial_radii, pipe_type, to_pygfunction

TUBE = Tube(0.03398, 0.04216, 0.4, 2.07e6)
SHANK = 0.03404
CENTRE, OUTER = Tube(0.0442, 0.050, 0.4, 1.5e6), Tube(0.0974, 0.110, 0.4, 1.5e6)


def test_materials():
    assert to_bhresist(Soil(2.6, 2.5e6)) == {"soil_conductivity": 2.6}
    assert to_pygfunction(Grout(2.4, 3.4e6)) == {"k_g": 2.4}
    assert to_bhresist(Grout(2.4, 3.4e6)) == {"grout_conductivity": 2.4}


def test_pygfunction_u_tubes():
    single, double = SingleUTube(TUBE, SHANK), DoubleUTube(TUBE, SHANK, flow="series")
    assert to_pygfunction(single) == {
        "pos": single.leg_positions(),
        "r_in": TUBE.inner_diameter_m / 2,
        "r_out": TUBE.outer_diameter_m / 2,
    }
    assert to_pygfunction(double)["config"] == "series"
    assert to_pygfunction(double)["nPipes"] == 2
    assert pipe_type(single) == "SINGLE_UTUBE"
    assert pipe_type(double) == "DOUBLE_UTUBE_SERIES"


def test_pygfunction_coaxial_radii_follow_the_inlet():
    assert coaxial_radii(Coaxial(CENTRE, OUTER)) == ((0.0442 / 2, 0.0974 / 2), (0.050 / 2, 0.110 / 2))
    assert coaxial_radii(Coaxial(CENTRE, OUTER, inlet="annulus")) == ((0.0974 / 2, 0.0442 / 2), (0.110 / 2, 0.050 / 2))
    assert pipe_type(Coaxial(CENTRE, OUTER)) == "COAXIAL_ANNULAR_OUT"
    assert pipe_type(Coaxial(CENTRE, OUTER, inlet="annulus")) == "COAXIAL_ANNULAR_IN"


def test_bhresist():
    assert to_bhresist(DoubleUTube(TUBE, SHANK, inlets="diagonal"))["pipe_inlet_arrangement"] == "DIAGONAL"
    with pytest.raises(ValueError, match="parallel only"):
        to_bhresist(DoubleUTube(TUBE, SHANK, flow="series"))
    assert [init_method(p) for p in (SingleUTube(TUBE, SHANK), DoubleUTube(TUBE, SHANK), Coaxial(CENTRE, OUTER))] == [
        "init_single_u_borehole",
        "init_double_u_borehole",
        "init_coaxial_borehole",
    ]
    assert set(to_bhresist(Coaxial(CENTRE, OUTER))) == {
        "outer_pipe_outer_diameter",
        "outer_pipe_dimension_ratio",
        "outer_pipe_conductivity",
        "inner_pipe_outer_diameter",
        "inner_pipe_dimension_ratio",
        "inner_pipe_conductivity",
    }


# --- extending converters ----------------------------------------------------------------


@pytest.mark.parametrize("convert", [to_pygfunction, to_bhresist, pipe_type, init_method])
def test_unknown_types_get_a_clear_error(convert):
    with pytest.raises(TypeError, match=r"register one with \.register"):
        convert(object())


def test_new_types_can_be_registered_without_changing_bhtypes():
    @dataclasses.dataclass(frozen=True)
    class TripleUTube:
        outer_diameter_m: float

    @to_bhresist.register(TripleUTube)
    def _(pipe):
        return {"pipe_outer_diameter": pipe.outer_diameter_m, "n_u_tubes": 3}

    assert to_bhresist(TripleUTube(0.04)) == {"pipe_outer_diameter": 0.04, "n_u_tubes": 3}
    assert "pipe_inlet_arrangement" in to_bhresist(DoubleUTube(TUBE, SHANK))  # existing types unaffected


def test_subclass_gets_its_own_conversion_parent_unchanged():
    @dataclasses.dataclass(frozen=True, slots=True)
    class LabelledSingleUTube(SingleUTube):
        label: str = ""

    @to_bhresist.register(LabelledSingleUTube)
    def _(pipe):
        return {**to_bhresist.dispatch(SingleUTube)(pipe), "name": pipe.label}

    labelled = LabelledSingleUTube(TUBE, SHANK, label="field A")
    assert to_bhresist(labelled)["name"] == "field A"
    assert "name" not in to_bhresist(SingleUTube(TUBE, SHANK))
