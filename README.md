# BHTypes

Plain data types for what is inside a borehole heat exchanger -- `Soil`, `Grout`, a pipe
(`Tube`), its arrangements `SingleUTube`, `DoubleUTube` and `Coaxial`, and the `Borehole` --
with converters to the conventions of [pygfunction](https://github.com/MassimoCimmino/pygfunction)
and [bhresist](https://pypi.org/project/bhresist/). No dependencies; SI units throughout.

```bash
pip install bhtypes   # Python 3.11 or newer
```

Each package describes the same pipe differently (radii or diameters, a dimension ratio,
shank spacing wall to wall or from the axis, leg order). `bhtypes` stores each dimension once,
under a name that says what it is and in what unit, and derives the rest:

```python
import pygfunction as gt
from bhr.borehole import Borehole as BhresistBorehole
from scp.water import Water

from bhtypes import Borehole, DoubleUTube, Grout, Soil, Tube
from bhtypes.convert.bhresist import init_method, to_bhresist
from bhtypes.convert.pygfunction import to_pygfunction

tube = Tube(inner_diameter_m=0.03398, outer_diameter_m=0.04216,
            thermal_conductivity_w_per_m_k=0.4, volumetric_heat_capacity_j_per_m3_k=2.07e6)
pipe = DoubleUTube(tube, shank_spacing_m=0.03404, inlets="adjacent", flow="parallel")
borehole = Borehole(length_m=200.0, diameter_m=0.1524)
grout = Grout(thermal_conductivity_w_per_m_k=2.4, volumetric_heat_capacity_j_per_m3_k=3.4e6)
soil = Soil(thermal_conductivity_w_per_m_k=3.0, volumetric_heat_capacity_j_per_m3_k=2.6e6)

# pygfunction: position and buried depth belong to the field; R_fp comes from your convection model
gt.pipes.MultipleUTube(**to_pygfunction(pipe), **to_pygfunction(soil), **to_pygfunction(grout),
                       borehole=gt.boreholes.Borehole(D=4.0, x=0.0, y=0.0, **to_pygfunction(borehole)),
                       R_fp=0.1)

# bhresist: state the boundary condition (its default is uniform heat flux)
bh = BhresistBorehole()
getattr(bh, init_method(pipe))(**to_bhresist(pipe), **to_bhresist(borehole), **to_bhresist(grout),
                               **to_bhresist(soil), fluid=Water(),
                               boundary_condition="UNIFORM_BOREHOLE_WALL_TEMP")
```

A coaxial exchanger is two tubes: `Coaxial(center=Tube(...), outer=Tube(...), inlet="center")`.

## Conventions

| Field or property | Meaning |
|---|---|
| `Tube.dimension_ratio` | outer diameter / wall thickness (DR, SDR) |
| `shank_spacing_m` | gap between the outer walls of a U-tube's two legs |
| `leg_offset_m` | borehole axis to each leg's center (bhresist's `shank_space`) |
| `leg_positions()` | leg centers, inlets first (pygfunction's `pos`); GHEDesigner's arithmetic, bit for bit |
| `DoubleUTube.inlets`, `.flow` | `"adjacent"` / `"diagonal"`; `"parallel"` / `"series"` |
| `Coaxial.inlet` | `"center"` or `"annulus"`: which channel the fluid goes down |

## Converters

`bhtypes.convert.pygfunction` (`to_pygfunction`, `pipe_type`, `coaxial_radii`) and
`bhtypes.convert.bhresist` (`to_bhresist`, `init_method`) return keyword arguments; they are a
convenience over the types' derived geometry, tested against pygfunction 2.3 and bhresist 0.4.
They refuse what the target cannot represent (bhresist has no series double U-tube). Each
`to_*` is a `functools.singledispatch` function, so new types can register their own.

## Scope

Out of scope: fluids (use [SecondaryCoolantProps](https://pypi.org/project/SecondaryCoolantProps/),
which pygfunction and bhresist already take), the undisturbed ground temperature and bore fields
(positions, buried depths, tilts) -- conditions of a site, not of a borehole -- and applications'
input files.

## Status

Pre-1.0: minor versions may change the API. See the [changelog](CHANGELOG.md) for migration
notes.

## License

MIT
