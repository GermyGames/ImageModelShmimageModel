# Seamless Tiles and Styling

Use this workflow for repeating pixel-art surfaces, including original tiles from a written brief and restyles of existing tiles. Treat seamless joins and an unobtrusive repeat as separate goals. A tile can join perfectly and still produce a visible checkerboard in a filled area.

## Establish the material and style

- Record the intended native dimensions and wrap axes. Use both axes for an endlessly filled surface unless the brief calls for a strip or border. Choose the pixel scale for the game or artwork before choosing the tile size. For a natural surface, a larger tile can fit more distinct structures at the same pixel scale.
- Read the **material reference** for structure and lighting cues. For a cliff, look for the overall fracture direction, where planes split and overlap, and where crevices taper out. An original tile can start from these observations or from a written description.
- Read the **style reference** for cluster size, palette and value spacing, outline coverage, and the placement of highlights and texture. For a scene with many materials, study a crop of the relevant material. Use `shmimage.py style` on that crop if sampled colors are useful. Its JSON is a starting point for a hand-drawn palette. The command does not infer the shape of rock faces or where to place their shadows. Explicit color and detail requests take precedence over sampled values.
- **Match value weight to the surface and material reference.** Inspect the material reference's luminance distribution with `shmimage.py tile-stats` before choosing palette roles instead of reusing a high-key palette from another material or lit ground plane. Horizontal sunlit paving can stay high-key, while rugged vertical cliff rock usually needs mid-dark faces and cool shadows carrying ~65–75% of pixels, reserving bright warm highlights for protruding brows. Apply warm/cool temperature shifts as broad low-frequency glazes over one unified material rather than contrasting per-cell mosaic colors.
- Keep a restyle on the existing grid when dimensions or edge compatibility matter. If the requested change is the arrangement of forms or the repeat, redraw the block-in before revising the shading.

## Draw on the wrapping grid

Work at native resolution. For programmatic drawing, duplicate shapes that cross an edge with offsets of one canvas width or height, including the diagonal copy for a corner. In a pixel editor, use wrap mode or offset the image to work on the original joins. Apply the same wrapping to masks and secondary details. Opposite edge pixels need to read as **neighbors**, so check that a crossing feature keeps its direction, width and shading. Copying the first row onto the last can introduce a visible doubled row.

Save the usual passes under `build/steps/` on the same grid:

| Pass | What to establish |
| --- | --- |
| `01_silhouette.png` | The main masses and directional breaks. In a full-bleed texture this is a structure pass. |
| `02_blockin.png` | Flat planes and larger value groups. Review this as a repeat before shading. |
| `03_shading.png` | Coherent light and shadow clusters. Add accents where the form turns or splits. |
| `04_cleanup.png` | Remove distracting islands and tidy contours and wrap joins. |

For irregular materials such as rock, vary the width, length, spacing and endpoints of features while keeping the dominant material direction. For example, use a few long angled fractures, some shorter forks, and stretches of open rock. Avoid outlining every facet equally. Rows of similarly sized shapes, uniform grids of highlights, and evenly spaced fissures remain visible even with randomized local contours. In a quiet pixel-art style, build shading from contiguous color clusters and reserve tiny marks for meaningful chips or glints. Skip generic stipple and square-block noise unless the style calls for that texture. Keep deliberate patterns for materials that have them, such as woven cloth or laid brick.

- **Avoid multi-band gradients on flat faces.** In painterly or cel pixel art, stepping 4–5 diagonal or concentric value bands across flat faces makes paving stones or stepped ledges look pillowy and airbrushed. Hold each lit flat face to one dominant flat value plus at most one crisp, edge-anchored single-step wash or chip (never centered floating ovals or soft ramps), placing light/shadow turns in tight `1px`–`2px` bevels.
- **Break sub-period repeats and anchor details.** When a tile holds multiple repeats of a smaller structural bond (such as an `8 × 8` herringbone grid holding `2 × 2` repeats of a `4 × 4` unit), break sub-period symmetries and avoid matching neighbor temperaments across the torus so diagonal stripes do not emerge in a 3 × 3 repeat. Anchor fractures and overhang shadows to real edges, snap moss or secondary growth onto solid crevice runs, and prune `< 4px` isolated mask fragments (`prune_sparse_mask` in `scripts/tile_tools.py`) to prevent floating marks or stray dark specks.

## Restyle a complex seamless reference

