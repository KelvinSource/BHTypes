"""Converters checked against the real packages.

pygfunction and bhresist are dev dependencies. The GHEDesigner tests skip unless it is
installed; they show bhtypes reproduces what GHEDesigner itself passes to pygfunction
and bhresist, bit for bit.
"""

import dataclasses

import pytest

from bhtypes import Coaxial, DoubleUTube, Grout, Soil
from bhtypes.convert.bhresist import init_method, to_bhresist
from bhtypes.convert.ghedesigner import pipe_from_ghedesigner, to_ghedesigner
from bhtypes.convert.pygfunction import coaxial_radii, to_pygfunction

gt = pytest.importorskip("pygfunction")
bhr_borehole = pytest.importorskip("bhr.borehole")

SOIL, GROUT = Soil(3.0, 2.6e6, 12.0), Grout(2.4, 3.4e6)
U_BLOCK = {
    "inner_diameter": 0.03398,
    "outer_diameter": 0.04216,
    "shank_spacing": 0.03404,
    "roughness": 1e-6,
    "conductivity": 0.4,
    "rho_cp": 2.07e6,
}
COAX_BLOCK = {
    "arrangement": "COAXIAL",
    "inner_pipe_d_in": 0.0442,
    "inner_pipe_d_out": 0.050,
    "outer_pipe_d_in": 0.0974,
    "outer_pipe_d_out": 0.110,
    "roughness": 1e-6,
    "conductivity_inner": 0.4,
    "conductivity_outer": 0.4,
    "rho_cp": 1.5e6,
}
BLOCKS = {
    "single": {"arrangement": "SINGLEUTUBE", **U_BLOCK},
    "double_parallel": {"arrangement": "DOUBLEUTUBEPARALLEL", **U_BLOCK},
    "coaxial": COAX_BLOCK,
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


@pytest.mark.parametrize("name", list(BLOCKS))
def test_pygfunction_pipe_models_build(name):
    pipe = pipe_from_ghedesigner(BLOCKS[name])
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
    adjacent = pipe_from_ghedesigner(BLOCKS["double_parallel"])
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


@pytest.mark.parametrize("name", list(BLOCKS))
def test_bhresist_borehole_builds(name):
    assert 0 < _bhresist(pipe_from_ghedesigner(BLOCKS[name])).calc_bh_resist(0.4, 12.0) < 1


# --- against GHEDesigner ------------------------------------------------------------------


@pytest.fixture
def ghedesigner():
    return pytest.importorskip("ghedesigner")


def _ghedesigner_pipe(block):
    from ghedesigner.ghe.pipe import Pipe

    props = {k: v for k, v in block.items() if k != "arrangement"}
    if block["arrangement"] == "SINGLEUTUBE":
        return Pipe.init_single_u_tube(
            props["conductivity"],
            props["rho_cp"],
            props["inner_diameter"],
            props["outer_diameter"],
            props["shank_spacing"],
            props["roughness"],
        )
    if block["arrangement"] == "DOUBLEUTUBEPARALLEL":
        return Pipe.init_double_u_tube_parallel(
            props["conductivity"],
            props["rho_cp"],
            props["inner_diameter"],
            props["outer_diameter"],
            props["shank_spacing"],
            props["roughness"],
        )
    return Pipe.init_coaxial(
        (props["conductivity_inner"], props["conductivity_outer"]),
        props["rho_cp"],
        props["inner_pipe_d_in"],
        props["inner_pipe_d_out"],
        props["outer_pipe_d_in"],
        props["outer_pipe_d_out"],
        props["roughness"],
    )


@pytest.mark.parametrize("name", ["single", "double_parallel"])
def test_leg_positions_match_ghedesigner(ghedesigner, name):
    assert pipe_from_ghedesigner(BLOCKS[name]).leg_positions() == _ghedesigner_pipe(BLOCKS[name]).pos


def test_coaxial_radii_match_ghedesigner_pygfunction_mapping(ghedesigner):
    """GHEDesigner's calculate_g_function: r_in = [inner.r_in, outer.r_in], r_out = [inner.r_out, outer.r_out]."""
    gd = _ghedesigner_pipe(COAX_BLOCK)
    r_in, r_out = coaxial_radii(pipe_from_ghedesigner(COAX_BLOCK))
    assert list(r_in) == [gd.r_in[0], gd.r_out[0]]
    assert list(r_out) == [gd.r_in[1], gd.r_out[1]]


@pytest.mark.parametrize("name", list(BLOCKS))
def test_bhresist_resistance_matches_ghedesigner(ghedesigner, name):
    from ghedesigner.enums import DoubleUTubeConnType
    from ghedesigner.ghe.boreholes.coaxial_borehole import CoaxialPipe
    from ghedesigner.ghe.boreholes.multi_u_borehole import MultipleUTube
    from ghedesigner.ghe.boreholes.single_u_borehole import SingleUTube as GDSingle
    from ghedesigner.media import Fluid
    from ghedesigner.media import Grout as GDGrout
    from ghedesigner.media import Soil as GDSoil

    block = BLOCKS[name]
    args = (
        0.4,
        Fluid("PropyleneGlycol", 12.0, 25.0),
        gt.boreholes.Borehole(LENGTH, 4.0, BOREHOLE_DIAMETER / 2, 0.0, 0.0),
        _ghedesigner_pipe(block),
        GDGrout(2.4, 3.4e6),
        GDSoil(3.0, 2.6e6, 12.0),
    )
    if name == "single":
        gd = GDSingle(*args)
    elif name == "double_parallel":
        gd = MultipleUTube(*args, config=DoubleUTubeConnType.PARALLEL)
    else:
        gd = CoaxialPipe(*args)
    ours = _bhresist(pipe_from_ghedesigner(block))
    for m_flow in (0.05, 0.4, 0.8):
        for temperature in (2.0, 12.0, 25.0):
            gd.m_flow_borehole = m_flow
            gd.fluid.update_props_with_new_temp(temperature)
            assert ours.calc_bh_resist(m_flow, temperature) == gd.calc_effective_borehole_resistance()


def test_single_u_round_trip_through_ghedesigner_pipe(ghedesigner):
    pipe = pipe_from_ghedesigner(BLOCKS["single"])
    gd = _ghedesigner_pipe(to_ghedesigner(pipe))
    assert (gd.r_in, gd.r_out, gd.s, gd.roughness) == (
        pipe.inner_radius_m,
        pipe.outer_radius_m,
        pipe.shank_spacing_m,
        pipe.roughness_m,
    )
