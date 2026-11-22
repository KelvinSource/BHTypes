# BHTypes

**Plain data types for borehole heat exchangers**: `Soil`, `Grout`, a pipe (`Tube`) and its
arrangements `SingleUTube`, `DoubleUTube` and `Coaxial`, and the `Borehole`, plus converters to the conventions
of the computational packages [pygfunction](https://github.com/MassimoCimmino/pygfunction) and
[bhresist](https://pypi.org/project/bhresist/). No dependencies.

Each of those packages describes the same pipe differently -- radii or diameters, a wall
dimension ratio, shank spacing measured edge to edge or from the borehole axis, leg order,
coaxial radii grouped by pipe or by surface. `bhtypes` stores each dimension once, under a
name that says what it is and in what unit, and derives the rest:

```python
from bhtypes import Coaxial, DoubleUTube, Grout, Soil, Tube
from bhtypes.convert.bhresist import init_method, to_bhresist
from bhtypes.convert.pygfunction import to_pygfunction

tube = Tube(                               # one pipe: its wall and material
    inner_diameter_m=0.03398,
    outer_diameter_m=0.04216,
    thermal_conductivity_w_per_m_k=0.4,
    volumetric_heat_capacity_j_per_m3_k=2.07e6,
)
pipe = DoubleUTube(
    tube,
    shank_spacing_m=0.03404,               # gap between the outer walls of a U-tube's legs
    inlets="adjacent",                     # or "diagonal"
    flow="parallel",                       # or "series"
)
coaxial = Coaxial(center=Tube(0.044, 0.050, 0.4, 1.5e6), outer=Tube(0.097, 0.110, 0.4, 1.5e6))
grout = Grout(thermal_conductivity_w_per_m_k=2.4, volumetric_heat_capacity_j_per_m3_k=3.4e6)
soil = Soil(thermal_conductivity_w_per_m_k=3.0, volumetric_heat_capacity_j_per_m3_k=2.6e6)

# pygfunction
gt.pipes.MultipleUTube(**to_pygfunction(pipe), **to_pygfunction(soil), **to_pygfunction(grout),
                       borehole=borehole, R_fp=R_fp)

# bhresist
bh = bhr.borehole.Borehole()
getattr(bh, init_method(pipe))(**to_bhresist(pipe), **to_bhresist(grout), **to_bhresist(soil),
                               borehole_diameter=0.1524, length=200.0, fluid=fluid)
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

## Layout

The types (`bhtypes.materials`, `bhtypes.pipes`, `bhtypes.borehole`) are plain data:
fields, validation and derived geometry, with no knowledge of any other package. Each conversion lives in
`bhtypes.convert.<package>`:

| Module | Functions |
|---|---|
| `bhtypes.convert.pygfunction` | `to_pygfunction`, `pipe_type` (`pipe_type_str`), `coaxial_radii` |
| `bhtypes.convert.bhresist` | `to_bhresist`, `init_method` |

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
  own its conversion.
  Do not re-register an existing bhtypes type: the registry is shared by every package in the
  process, so that would change the conversion for all of them.

## Installation

```bash
pip install bhtypes
```

## Scope

- **In:** soil and grout thermal properties (not the undisturbed ground temperature, a site
  condition); a pipe and its arrangements: single U-tube,
  double U-tube (explicit inlet arrangement and parallel/series flow) and coaxial; the borehole's length and
  diameter; converters.
- **Out:** fluids -- use [SecondaryCoolantProps](https://pypi.org/project/SecondaryCoolantProps/)
  (`scp`), which pygfunction and bhresist already share; bore fields (positions, buried
  depths, tilts, orientations); reading and writing applications' input files (e.g.
  GHEDesigner's), which belongs to those applications.

## Conventions

| Quantity | Field | Derived |
|---|---|---|
| Pipe (`Tube`) | `inner_diameter_m`, `outer_diameter_m`, wall conductivity and heat capacity, roughness | radii, `wall_thickness_m`, `dimension_ratio` (outer diameter / wall) |
| Leg spacing | `shank_spacing_m`: gap between the legs' outer walls | `leg_offset_m`: borehole axis to leg center |
| Leg positions | -- | `leg_positions()`: inlets first, then outlets (pygfunction's order) |
| Double U inlets | `inlets`: `"adjacent"` or `"diagonal"` | bhresist's `pipe_inlet_arrangement` |
| Coaxial flow | `inlet`: `"center"` or `"annulus"` | pygfunction's radius order and `pipe_type_str` |
| Coaxial pipes | `center` and `outer` tubes | `annulus_radii_m`; each tube's radii and dimension ratio |

Leg positions are computed with GHEDesigner's own arithmetic (`Pipe.place_pipes`), so they
match what GHEDesigner passes to pygfunction and bhresist bit for bit.

Converters refuse what the target package cannot represent rather than approximating it:
bhresist has no series double U-tube model.
