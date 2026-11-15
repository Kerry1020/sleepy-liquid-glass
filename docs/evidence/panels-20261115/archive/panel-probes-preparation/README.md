# Nonperiodic panel calibration sources

Two new deterministic source images support the first static Alert/Sheet feasibility comparison. They are inputs to real native and Android glass, not renders of an expected result. All PNGs are750×1334 RGB8 with the same embedded sRGB ICC profile. The two selected sources plus six explicitly unselected gray compatibility slots occupy203,302bytes.

|Selected ID|Source design|PNG SHA256|
|---|---|---|
|`panel_probe_coordinate`|104 nonperiodic coarse cells, independent two-axis RGB ramps|`e2cc037db338c828d64de91c31035d251c226b23184abadac0fb51f688ff4b3e`|
|`panel_probe_shapes`|16 filled unique colored shapes, dimensions80–124px|`cf674c516d49a54c7f34529bf4186f9fa4943ab11dc803779097b90024113149`|

![Nonperiodic coordinate-coded source](inputs/panel_probe_coordinate.png)

![Unique filled-shape source](inputs/panel_probe_shapes.png)

`manifest.json` binds every source file, decoded RGB, profile and generator. Its SHA256 is `ea42ecc8435b265a48c5740c03bfc3dea3eb11b50426d4d81b3270d07b171282`. Only its two `selected_ids` enter capture/analysis; the six `compatibility_unselected` files are fresh uniform gray, excluded from scoring. No old noise, hidden or holdout source was read.

`oracle.json` supplies every coordinate-cell bbox/base color/two-axis slope and every shape's dimensions, vertices/bbox, exact color, visible raster centroid, area and mask hash. It uses original source pixels with pixel centers(i+.5,j+.5); logical coordinates divide these by2. Source shapes do not overlap or clip at the canvas. Output glass/foreground can still clip, blur or merge them.

The preregistered [analysis plan](analysis-plan.md) and machine-readable `analysis-plan.json` separate external scrim, body color/texture, apparent color-edge width, identifiable feature deformation and the narrow highlight. They fix straight/corner regions and failure gates before output decoding. They do not promise that small features remain identifiable through16dp blur, fit material parameters or claim parity from four light observations.

To regenerate the source assets with the persisted profile:

```sh
/usr/bin/python3 -B generate_probes.py
```

The profile file is persisted because a newly created ICC profile can carry a new metadata timestamp. Generator code and dependency versions are recorded. Generated PNGs were opened and checked for dimensions, mode,8bit RGB IHDR, embedded profile identity and exact decoded RGB equality. Both selected source images were visually inspected. No output screenshot was transformed or duplicated, and this preparation did not use a device/build tool.
