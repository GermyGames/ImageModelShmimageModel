# Pixel Art Case

- Case name `paving-stones`
- Subject reference `/home/jeremym/media/Storage/Dev/ImageModelShmimageModel/cases/paving-stones/source/reference.jpg`
- Target grid up to `128` pixels on the longer side
- Palette selection `auto` with `22` requested colors when using auto

## Art Direction

- **Subject / Material reference:** `source/reference.jpg` — exact 8×8 unit herringbone paving grid (32 rectangular pavers, each 2×1 units = `32 × 16` or `16 × 32` px on the 128×128 grid).
- **Style references:**
  - `source/style-wall.jpg` — warm sunlit cream-ochre stone face highlights, cool blue-teal shaded retaining-wall stones, lush sunlit moss pockets.
  - `source/style-boulders.jpg` — painterly Studio Ghibli stone planes, limestone/ivory highlights, cool slate-blue shadows, sparse crisp hairline fractures and moss patches.
  - `source/style-meadow.jpg` — vibrant sunlit meadow greens and luminous daylight atmosphere.
- **Direction & Palette:** Curated 22-color Ghibli daylight palette. Consistent upper-left golden-cream sunlight, cool blue-teal/slate shadows, clean broad painterly gouache-like planes (no photographic noise or stipple), subtle per-stone hue variation (warm limestone, sunlit buff-ochre, cool weathered sage-mineral) broken across the 4×4 sub-period, selective hairline fractures and chipped bevels, and sunlit chartreuse-to-deep-pine moss tucked into select joints and corner pockets.

## Review

Compare the silhouette and block-in with the reference at native size and integer zoom. Review recognizable landmarks and the requested style again after cleanup. For a conversion, inspect the diagnostics from `check` alongside the artwork. Verify the native PNG, scaled PNG, and timelapse after export.

## Seamless tile

- **Native dimensions:** `128 × 128` pixels.
- **Wrap axes:** Both X and Y axes (toroidal wrapping modulo 128).
- **Material reference:** `source/reference.jpg`.
- **Style choices:** Painterly sunlit limestone, ochre, and sage pavers with dark pine-slate mortar joints and organically placed moss cushions. Inspect centered-seam offset joins (`joins.png`) and 3×3 repeated field (`repeat.png`) at every visual pass.
