# BHTypes

**Plain data types for borehole heat exchangers**: `Soil`, `Grout`, the pipe geometries
`SingleUTube`, `DoubleUTube` and `Coaxial`, and the `Borehole`, plus converters to the conventions
of [pygfunction](https://github.com/MassimoCimmino/pygfunction),
[bhresist](https://pypi.org/project/bhresist/) and
[GHEDesigner](https://github.com/BETSRG/GHEDesigner). No dependencies.

Each of those packages describes the same pipe differently -- radii or diameters, a wall
dimension ratio, shank spacing measured edge to edge or from the borehole axis, leg order,
coaxial radii grouped by pipe or by surface. `bhtypes` stores each dimension once, under a
name that says what it is and in what unit, and derives the rest:

```python
from bhtypes import DoubleUTube, Grout, Soil
from bhtypes.convert.bhresist import init_method, to_bhresist
from bhtypes.convert.ghedesigner import pipe_from_ghedesigner, to_ghedesigner
from bhtypes.convert.pygfunction import to_pygfunction

pipe = DoubleUTube(
    inner_diameter_m=0.03398,
    outer_diameter_m=0.04216,
    shank_spacing_m=0.03404,               # gap between the outer walls of a U-tube's legs
    thermal_conductivity_w_per_m_k=0.4,
    volumetric_heat_capacity_j_per_m3_k=2.07e6,
    inlets="adjacent",                     # or "diagonal"
    flow="parallel",                       # or "series"
)
grout = Grout(thermal_conductivity_w_per_m_k=2.4, volumetric_heat_capacity_j_per_m3_k=3.4e6)
soil = Soil(thermal_conductivity_w_per_m_k=3.0, volumetric_heat_capacity_j_per_m3_k=2.6e6,
            undisturbed_temperature_c=12.0)

# pygfunction
gt.pipes.MultipleUTube(**to_pygfunction(pipe), **to_pygfunction(soil), **to_pygfunction(grout),
                       borehole=borehole, R_fp=R_fp)

# bhresist
bh = bhr.borehole.Borehole()
getattr(bh, init_method(pipe))(**to_bhresist(pipe), **to_bhresist(grout), **to_bhresist(soil),
                               borehole_diameter=0.1524, length=200.0, fluid=fluid)

# GHEDesigner input files
pipe = pipe_from_ghedesigner(config["pipe"])
config["pipe"] = to_ghedesigner(pipe)
```

## Boreholes

A `Borehole` is the hole itself: its length and diameter, the same wherever it is drilled.
Where it is placed -- position, buried depth, tilt, orientation -- belongs to the bore field
and is given to the package that models the field:

```python
from bhtypes import Borehole

borehole = Borehole(length_m=210.0, diameter_m=0.1524)

gt.boreholes.Borehole(D=4.0, x=0.0, y=0.0, **to_pygfunction(borehole))              # H, r_b
gt.borefield.Borefield.rectangle_field(4, 3, 6.0, 6.0, D=4.0, **to_pygfunction(borehole))
getattr(bh, init_method(pipe))(..., **to_bhresist(borehole))   # length, borehole_diameter
```

GHEDesigner keeps the borehole diameter with the buried depth (its `borehole` block) and the
length with the field (`pre_designed`), so a `Borehole` has no GHEDesigner conversion.

## Layout

The types (`bhtypes.materials`, `bhtypes.pipes`, `bhtypes.borehole`) are plain data:
fields, validation and derived geometry, with no knowledge of any other package. Each conversion lives in
`bhtypes.convert.<package>`:

| Module | Functions |
|---|---|
| `bhtypes.convert.pygfunction` | `to_pygfunction`, `pipe_type` (`pipe_type_str`), `coaxial_radii` |
| `bhtypes.convert.bhresist` | `to_bhresist`, `init_method` |
| `bhtypes.convert.ghedesigner` | `to_ghedesigner`, `pipe_from_ghedesigner`, `soil_from_ghedesigner`, `grout_from_ghedesigner` |

Import the functions, not the modules, so `bhtypes.convert.pygfunction` does not shadow
`pygfunction` itself.

## Extending conversions

Every `to_*` converter is a `functools.singledispatch` function:

- **New types** -- register a conversion without changing bhtypes:
  ```python
  @to_bhresist.register(MyTripleUTube)
  def _(pipe): ...
  ```
- **Subclasses** -- dispatch picks the most specific type, so a subclass of a bhtypes class can
  have its own conversion while the parent's is unchanged.
- **Converting differently** -- write your own function. A package that adopts bhtypes would
  own its conversion (e.g. GHEDesigner's own `from_bhtypes`), and the bridge here would retire.
  Do not re-register an existing bhtypes type: the registry is shared by every package in the
  process, so that would change the conversion for all of them.

## Installation

```bash
pip install bhtypes
```

## Scope

- **In:** soil and grout thermal properties; single U-tube, double U-tube (explicit inlet
  arrangement and parallel/series flow) and coaxial pipe geometry; the borehole's length and
  diameter; converters.
- **Out:** fluids -- use [SecondaryCoolantProps](https://pypi.org/project/SecondaryCoolantProps/)
  (`scp`), which pygfunction, bhresist and GHEDesigner already share; bore fields
  (positions, buried depths, tilts, orientations).

## Conventions

| Quantity | Field | Derived |
|---|---|---|
| Pipe size | `inner_diameter_m`, `outer_diameter_m` | radii, `dimension_ratio` (outer diameter / wall) |
| Leg spacing | `shank_spacing_m`: gap between the legs' outer walls | `leg_offset_m`: borehole axis to leg centre |
| Leg positions | -- | `leg_positions()`: inlets first, then outlets (pygfunction's order) |
| Double U inlets | `inlets`: `"adjacent"` or `"diagonal"` | bhresist's `pipe_inlet_arrangement` |
| Coaxial flow | `inlet`: `"centre"` or `"annulus"` | pygfunction's radius order and `pipe_type_str` |
| Coaxial pipes | four diameters, per-pipe conductivity and heat capacity | `inner_pipe_radii_m`, `outer_pipe_radii_m`, dimension ratios |

Leg positions are computed with GHEDesigner's own arithmetic, so converted values match
what GHEDesigner passes to pygfunction and bhresist bit for bit.

Converters refuse what the target package cannot represent rather than approximating it:
bhresist has no series double U-tube model, and GHEDesigner input files have no diagonal
double U-tube, no annulus-inlet coaxial and no per-pipe coaxial heat capacity.
