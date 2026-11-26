# Sprite Animation and Review

Start from the latest approved still or loop. Keep the existing direction, stance, and character proportions unless the requested motion needs a change. When revising a loop, preserve its frame order, timing, and contact poses unless those are part of the feedback.

## Block the primary action

1. Set a shared native frame canvas, a consistent anchor, and room for limbs and props at their extremes. Keep the anchor fixed across frames, even when the figure bobs.
2. For a walk, block contact, down, passing, and up poses on both sides. Draw the boot paths and test the loop before working on secondary movement. In an in-place walk, the planted foot moves back on its contact line as the body would move forward in the game. Keep the foot on that line until lift-off. Check the transition from the last frame back to the first.
3. Save a silhouette strip and a flat-color strip at the same grid and frame order as the final sheet. Inspect the main movement and overlaps at native size and an integer zoom before shading.

## Animate fire

- Keep the fuel and the origin of the flame fixed. Block individual tongues as they form at the source, stretch upward, pinch at the trailing edge, and peel away as cooler wisps. A little lateral curl can shape a tongue as it rises. If the fire reads as a wiggle, follow a bright cluster and its tip across adjacent frames and redraw their upward path.
- Stagger the tongues so fresh flame is already rising when older tips break away. Give side flames and sparks their own timing. If a detached shape reads as a floating fireball, narrow its tail before release and shrink and darken the fragment as it rises.
- Play the loop at delivery speed. Check that bright clusters climb through the flame itself and that new tongues and drifting embers carry through the last-to-first transition. For one local implementation, see the [campfire drawing source](../cases/campfire/source/draw.py).

## Add secondary motion to the parts that move

- **Soft parts.** Attach the beard, cloth, or hair at its root. Let tips and hems travel farther and settle a beat after the stride or turn. Keep the head, belt, and other nearby landmarks out of the deformation.
- **Arms and armor.** Track the shoulder, elbow, and wrist through adjacent frames. If the shoulder appears to jitter while the hand barely moves, anchor the shoulder to the torso and give the forearm and hand a clear swing. Move the bracer and hand together through the arc. Let the sleeve flex at the elbow only as needed to keep the connection. On a load-bearing arm, anchor the wrist at the grip and let the elbow absorb the movement.
- **Rigid props.** Treat the whole prop as one object and keep it attached to the hand. Resampling a small prop at a different angle each frame can make its bevels crawl even when the geometry is rigid. If that happens, use a fixed orientation and whole-pixel shifts with the grip. If the action needs a turn, draw and check a few consistent orientations around the grip. Compare aligned blade outlines, shaft, and grip at native size.

## Verify and export

Review both a contact sheet and the moving loop. A strip shows proportions and contact, while playback reveals pixel shimmer, seams, foot sliding, and shoulder movement that doesn't carry into the arm. Zoom the reported problem area across neighboring frames, then return to native size to judge whether the change reads in play. For a targeted revision, compare against the previous sheet and keep edits local where possible.

Keep frame cells equally sized and transparent, with room at their edges. Export the native sheet and a nearest-neighbor looping preview. Verify that the preview plays the same frames in the same order and timing. Give the frame dimensions, playback order, and frame timing with the exported files. Keep the still and the animation stage sheets in separate build paths, and save reviewed animation revisions before replacing the working sheet.