Draw geometry from scratch for original tiles and structured patterns such as brick or plank bonds. For complex seamless organic references (craggy cliffs, bark, soil, foliage) where synthetic polygons or Voronoi cells read as geometric blocks while `shmimage.py fit` retains photo stipple, sculpt the reference's real relief on the torus using `scripts/tile_tools.py`:

1. **Verify seams and downsample.** Check edge continuity with `shmimage.py tile-stats` (or `seam_continuity`) and box-downsample (`Image.Resampling.BOX` or integer block-averaging) onto the wrapping native grid.
2. **Equalize broad drift.** Run gentle periodic FFT low-frequency equalization (`equalize_toroidal_luma`) to suppress tile-wide bright or dark hotspots in the 3 × 3 repeat while keeping local ledges intact.
3. **Planarize facets on the torus.** Apply toroidal Kuwahara planarization (`toroidal_kuwahara`) and small-component absorption (`absorb_small_components`, removing `< 3–4px` islands while protecting key highlights and deep crevices) to turn photographic grain into crisp painted planes without gradient blur.
4. **Calibrate crevices, ridges, and glazes.** Derive deep crevices and `1px` ridge highlights from multi-scale local valleys/ridges (`periodic_gaussian` difference) using percentile thresholds rather than arbitrary raw constants, then map rock tiers and broad low-frequency warm/cool chroma glazes into the style palette.

## Inspect the joins and the repeat

1. **Joins.** Offset the tile by half its width and height so the original wrap lines meet in the center. Inspect at integer zoom. Follow features across both joins and through their intersection. Check for abrupt value steps, gaps, doubled edges, and chopped marks.
2. **Repeat.** View a plain 3 × 3 field without borders or guides at the intended viewing scale. Look for bright or dark features that recur in lockstep, broad stripes, rows of similar facets, and any tile-wide value shift that makes each square stand out. If they show up in the block-in, alter the layout or value masses. Added detail rarely hides those patterns.
3. **Scale.** If the tile reads well up close but its repetition dominates at game scale, reduce the contrast of recurring landmarks, spread them out, or use a larger tile at the same pixel scale. When the brief calls for less repetition across a large world, compatible variants can help; keep edge and corner transitions compatible and review mixed neighbors. A single repeated bitmap always has a fixed period.
4. **Value and coverage.** Run `shmimage.py tile-stats --input <pass.png> --reference <material>` on `02_blockin.png` and `03_shading.png` to check mean luminance against the material reference, dark/mid/light balance, per-color pixel share (catching runaway deep crevices above ~10–15% or chalky over-lit faces early), and seam continuity ratios (`lr_ratio` and `tb_ratio` near `1.0`).

For a strip, repeat only the wrapping axis using `--columns` and `--rows`, and inspect only the intended join on the offset view. `tile-preview` assembles the artwork as is and does not repair seams. Source-alignment metrics from `check` cannot judge the joins or how obvious the repeat is.

## Set up and export

```bash
python3 scripts/shmimage.py init cases/cliff --tile --size 256
# Add --input /path/to/material.png if the case has a material reference.
# Draw the passes on the native grid, then capture the reviewed draft.
python3 scripts/shmimage.py record-revision cases/cliff --label "First reviewed draft"
python3 scripts/shmimage.py tile-stats --input cases/cliff/build/steps/02_blockin.png --reference /path/to/material.png
python3 scripts/shmimage.py tile-preview --input cases/cliff/build/steps/04_cleanup.png --output cases/cliff/build/check/joins.png --columns 1 --rows 1 --center-seams --scale 3
python3 scripts/shmimage.py tile-preview --input cases/cliff/build/steps/04_cleanup.png --output cases/cliff/build/check/repeat.png
# Save later visual revisions and rerun both previews after the final edit.
python3 scripts/shmimage.py deliver cases/cliff --manual --scale 4
python3 scripts/shmimage.py tile-preview --input cases/cliff/deliver/cliff_1x.png --output cases/cliff/deliver/cliff_repeat.png
```

`--size` records a target. The PNG passes determine the exported dimensions and may be rectangular. `deliver --manual` makes the native tile, integer-scaled preview, palette, timelapse and an Aseprite file when available. The repeat PNG is a review image; use the native tile as the asset. For follow-up feedback, reuse the case and its saved history. See [Export options and revision history](aseprite-and-delivery.md).
