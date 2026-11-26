# Prep, Masks, and Grid Phase Alignment

`shmimage.py prep` prepares the reference and chooses how its edges fall on the target pixel grid.

## Background modes

- `auto` uses an input alpha channel if any pixel has alpha below 250. For an opaque input it uses a CIELAB, corner-seeded flood fill with `--bg-tolerance` (default 18).
- `none` makes the full frame opaque. Use this mode for a scene or to retain the backdrop.

When the alpha mask has foreground at or above 128, `prep` crops to that foreground with a margin of 2% of the longer source dimension, at least two pixels and clipped to the image bounds.

## Grid phase

The longest target dimension comes from `init --size`. The other is rounded to preserve the prepared image’s aspect ratio. The search tries 16 combinations of horizontal and vertical offsets, with each axis at 0, 0.25, 0.5, or 0.75 target pixels. It scores each box-resampled candidate by mean Sobel edge magnitude. The sampling image extends the last row and column to give the shifted boxes room while keeping the grid stride fixed.

The prepared subject, selected grid, and normalized edge map are saved as `build/prep/subject_rgba.png`, `phase_aligned.png`, and `edge_target.png`. The selected phase is recorded in `build/case.json`.
