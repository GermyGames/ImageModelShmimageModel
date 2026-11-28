# Germy Wearing Studio Monitor Headphones

- Case name `germy-headphones`
- Subject reference `/home/jeremym/media/Storage/Dev/ImageModelShmimageModel/cases/germy-headphones/source/reference.png` (`cases/germy-games-logo/deliver/germy-games-logo_1x.png`)
- Native canvas `256 × 192` pixels RGBA
- Palette: Custom hand-curated 39-color palette (`COLORS` in `source/draw.py`), strictly palette-locked with zero Gaussian blur, anti-aliasing, or semi-transparent pixels

## Art Direction

Create a text-free variant of the Germy mascot on a `256 × 192` native pixel grid via `cases/germy-headphones/source/draw.py`, centered vertically and wearing chunky studio monitor headphones.

Preserved Germy landmarks:
- Arched kidney-bean purple jelly body with smooth C∞ shading and continuous bright lavender outer membrane.
- All 10 grouped pairs (20 total) of rounded cilia radiating around the crown and peeking behind the earcups/yokes.
- Glossy circular black eyes with upper-left specular crescent glints and subtle lower-right bounce sheen.
- Goofy wide arched open mouth with bold dark outline, tapered upturned corner flicks, 4 rounded upper teeth (2 outer corner teeth + 2 central buck teeth with a 2 px center gap), dark maroon interior, and fiery multi-tone orange-red tongue.
- Translucent internal jelly bubbles/vacuoles and the stepped neon purple sticker halo on `#210351`.

Added studio monitor headphones:
- Plush vertical-oval circumaural earpads clamping snugly onto the left and right cheeks with cheek contact shadows and violet rim bounce light.
- Stepped closed-back matte-charcoal monitor driver housings with brushed steel trim rings, recessed acoustic backplate grooves, and a left-cup cable strain-relief jack boot.
- Brushed steel telescoping C-yoke sliders with adjustment notches and classic studio L/R indicator bars (`#29b6ff` blue left, `#ff3b5c` red right).
- Wide contoured padded studio headband arching cleanly over the top cilia crown with brushed metal end-clamps and reflected violet under-glow.

## Review

Inspect `build/check/review_sheet.png` (generated via `review-sheet`) at 1× and integer zoom for passes 1–2 before shading, then review all four passes together alongside `check --manual --max-colors 39` (`build/check/check_sheet.png`), record each reviewed draft and polish pass via `record-revision`, and export with `deliver --manual --scale 4`.

## Revisions

- **Revision 1 (`First reviewed draft`)**: Initial `256 × 192` text-free Germy variant wearing studio monitor headphones (circumaural earpads, closed-back driver housings, steel yokes with adjustment notches, studio L/R markers, contoured padded headband, and left-cup jack boot).
- **Revision 2**: Masked cilia/membrane specular glints beneath headphones, curved the brushed steel cup bezel rings, aligned end-clamps to the headband curve tangent, restored crisp steel slider notches, and closed the inner arch halo gap.
- **Revision 3**: Tapered the headband top bevel highlight smoothly and cleaned up the swivel pivot cluster (final verified palette: 39 colors, `semi_transparent_pixels: 0`, `orphan_ratio: 0.0001`).

