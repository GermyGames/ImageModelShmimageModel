# Campfire

Draw an isolated campfire on a transparent 64 × 64 pixel grid. Use the wide pile
of crossed logs and tall, asymmetric flame from `source/reference.jpg`.
Use the charcoal and rust facets from `source/style-rocks.jpeg` for the fuel
and hearth. Use the stepped orange, gold, and cream clusters and upward sparks
from `source/style-fire.gif` for the flame.

The logs stay planted at the bottom center of every cell. Tongues of flame form
at the coals, stretch upward, and thin into cooler wisps. Their lifetimes overlap
so a fresh tongue is already rising as an older one breaks away. The side flames
and sparks have their own timing.

## Export

- `deliver/campfire_sheet.png` is a transparent 256 × 256 PNG with a 4 × 4 grid.
  Play the 16 cells left to right, then top to bottom, at 70 ms per frame.
- `deliver/campfire_loop.gif` shows the same 1.12-second loop at 5× scale on a
  charcoal background.
- Run `python3 cases/campfire/source/draw.py --export` from the project root
  with Pillow installed to rebuild the outputs.

The still passes are in `build/steps/`. The ordered animation passes and saved
revisions are in `build/animation/`.
