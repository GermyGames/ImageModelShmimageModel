# Guided Pixel-Art Conversion

The guide tools run locally with Python, NumPy, and Pillow. A browser can open the generated mask editor directly from its file path.

## Extract guides from the subject

Run `init` and `prep` to choose the case's native grid. Use `fit` once first if you want a palette block-in in the editor. Then run `extract` with a method that suits the source.

| Method | Use it for | How it finds candidate lines |
| --- | --- | --- |
| `ink` | Comics and inked drawings | Finds dark strokes against their local surroundings. |
| `xdog` | Photos and rendered images | Finds dark ridges at two blur scales with a soft threshold. |
| `regions` | Paintings and images with broad color masses | Groups locally smoothed colors and emphasizes boundaries with underlying color contrast. |

```bash
python3 scripts/shmimage.py extract cases/portrait --method xdog
```

The command saves `lineart.png`, `detail_mask.png`, `overlay.png`, and a self-contained `review.html` in `build/guides/`. The candidate masks use the exact case grid, including its phase alignment. The detail mask marks small local luminance and color changes such as bright teeth, highlights, or dark pupils.

Open the generated `build/guides/review.html` in your browser and compare the prepared source with the grid. The project file `scripts/guide_review.html` is the template used to generate it. File previews that disable JavaScript show the source and overlay. Open the generated file in a browser with JavaScript enabled for the brush controls.

Cyan shows the line mask and orange shows protected details. Pick either layer, use **Keep** to add pixels or **Erase** to clear them, then download the edited masks as PNGs. The page supports integer zoom and undo. White pixels select a location in a mask. A pixel editor can edit the same PNGs directly.

Increase `--line-threshold` or `--detail-threshold` for sparser candidates. Both accept values greater than zero up to one. `--region-colors` adjusts the number of color groups in `regions` mode. Rerunning `extract` regenerates the original candidates in `build/guides/`, so save your edited masks separately.

## Sample a style and apply the guides

The style command estimates a small palette, a likely outline color, and a stroke width. It can detect exact integer enlargement, or you can set `--pixel-scale` for a known enlargement. The resulting JSON is editable. Set `outline.width` to `1` to retain the mask's existing thickness. The chosen outline color must be present in the palette.

```bash
python3 scripts/shmimage.py style --input /path/to/style.png --output cases/portrait/style.json --colors 16
python3 scripts/shmimage.py fit cases/portrait --style cases/portrait/style.json \
  --lineart /path/to/edited/lineart.png --detail-mask /path/to/edited/detail_mask.png
python3 scripts/shmimage.py check cases/portrait
python3 scripts/shmimage.py deliver cases/portrait --scale 4
```

The three `fit` options can be used independently. The style supplies the palette and the line-mask ink settings. With a line mask alone, `fit` uses the darkest active palette color. The automatic palette sets aside room for colors sampled from the detail mask. With a fixed palette, protected details use the nearest available color. In both cases, that color survives shading and cleanup. Detail protection takes precedence where the masks overlap.

Review the finished sprite beside the source. The guides estimate visible structure and often capture incidental texture as well. An intentional protected highlight can still appear in the diagnostic sheet as an isolated pixel.
