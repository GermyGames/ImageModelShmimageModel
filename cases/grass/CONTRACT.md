# Pixel Art Case

- Case name `grass`
- Subject reference `/home/jeremym/media/Storage/Dev/ImageModelShmimageModel/cases/grass/source/reference.jpg`
- Target grid up to `128` pixels on the longer side
- Palette selection `auto` with `16` requested colors when using auto

## Art Direction

- **Material reference:** `source/reference.jpg` — dense, plush overlapping grass tuft carpet with organic swirling directional blade currents and deep tucked shadow pockets (synthesized directly on the wrapping grid to exclude the reference's center watermark and photographic micro-blade grain).
- **Style alignment:** Matches the Ghibli style references and delivered `cases/paving-stones` and `cases/cliff-rock` tiles: top-left sunlight, cohesive painted cel grass clusters (no stipple confetti, no blobby camo, no multi-band airbrush ramps), and a curated 16-color lush emerald/cool-teal/warm-olive/chartreuse palette.
- **Quantitative targets (`tile-stats`):** `luma_mean` around `100–125`, `dark_pct` ~`22–36%` (`shadow_deep` ≤ `10%`), `mid_pct` ~`52–68%`, `light_pct` ~`6–14%`, seam continuity `lr_ratio` and `tb_ratio` near `1.0` (`<= 1.4`).

## Review

Compare the silhouette and block-in with the reference at native size and integer zoom. Review recognizable landmarks and the requested style again after cleanup. For a conversion, inspect the diagnostics from `check` alongside the artwork. Verify the native PNG, scaled PNG, and timelapse after export.

## Seamless tile

- **Native dimensions:** `128 × 128` pixels.
- **Wrap axes:** Both X and Y axes (exact periodic FFT fields, toroidal blue-noise tuft placement, modulo-`N` blade rasterization, and toroidal component cleanup via `scripts/tile_tools.py`).
- **Material reference:** `source/reference.jpg`.
- **Style choices:** Lush painterly cel grass clusters fanned into curved 3–5 blade tufts aligned to a smooth swirling directional wind field, with broad low-frequency cool/warm meadow glazes and crisp `1px` sunlit chartreuse tips. Inspect centered-seam offset joins (`joins.png`), 3 × 3 repeated field (`repeat.png`), and `tile-stats` across passes.
