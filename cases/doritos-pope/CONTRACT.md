# Pixel Art Conversion Contract

- **Case Name:** doritos-pope
- **Source Image:** /home/jeremym/media/Storage/Dev/ImageModelShmimageModel/cases/doritos-pope/source/reference.jpg
- **Target Max Dimension:** 160 px
- **Palette Mode:** auto (36 colors max)
- **Dithering:** none
- **Cleanup Passes:** 1

## Art Direction Notes

- Preserve recognizable silhouette proportions and key focal landmarks (eyes, face, weapon/prop contours).
- Favor clean, readable pixel clusters over noisy single-pixel confetti.
- Keep outer silhouette crisp with binary transparency (no semi-transparent edge fringe).

- Retouch the eyes and nose in the cleanup pass with colors from the fitted palette.

## Acceptance Criteria

Must pass all thresholds in `acceptance.json` before final delivery:
- `silhouette_iou >= 0.88`
- `edge_alignment >= 0.72`
- `orphan_ratio <= 0.02`
- `jaggie_index <= 0.08`
