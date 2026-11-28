# Germy Games Pixel Art Logo

- Case name `germy-games-logo`
- Subject reference `/home/jeremym/media/Storage/Dev/ImageModelShmimageModel/cases/germy-games-logo/source/reference.png`
- Native canvas `256 × 192` pixels (4:3 framing; logo fills roughly `220 × 150` px)
- Palette: Custom hand-curated 29-color palette (`COLORS` in `source/draw.py`), strictly palette-locked with zero Gaussian blur or anti-aliased blending

## Art Direction

Hand-redraw the uploaded Germy Games logo on a large `256 × 192` native pixel grid via `cases/germy-games-logo/source/draw.py`.

Required identity landmarks carried over from the reference:
- Plump arched kidney-bean purple jelly body with a uniform bright lavender outer membrane.
- All 10 grouped pairs (20 total) of radiating rounded cilia preserving the reference grouping, angles, and subtle organic length variation.
- Glossy circular black eyes set wide on the cheeks with curved upper-left specular crescent glints and subtle lower-right bounce sheen.
- Goofy wide arched open mouth with a bold dark ink outline, upturned corner flicks, 4 chunky white upper teeth (2 outer corner teeth and 2 central buck teeth separated by a center gap), dark maroon interior, and a fiery orange-red shaded tongue.
- Translucent internal jelly bubbles/vacuoles (bright upper-left sparkle bubble, tiny upper-right dot, softer lower-right cheek vacuole).
- Hand-authored arched condensed uppercase pixel lettering **"GERMY GAMES"** hugging the concave bottom belly, wrapped together with the germ in a unified puffy stepped violet neon halo/sticker contour on the `#210351` deep midnight-purple background.

## Review

Compare `01_silhouette.png` and `02_blockin.png` against the reference at native 1× and integer zoom before accepting shading, checking bean proportions, the 10 pairs of cilia, eye and mouth landmarks, and `"GERMY GAMES"` legibility. Review `03_shading.png` and `04_cleanup.png` at both 1× and 4×, record each reviewed draft and polish pass with `record-revision`, and export with `deliver --manual --scale 4`.

## Revisions

- **Revision 1 (`First reviewed draft`)**: Initial `256 × 192` full four-pass render with 10 pairs of cilia, glossy eyes, 4-tooth mouth with fiery tongue, arched condensed `"GERMY GAMES"` lettering, and stepped neon sticker halo.
- **Revision 2**: Smoothed C1-continuous jelly body shading, replaced noisy typography drop-shadow speckles with a clean neon outline, pulled outer teeth inward from the acute mouth corners, and fused cilia roots cleanly beneath the continuous outer membrane.
- **Revision 3**: Unified analytic jelly gradient across the rounded cheek endcaps, adjusted text arch and halo thickness for an unbroken mid-violet band under the belly, unified cilia tip glints and bottom-rim letter tint, and cleaned stray 1-pixel isolated islands (final exact palette: 29 colors).

