# Pixel Art Case

- Case name `cliff-rock`
- Subject reference `/home/jeremym/media/Storage/Dev/ImageModelShmimageModel/cases/cliff-rock/source/reference.jpg`
- Target grid up to `128` pixels on the longer side
- Palette selection `auto` with `22` requested colors when using auto

## Art Direction

- **Material reference:** `source/reference.jpg` — fractured granite/shale cliff wall with overlapping NW → SE (~25°–36° down-right) diagonal strata, protruding stepped shelves, deep tapering under-ledge overhangs, shorter cross-fractures, and broad angular open faces.
- **Style references:** `source/style-paving-stones.png` (matching the crisp, flat-faceted Ghibli daylight stonework from `paving-stones`), alongside `source/style-wall.jpg`, `source/style-boulders.jpg`, and `source/style-meadow.jpg`.
- **Direction & Palette:** Rugged 18-color Ghibli cliff daylight palette (`#162228` deep crevice shadow through `#d4c9af`/`#cbb68e` sunlit ridge crests, warm/cool rock glazes `#7c705d`/`#a49376`/`#576968`/`#7c8d86`, and sparse ledge moss `#1d3829`–`#85aa43`), matching the reference's grounded value weight (~95–115 mean luminance). Built via reference-sculpted toroidal low-frequency equalization + 2-pass toroidal Kuwahara planarization on `128 × 128` + crisp cluster absorption (`< 3px`), carved overhang clefts, `1px` sunlit ridge crests, and sparse crevice moss.

## Review

Compare the silhouette and block-in with the reference at native size and integer zoom. Review recognizable landmarks and the requested style again after cleanup. For a conversion, inspect the diagnostics from `check` alongside the artwork. Verify the native PNG, scaled PNG, and timelapse after export.

## Seamless tile

- **Native dimensions:** `128 × 128` pixels (exact 1:4 toroidal downsample of the `512 × 512` seamless cliff reference).
- **Wrap axes:** Both X and Y axes (periodic FFT convolution, wrap-padded Kuwahara filtering, and toroidal component cleanup).
- **Material reference:** `source/reference.jpg`.
- **Style choices:** Reference-sculpted rugged craggy cliff ledges with bold flat-faceted planes (zero photo stipple and zero gradient blur). Inspect centered-seam offset joins (`joins.png`) and 3×3 repeated field (`repeat.png`) across passes.
