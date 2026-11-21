# Changelog

## 0.1.0 (unreleased)

First release.

- `Soil`, `Grout`, `SingleUTube`, `DoubleUTube` (adjacent or diagonal inlets, parallel or
  series flow) and `Coaxial` (centre or annulus inlet) as frozen, validated dataclasses with
  units in their field names.
- Converters in `bhtypes.convert`: `pygfunction` (`to_pygfunction`, `pipe_type`,
  `coaxial_radii`), `bhresist` (`to_bhresist`, `init_method`) and `ghedesigner`
  (`to_ghedesigner`, `pipe_from_ghedesigner`, `soil_from_ghedesigner`,
  `grout_from_ghedesigner`). Each is a `functools.singledispatch` function that other
  packages can extend.
- No runtime dependencies; Python 3.11 or newer.
