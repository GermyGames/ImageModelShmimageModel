# Conversion Passes and Cleanup

`shmimage.py fit` writes these passes to `build/steps/`.

| Pass | Operation |
| --- | --- |
| `01_silhouette.png` | Threshold the alpha of the phase-aligned reference at 128. |
| `02_blockin.png` | Match pixels to the closest palette colors in CIELAB and smooth some low-edge regions with a local majority filter. The `auto` palette comes from CIELAB k-means on foreground pixels. |
| `03_shading.png` | Recompute palette matches after applying `--hue-shift` and optional ordered dithering to the aligned colors. |
| `04_cleanup.png` | Apply orphan removal and local kink smoothing for `--cleanup-passes` iterations. The optional `--sel-out` flag adds a dark, palette-based edge outline. |

Start with `--dither none` for flat regions. Use `bayer2` or `bayer4` when the target style needs patterned shading. Compare the shading and cleanup passes at the face, hands, and other focal points. Cleanup can remove an intentional single pixel, so adjust the cleanup count or restore the detail by hand when it affects readability.
