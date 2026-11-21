"""Conversions, without the target packages installed, and how converters are extended."""

import dataclasses

import pytest

from bhtypes import Coaxial, DoubleUTube, Grout, SingleUTube, Soil
from bhtypes.convert.bhresist import init_method, to_bhresist
from bhtypes.convert.ghedesigner import (
    grout_from_ghedesigner,
    pipe_from_ghedesigner,
    soil_from_ghedesigner,
    to_ghedesigner,
)
from bhtypes.convert.pygfunction import coaxial_radii, pipe_type, to_pygfunction

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


def test_materials():
    assert to_bhresist(Soil(2.6, 2.5e6, 12.0)) == {"soil_conductivity": 2.6}
    assert to_pygfunction(Grout(2.4, 3.4e6)) == {"k_g": 2.4}
    assert to_bhresist(Grout(2.4, 3.4e6)) == {"grout_conductivity": 2.4}


def test_pygfunction_u_tubes():
    single, double = SingleUTube(**U), DoubleUTube(**U, flow="series")
    assert to_pygfunction(single) == {
        "pos": single.leg_positions(),
        "r_in": U["inner_diameter_m"] / 2,
        "r_out": U["outer_diameter_m"] / 2,
    }
    assert to_pygfunction(double)["config"] == "series"
    assert to_pygfunction(double)["nPipes"] == 2
    assert pipe_type(single) == "SINGLE_UTUBE"
    assert pipe_type(double) == "DOUBLE_UTUBE_SERIES"


def test_pygfunction_coaxial_radii_follow_the_inlet():
    assert coaxial_radii(Coaxial(**COAX)) == ((0.0442 / 2, 0.0974 / 2), (0.050 / 2, 0.110 / 2))
    assert coaxial_radii(Coaxial(**COAX, inlet="annulus")) == ((0.0974 / 2, 0.0442 / 2), (0.110 / 2, 0.050 / 2))
    assert pipe_type(Coaxial(**COAX)) == "COAXIAL_ANNULAR_OUT"
    assert pipe_type(Coaxial(**COAX, inlet="annulus")) == "COAXIAL_ANNULAR_IN"


def test_bhresist():
    assert to_bhresist(DoubleUTube(**U, inlets="diagonal"))["pipe_inlet_arrangement"] == "DIAGONAL"
    with pytest.raises(ValueError, match="parallel only"):
        to_bhresist(DoubleUTube(**U, flow="series"))
    assert [init_method(p) for p in (SingleUTube(**U), DoubleUTube(**U), Coaxial(**COAX))] == [
        "init_single_u_borehole",
        "init_double_u_borehole",
        "init_coaxial_borehole",
    ]
    assert set(to_bhresist(Coaxial(**COAX))) == {
        "outer_pipe_outer_diameter",
        "outer_pipe_dimension_ratio",
        "outer_pipe_conductivity",
        "inner_pipe_outer_diameter",
        "inner_pipe_dimension_ratio",
        "inner_pipe_conductivity",
    }


@pytest.mark.parametrize(
    "pipe",
    [SingleUTube(**U), DoubleUTube(**U), DoubleUTube(**U, flow="series"), Coaxial(**COAX)],
    ids=["single", "double_parallel", "double_series", "coaxial"],
)
def test_ghedesigner_round_trip(pipe):
    block = to_ghedesigner(pipe)
    assert pipe_from_ghedesigner(block) == pipe
    assert pipe_from_ghedesigner({**block, "arrangement": block["arrangement"].lower()}) == pipe


def test_ghedesigner_refusals():
    with pytest.raises(ValueError, match="adjacent inlets only"):
        to_ghedesigner(DoubleUTube(**U, inlets="diagonal"))
    with pytest.raises(ValueError, match="centre pipe as the inlet"):
        to_ghedesigner(Coaxial(**COAX, inlet="annulus"))
    with pytest.raises(ValueError, match="one rho_cp"):
        to_ghedesigner(Coaxial(**{**COAX, "outer_pipe_volumetric_heat_capacity_j_per_m3_k": 1.6e6}))
    with pytest.raises(ValueError, match="one U-tube"):
        pipe_from_ghedesigner({**to_ghedesigner(SingleUTube(**U)), "num_pipes": 2})
    with pytest.raises(ValueError, match="unknown GHEDesigner pipe arrangement"):
        pipe_from_ghedesigner({"arrangement": "TRIPLEUTUBE"})


def test_ghedesigner_materials_read_both_key_styles():
    old = {"conductivity": 2.6, "rho_cp": 2.5e6, "undisturbed_temp": 12.0}
    new = {
        "thermal_conductivity_w_per_m_k": 2.6,
        "volumetric_heat_capacity_j_per_m3_k": 2.5e6,
        "undisturbed_ground_temperature_c": 12.0,
    }
    assert soil_from_ghedesigner(old) == soil_from_ghedesigner(new) == Soil(2.6, 2.5e6, 12.0)
    assert to_ghedesigner(Soil(2.6, 2.5e6, 12.0)) == old
    with pytest.raises(ValueError, match="not both"):
        grout_from_ghedesigner({"conductivity": 2.4, "thermal_conductivity_w_per_m_k": 2.4, "rho_cp": 3.4e6})
    with pytest.raises(KeyError, match="rho_cp"):
        grout_from_ghedesigner({"conductivity": 2.4})


# --- extending converters ----------------------------------------------------------------


@pytest.mark.parametrize("convert", [to_pygfunction, to_bhresist, to_ghedesigner, pipe_type, init_method])
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
    assert "pipe_inlet_arrangement" in to_bhresist(DoubleUTube(**U))  # existing types unaffected


def test_subclass_gets_its_own_conversion_parent_unchanged():
    @dataclasses.dataclass(frozen=True, slots=True)
    class LabelledSingleUTube(SingleUTube):
        label: str = ""

    @to_ghedesigner.register(LabelledSingleUTube)
    def _(pipe):
        return {**to_ghedesigner.dispatch(SingleUTube)(pipe), "name": pipe.label}

    labelled = LabelledSingleUTube(**U, label="field A")
    assert to_ghedesigner(labelled)["name"] == "field A"
    assert "name" not in to_ghedesigner(SingleUTube(**U))
