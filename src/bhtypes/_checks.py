"""Input checks shared by the dataclasses."""

from __future__ import annotations

from math import isfinite


def positive(name: str, value: float) -> None:
    if not (isinstance(value, int | float) and not isinstance(value, bool) and isfinite(value) and value > 0):
        raise ValueError(f"{name} must be a finite positive number, got {value!r}")


def non_negative(name: str, value: float) -> None:
    if not (isinstance(value, int | float) and not isinstance(value, bool) and isfinite(value) and value >= 0):
        raise ValueError(f"{name} must be a finite non-negative number, got {value!r}")


def wall(inner_name: str, inner: float, outer_name: str, outer: float) -> None:
    positive(inner_name, inner)
    positive(outer_name, outer)
    if not inner < outer:
        raise ValueError(f"{inner_name} ({inner}) must be smaller than {outer_name} ({outer})")


def choice(name: str, value: str, options: tuple[str, ...]) -> None:
    if value not in options:
        raise ValueError(f"{name} must be one of {options}, got {value!r}")
