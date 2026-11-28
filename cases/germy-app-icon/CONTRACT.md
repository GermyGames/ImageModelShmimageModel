# Germy Headphones Desktop App Icon

- Case name `germy-app-icon`
- Subject reference `/home/jeremym/media/Storage/Dev/ImageModelShmimageModel/cases/germy-app-icon/source/reference.png` (`cases/germy-headphones/deliver/germy-headphones_1x.png`)
- Native canvas `128 × 128` pixels RGBA (`alpha = 0` outside the squircle tile, `alpha = 255` inside)
- Palette: Custom hand-curated 41-color palette (`COLORS` in `source/draw.py`), strictly palette-locked with binary alpha and zero anti-aliasing or blur

## Art Direction

Re-author Germy wearing studio monitor headphones natively on a `128 × 128` pixel-art desktop app icon grid via `cases/germy-app-icon/source/draw.py` (no downsampling from the `256 × 192` banner art).

Key icon container & subject landmarks:
- Centered `116 × 116` beveled dark-violet superellipse ("squircle") app tile (`x, y ∈ [6, 122]`) with transparent exterior corners, crisp dark `hp_ink` border for light and dark docks, lit top-left bevel, shaded bottom-right rim, subtle inner ambient glow, and soft grounding shadow below Germy.
- Bold chunky Germy proportions tuned for readability down to `32×32` taskbar size while keeping detail crisp up to `512×512`/`1024×1024`: arched purple jelly body, continuous glowing lavender membrane, all 10 grouped pairs (20 total) of separated cilia, glossy eyes with upper-left crescent glints, goofy 4-tooth open mouth with upturned corner flicks and fiery shaded orange-red tongue, and translucent internal bubbles.
- Studio monitor headphones: circumaural earpads with cheek contact shadows and violet rim bounce light, closed-back driver housings with curved steel bezel rings and acoustic backplate grooves, brushed steel notched sliders with blue/red studio L/R indicators, contoured padded headband with tangent-aligned metal end-clamps, and a compact left-cup strain-relief jack boot.
- Stepped neon purple halo clipped cleanly inside the squircle interior.

## Desktop Icon Exports

Export standard desktop sizes alongside the skill's `deliver/` artifacts:
- `deliver/germy-app-icon_1x.png` (`128 × 128`)
- `deliver/germy-app-icon_256.png` (`256 × 256`, 2× nearest-neighbor)
- `deliver/germy-app-icon_4x.png` (`512 × 512`, 4× nearest-neighbor)
- `deliver/germy-app-icon_1024.png` (`1024 × 1024`, 8× nearest-neighbor)
- `deliver/germy-app-icon.ico` (multi-size `.ico`: `256, 128, 64, 48, 32, 16`)

## Review

Inspect passes 1–2 via `review-sheet --steps 1,2 --scale 4`, then review all four passes together with `check --manual --max-colors 41` and a light/dark dock-size preview sheet (`128px`, `64px`, `48px`, `32px`), recording each reviewed draft and polish pass via `record-revision` before final `deliver --manual --scale 4`.

## Revisions

- **Revision 1 (`First reviewed draft`)**: Native `128 × 128` Germy + studio monitor headphones centered inside a `114 × 114` beveled dark-violet squircle tile with transparent corners, stepped inner neon halo, 10 separated cilia pairs, glossy eyes, 4-tooth mouth, orange-red tongue, and detailed monitor cups/yokes/headband.
- **Revision 2**: Expanded the radial `tile_glow` inner vignette so all 41 palette colors are active, replaced the flat bottom depth cut with a curved floor vignette + grounding shadow, extended the top-left squircle bevel corner glint, and cleaned slider/jack highlight speckles (`orphan_ratio: 0.0002`, `semi_transparent_pixels: 0`).

