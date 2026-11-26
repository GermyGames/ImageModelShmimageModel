# Hand Redraws and Visual Review

Use a local pixel editor or write shapes and pixels directly on the native grid. Use the source image for identity, pose, and composition. Use a separate style reference for choices such as pixel size, shading, palette, and outline treatment.

## Build and review the four passes

| File in `build/steps/` | What to draw and check |
| --- | --- |
| `01_silhouette.png` | Establish the framing, stance, head and shoulder widths, arm positions, and held objects. Check whether the contour and pose read at native size. |
| `02_blockin.png` | Place the flat colors and identity landmarks. Open the source and the block-in side by side at corresponding zooms. For a portrait, compare the chin and cheek contour, pupil placement within each eye, mouth shape, and shoulder height. Follow each forearm into the wrist and check finger placement, overlap, and contact with any props. Fix the construction here before shading. |
| `03_shading.png` | Add the color ramps, contour accents, and texture seen in the style reference. Keep the expression and gesture readable when the shading is in place. |
| `04_cleanup.png` | Refine the important clusters and remove distracting pixels. Inspect at native size and again at an integer nearest-neighbor zoom. Keep isolated pixels that carry meaning, such as highlights or pupils. |

Save a snapshot after each distinct visual revision, including drafts you refine yourself. For feedback on an existing image, reuse its case and save the current version before editing if it is missing from the history. Confine edits to the requested areas and any adjoining contours that need to connect. Check the result against the subject reference and the previous version. [See the revision recording commands](aseprite-and-delivery.md#record-revisions-for-the-timelapse).

## Resolve the construction before adding detail

- **Style.** Compare the block-in with the style reference at similar figure heights. Look at the head-to-body ratio, how the poses carry weight, and the size of the major light and shadow shapes. A palette match alone can leave the sprite too stiff or too close to the photo.
- **Face.** Place the brow, eyes, nose, and cheeks on the same head turn before laying in rim light or hair. Leave enough room under headgear for the intended gaze. Deliberate occlusion should follow the angle of the helmet or cheek guard. At native size, check that the nose still reads as part of the face and that the mouth or mustache carries the intended expression.
- **Arms and grip.** Trace each arm from shoulder through elbow and cuff to the hand. Use the wrist transition, thumb silhouette, and a grouped shape for curled fingers to show which way the hand faces. A small crease can separate the fingers without turning them into equally spaced stripes. With two hands on a prop, check that both contacts and the overlap read. If the pose is flexible and the grip becomes crowded, simplify the pose before adding detail.
- **Held objects.** Draw a single centerline through the shaft, socket, and cap. Choose the prop's orientation and view before drawing the blades or fittings. For a symmetrical head seen from one plane, build both sides from the same profile and apply the tilt to the entire object. Keep the visible shaft continuous through the grip, and check where it ends or meets the ground.

## Export

Run `init` with the subject reference to make the case directory. Save the four same-sized PNGs under `build/steps/`. The native canvas of those PNGs determines the export dimensions.

```bash
python3 scripts/shmimage.py init cases/redraw --input /path/to/photo.jpg --size 112
python3 scripts/shmimage.py deliver cases/redraw --manual --scale 4
```

Manual export reads the palette from the final PNG and uses the original reference for the timelapse. Source-alignment metrics from `check` apply to the conversion workflow. For a redraw, use the visual review above and verify the exported dimensions and any requested palette.
