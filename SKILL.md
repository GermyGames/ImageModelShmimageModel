---
name: shmimage
description: Convert images into palette-limited pixel art, hand-redraw subjects in a reference style, animate sprites and export spritesheets, or create and restyle seamless pixel-art tiles.
---

# Image Model Shmimage Model

Work locally and build on a native pixel grid. Use an image generation workflow only when the user explicitly requests it.

## Choose the workflow

| User intent | Workflow |
| --- | --- |
| Create or restyle an infinitely repeating surface such as cliff, soil, foliage, or masonry, with or without a reference | Draw on a wrapping native grid. Follow [Seamless tiles and styling](references/seamless-tiles.md) and review both the joins and the visible repeat. |
| Pixelate a source, keep its framing and proportions, or apply a fixed palette | Use the conversion CLI below |
| Redraw or restyle a subject, use a separate style reference, or revise an expression, pose, or anatomy | Draw or edit the pixels directly. Follow [Hand redraws and visual review](references/hand-redraws.md) |
| Animate a sprite or effect, create a spritesheet, or revise an existing loop | Start from the latest approved art when available. [Sprite animation and review](references/sprite-animation.md) covers walk cycles, fire, and loop checks. |

Identify what makes the subject recognizable and which features the style changes. For a portrait, check the contour of the head and jaw, expression, gaze, shoulders, hands, and any held objects. For a revision, use the latest approved image as the base and compare the changed area to the original reference.

## Review the art

- **Before shading**, view the silhouette and block-in at native size and at an integer zoom. Compare them with the subject reference when available. Check proportions and landmarks for a sprite, or the distribution and cadence of forms for a tile.
- **Before delivery**, inspect the final art at both sizes. Check contours, readability, the requested style, and palette. Inspect a repeated field for tiles.
- Save the silhouette, block-in, shading, and cleanup PNGs on the same native grid in `cases/<case>/build/steps/`. Keep animation stages in their own subdirectory so they don't overwrite the still. Export previews with integer nearest-neighbor scaling.

## Convert a source image

Create a case, prepare its grid, and fit the palette. Use `--bg-mode none` for scenes that keep the whole frame. Choose `auto` for an isolated subject.

```bash
python3 scripts/shmimage.py init cases/portrait --input /path/to/photo.jpg --size 112 --palette auto --colors 24
python3 scripts/shmimage.py prep cases/portrait --bg-mode none
python3 scripts/shmimage.py fit cases/portrait --dither none --cleanup-passes 1
python3 scripts/shmimage.py check cases/portrait
python3 scripts/shmimage.py deliver cases/portrait --scale 4
```

Review the silhouette and block-in saved by `fit` before accepting the later passes. Use [Prep and masks](references/prep-and-masks.md) for framing and phase alignment and [Passes and cleanup](references/passes-and-cleanup.md) to tune color and detail.

For a source with useful line work or details worth protecting, run `extract` to create editable guides. Use `style` to sample a palette and outline settings from a separate reference. Review the guides before applying them with `fit`. [See guided conversion and the local mask editor](references/guided-conversion.md).

Read `build/check/metrics.json` and inspect `build/check/check_sheet.png` after `check`. Investigate failing metrics alongside the visual comparison. A fully opaque frame can score perfect silhouette overlap, and a passing edge score can coexist with an unreadable expression. See [Checking and metrics](references/checking-and-metrics.md) for what the checks measure.

## Deliver

Save the first draft you review and each distinct visual revision before overwriting the working art. Include refinements from your own review and from user feedback. Give each snapshot a short label and reuse the case for later revisions.

For still art, use `record-revision` and `deliver`. The export adds saved history as a labeled chapter after the four build passes. Review it and link the native PNG, scaled PNG, and timelapse from `cases/<case>/deliver/`. Include the Aseprite file when exported. For locally drawn passes, use `deliver --manual`. See [Export options and revision history](references/aseprite-and-delivery.md) for the commands.

For animation, save each revision as a complete ordered sheet or frame sequence. Deliver the native transparent spritesheet and a looping preview of the same frames and timing.
