# Pixel Art Case

- Case name `castle-bricks`
- Subject reference `/home/jeremym/media/Storage/Dev/ImageModelShmimageModel/cases/castle-bricks/source/reference.jpg`
- Target grid up to `128` pixels on the longer side
- Palette selection `auto` with `16` requested colors when using auto

## Art Direction

- **Material reference:** `source/reference.jpg` — 8 irregular medieval ashlar stone courses with varied heights (`14–20px`) and block widths (`13–35px`), a double-stacked narrow brick pair inside a tall course, staggered wrap-crossing vertical joints, hand-hewn chipped edges, deep shadowed mortar crevices, restrained rust mineral drips, 2 subtle carved mason marks, and crevice-anchored moss.
- **Style alignment:** Matches the Studio Ghibli painterly cel style of `cases/paving-stones`, `cases/cliff-rock`, and `cases/grass`: top-left sunlight, flat-dominant stone faces (one dominant value + at most one edge-anchored chiseled step/chip, zero multi-band airbrush ramps), tight `1–2px` top-left sunlit bevels and dark bottom-right/under-course cast shadows, and a curated 20-color weathered limestone/warm ochre/cool slate/rust/Ghibli moss palette.
- **Quantitative targets (`tile-stats`):** `luma_mean` around `105–128` (reference: `101.2`), `dark_pct` ~`20–32%` (`mortar_deep` ≤ `14%`), `mid_pct` ~`50–68%`, `light_pct` ~`8–22%`, seam continuity `lr_ratio` and `tb_ratio` near `1.0` (`<= 1.45`).

## Review

Compare the silhouette and block-in with the reference at native size and integer zoom. Review recognizable landmarks and the requested style again after cleanup. For a conversion, inspect the diagnostics from `check` alongside the artwork. Verify the native PNG, scaled PNG, and timelapse after export.

## Seamless tile

- **Native dimensions:** `128 × 128` pixels.
- **Wrap axes:** Both X and Y axes (toroidal 8-course ashlar layout, `tile_tools.torus_delta` signed distances, periodic edge roughness, wrap-safe moss/fracture/rust placement, and toroidal component cleanup via `scripts/tile_tools.py`).
- **Material reference:** `source/reference.jpg`.
- **Style choices:** Chunky, hand-hewn medieval castle blocks with crisp flat-faceted light planes, deep recessed under-course mortar shadows, subtle iron streaks, 2 carved mason marks, and velvet-clustered crevice moss. Inspect centered-seam offset joins (`joins.png`), 3 × 3 repeated field (`repeat.png`), and `tile-stats` across passes.
