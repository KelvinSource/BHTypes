"""Converters checked against the real packages, pygfunction and bhresist (dev dependencies)."""

import dataclasses

import pytest

from bhtypes import Coaxial, DoubleUTube, Grout, SingleUTube, Soil, Tube
from bhtypes.convert.bhresist import init_method, to_bhresist
from bhtypes.convert.pygfunction import to_pygfunction

gt = pytest.importorskip("pygfunction")
bhr_borehole = pytest.importorskip("bhr.borehole")

SOIL, GROUT = Soil(3.0, 2.6e6), Grout(2.4, 3.4e6)
TUBE = Tube(0.03398, 0.04216, 0.4, 2.07e6)
PIPES = {
    "single": SingleUTube(TUBE, 0.03404),
    "double_parallel": DoubleUTube(TUBE, 0.03404),
    "coaxial": Coaxial(Tube(0.0442, 0.050, 0.4, 1.5e6), Tube(0.0974, 0.110, 0.4, 1.5e6)),
}
BOREHOLE_DIAMETER, LENGTH = 0.1524, 200.0


def _bhresist(pipe):
    from scp.propylene_glycol import PropyleneGlycol

    bh = bhr_borehole.Borehole()
    getattr(bh, init_method(pipe))(
        **to_bhresist(pipe),
        **to_bhresist(GROUT),
        **to_bhresist(SOIL),
        borehole_diameter=BOREHOLE_DIAMETER,
        length=LENGTH,
        boundary_condition="UNIFORM_BOREHOLE_WALL_TEMP",
        fluid=PropyleneGlycol(0.25),
    )
    return bh


@pytest.mark.parametrize("name", list(PIPES))
def test_pygfunction_pipe_models_build(name):
    pipe = PIPES[name]
    borehole = gt.boreholes.Borehole(LENGTH, 4.0, BOREHOLE_DIAMETER / 2, 0.0, 0.0)
    common = {"borehole": borehole, **to_pygfunction(SOIL), **to_pygfunction(GROUT)}
    if isinstance(pipe, Coaxial):
        model = gt.pipes.Coaxial(**to_pygfunction(pipe), **common, R_ff=0.1, R_fp=0.1)
    elif isinstance(pipe, DoubleUTube):
        model = gt.pipes.MultipleUTube(**to_pygfunction(pipe), **common, R_fp=0.1)
    else:
        model = gt.pipes.SingleUTube(**to_pygfunction(pipe), **common, R_fp=0.1)
    assert model.local_borehole_thermal_resistance() > 0


def test_double_u_inlet_arrangement_reaches_both_packages():
    """Adjacent vs diagonal inlets change R_b* in pygfunction and in bhresist, the same way."""
    borehole = gt.boreholes.Borehole(LENGTH, 4.0, BOREHOLE_DIAMETER / 2, 0.0, 0.0)
    common = {"borehole": borehole, **to_pygfunction(SOIL), **to_pygfunction(GROUT), "R_fp": 0.08}
    adjacent = PIPES["double_parallel"]
    diagonal = dataclasses.replace(adjacent, inlets="diagonal")
    pyg = {
        p.inlets: gt.pipes.MultipleUTube(**to_pygfunction(p), **common).effective_borehole_thermal_resistance(
            0.4, 3900.0
        )
        for p in (adjacent, diagonal)
    }
    bhr = {p.inlets: _bhresist(p).calc_bh_resist(0.4, 12.0) for p in (adjacent, diagonal)}
    assert pyg["adjacent"] != pyg["diagonal"]
    assert bhr["adjacent"] != bhr["diagonal"]
    # diagonal inlets sit between two outlets: more thermal short-circuiting, higher R_b* in both
    assert pyg["diagonal"] > pyg["adjacent"]
    assert bhr["diagonal"] > bhr["adjacent"]


@pytest.mark.parametrize("name", list(PIPES))
def test_bhresist_borehole_builds(name):
    assert 0 < _bhresist(PIPES[name]).calc_bh_resist(0.4, 12.0) < 1


# --- borehole -----------------------------------------------------------------------------


def test_pygfunction_takes_the_borehole():
    from bhtypes import Borehole

    borehole = Borehole(length_m=150.0, diameter_m=0.15)
    single = gt.boreholes.Borehole(D=4.0, x=0.0, y=0.0, **to_pygfunction(borehole))
    assert (single.H, single.r_b) == (150.0, 0.075)
    rectangle = gt.borefield.Borefield.rectangle_field(2, 2, 6.0, 6.0, D=4.0, **to_pygfunction(borehole))
    assert len(rectangle) == 4
    assert rectangle.H[0] == 150.0
    assert rectangle.r_b[0] == 0.075


def test_bhresist_takes_the_borehole():
    from scp.propylene_glycol import PropyleneGlycol

    from bhtypes import Borehole

    pipe = PIPES["single"]
    bh = bhr_borehole.Borehole()
    getattr(bh, init_method(pipe))(
        **to_bhresist(pipe),
        **to_bhresist(GROUT),
        **to_bhresist(SOIL),
        **to_bhresist(Borehole(length_m=LENGTH, diameter_m=BOREHOLE_DIAMETER)),
        boundary_condition="UNIFORM_BOREHOLE_WALL_TEMP",
        fluid=PropyleneGlycol(0.25),
    )
    assert bh.calc_bh_resist(0.4, 12.0) == _bhresist(pipe).calc_bh_resist(0.4, 12.0)


# --- heat exchanger -----------------------------------------------------------------------


@pytest.mark.parametrize("name", list(PIPES))
def test_heat_exchanger_initialises_bhresist_in_one_call(name):
    from scp.propylene_glycol import PropyleneGlycol

    from bhtypes import Borehole, BoreholeHeatExchanger

    bhe = BoreholeHeatExchanger(Borehole(LENGTH, BOREHOLE_DIAMETER), PIPES[name], GROUT, SOIL)
    bh = bhr_borehole.Borehole()
    getattr(bh, init_method(bhe))(
        **to_bhresist(bhe), fluid=PropyleneGlycol(0.25), boundary_condition="UNIFORM_BOREHOLE_WALL_TEMP"
    )
    assert bh.calc_bh_resist(0.4, 12.0) == _bhresist(PIPES[name]).calc_bh_resist(0.4, 12.0)


def test_heat_exchanger_builds_pygfunction_pipes():
    from bhtypes import Borehole, BoreholeHeatExchanger

    borehole = Borehole(LENGTH, BOREHOLE_DIAMETER)
    bhe = BoreholeHeatExchanger(borehole, PIPES["double_parallel"], GROUT, SOIL)
    pyg_borehole = gt.boreholes.Borehole(D=4.0, x=0.0, y=0.0, **to_pygfunction(borehole))
    model = gt.pipes.MultipleUTube(**to_pygfunction(bhe), borehole=pyg_borehole, R_fp=0.1)
    assert model.local_borehole_thermal_resistance() > 0
