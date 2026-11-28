# Aseprite Integration and Final Delivery

`shmimage.py deliver` writes the artwork to `cases/<case>/deliver/`. After a CLI conversion, use the default export. For [hand-drawn passes](hand-redraws.md), use `--manual` to read the colors in the final PNG. Both modes use nearest-neighbor scaling for the pixel art.

## Generated Artifacts

1. **`deliver/<case>_1x.png`:** Native `1:1` pixel resolution PNG ready for game engines (Godot, Unity, GameMaker).
2. **`deliver/<case>_<scale>x.png`:** Crisp nearest-neighbor upscaled PNG for presentation and review.
3. **`deliver/<case>_timelapse.gif`:** The four build stages, with the original reference alongside when available, followed by a revision chapter when the case has multiple saved versions.
4. **`deliver/<case>_palette.hex`:** Exported hex palette file compatible with Aseprite, Lospec, and Pyxel Edit.
5. **`deliver/<case>.aseprite` (Optional):** If `aseprite` is installed on the system `PATH` (or passed via `--aseprite-bin`), `deliver` executes `scripts/aseprite/build.lua` in headless batch mode (`aseprite -b`) to generate a native multi-layer `.aseprite` source file with separate layers for `Silhouette`, `Block-In`, `Shading`, and `Cleanup`.
6. **`deliver/<case>_palette.png`:** Preview of the palette with color usage percentages.
7. **Desktop App Icon Exports (`--app-icon`, square canvases only):** Adds `<case>_256.png`, `<case>_512.png`, `<case>_1024.png` (nearest-neighbor for integer upscales), and a multi-size `<case>.ico` (`16`, `32`, `48`, `64`, `128`, `256`). Use `python3 scripts/shmimage.py icon-preview cases/<case>` beforehand to inspect dock/taskbar legibility on light and dark backgrounds.

## Record Revisions for the Timelapse

Save the first draft you review, then run `record-revision` after every distinct visual adjustment before the next edit. The command defaults to `build/steps/04_cleanup.png`. Use `--image` to save an earlier pass or to import an existing draft.

```bash
python3 scripts/shmimage.py record-revision cases/redraw --label "First reviewed draft"
# Edit the working artwork and save the revised PNG.
python3 scripts/shmimage.py record-revision cases/redraw --label "Softened the smile"
python3 scripts/shmimage.py deliver cases/redraw --manual --scale 4
```

The case stores numbered native PNGs in `build/revisions/`. Consecutive versions with identical pixels share one snapshot. `deliver` saves the current export if its pixels changed and can pick up an existing native export as a starting point for an older case. To import older drafts, record each available PNG in creation order before carrying on with new edits.

The GIF shows each saved edit in order, with the immediately preceding draft on the left and the result on the right. The comparison zooms into the changed area when the two native grids match and shows both full canvases when the grid size changes.
