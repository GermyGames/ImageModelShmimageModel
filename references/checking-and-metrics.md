# Conversion Checks and Visual Review

`shmimage.py check` compares `build/steps/04_cleanup.png` with the prepared reference on the native grid. Read `build/check/metrics.json` for the results. The default thresholds are listed below.

| Metric | Default target | What it measures |
| --- | --- | --- |
| `silhouette_iou` | ≥ 0.88 | Alpha-mask intersection over union at the native grid size. Two fully opaque frames score 1.0. |
| `edge_alignment` | ≥ 0.72 | F1 overlap of the strong Sobel edges in the prepared and finished images. |
| `mean_delta_e` | ≤ 14.0 | Mean Euclidean CIELAB color difference at foreground pixels. |
| `orphan_ratio` | ≤ 0.02 | Fraction of foreground pixels flagged as isolated palette colors among their eight neighbors. |
| `jaggie_index` | ≤ 0.08 | Fraction of foreground pixels flagged by the horizontal and vertical kink heuristic. |

`build/check/check_sheet.png` shows the alpha overlap, edge overlap, final art with defect outlines, and used palette with metric results. Open the original reference and artwork together to assess likeness, expression, and anatomy. In particular, check that eyes, hands, and other small features still read after cleanup.

If a conversion fails a check, first inspect the preparation and art. Try a larger native grid when detail is lost, `--dither none` when shading becomes noisy, or a different palette when colors drift. Deliberate changes of proportions and silhouette belong in the [hand-redraw workflow](hand-redraws.md).

## Hand-redraw hygiene checks (`check --manual`)

For artwork drawn directly on the native pixel grid without `prep` or `fit`, run:

```bash
python3 scripts/shmimage.py check cases/redraw --manual --max-colors 32
```

This writes `build/check/metrics.json` (`"mode": "manual"`) and `build/check/check_sheet.png`, checking:
- `step_sizes_match`: All existing passes in `build/steps/` share the target native dimensions.
- `semi_transparent_pixels`: Count of foreground pixels with `0 < alpha < 255` is `0` (catches accidental blur or anti-aliased edges).
- `orphan_ratio` & `jaggie_index`: Same defect detection and `acceptance.json` thresholds applied to the extracted foreground palette.
- `unique_colors` (when `--max-colors` is passed): Total foreground RGB colors stay within the budget. Pass `--image <path>` to inspect an earlier draft or specific PNG.
