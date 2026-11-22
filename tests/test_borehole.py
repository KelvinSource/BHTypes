"""Borehole: validation and conversions, without the target packages installed."""

import dataclasses

import pytest

from bhtypes import Borehole
from bhtypes.convert.bhresist import to_bhresist
from bhtypes.convert.pygfunction import to_pygfunction

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
