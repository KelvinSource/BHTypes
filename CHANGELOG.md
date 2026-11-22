# Changelog

## 0.3.0

- `Tube`: one pipe, with its diameters, wall conductivity and heat capacity, and roughness
  (derived radii, wall thickness and dimension ratio). The arrangements now hold tubes:
  `SingleUTube(tube, shank_spacing_m)`, `DoubleUTube(tube, shank_spacing_m, inlets, flow)` and
  `Coaxial(center, outer, inlet)`. This is a breaking change: the pipe fields move from the
  arrangements to the tube (`pipe.inner_radius_m` -> `pipe.tube.inner_radius_m`,
  `coaxial.inner_pipe_*` -> `coaxial.center.*`, `coaxial.outer_pipe_*` -> `coaxial.outer.*`), and
  each coaxial tube has its own roughness. The converters' output is unchanged.

  ```python
  # 0.2
  DoubleUTube(0.0274, 0.0334, 0.0266, 0.42, 1.5e6, inlets="diagonal")
  Coaxial(0.044, 0.050, 0.097, 0.110, 0.4, 0.4, 1.5e6, 1.5e6)
  # 0.3
  DoubleUTube(Tube(0.0274, 0.0334, 0.42, 1.5e6), 0.0266, inlets="diagonal")
  Coaxial(Tube(0.044, 0.050, 0.4, 1.5e6), Tube(0.097, 0.110, 0.4, 1.5e6))
  ```
- American spelling: the coaxial inlet option `"centre"` is now `"center"`
  (`Coaxial(..., inlet="center")`, the default), matching the `center` tube.
- `Soil` holds the soil's thermal properties only: `undisturbed_temperature_c` is removed. It is a
  site condition, not a property of the soil, and neither pygfunction nor bhresist uses it;
  tools that simulate a site keep it themselves. `Soil(k, rho_cp, T)` -> `Soil(k, rho_cp)`.
- Removed `bhtypes.convert.ghedesigner` (`to_ghedesigner`, `pipe_from_ghedesigner`,
  `soil_from_ghedesigner`, `grout_from_ghedesigner`). bhtypes converts to the computational
  packages, pygfunction and bhresist; reading and writing an application's input files belongs
  to that application.

## 0.2.0

- `Borehole` (length and diameter), with converters: `to_pygfunction` gives the `H` and `r_b`
  of pygfunction's `Borehole` and field constructors, `to_bhresist` the `length` and
  `borehole_diameter`.

## 0.1.0

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
