"""Shared box sampling for case preparation and source-resolution guides."""

from math import ceil

import numpy as np
from PIL import Image


def pad_for_phase(
    image: Image.Image, target_size: tuple[int, int], max_phase: tuple[float, float]
) -> Image.Image:
    """Extend the far edges so Pillow accepts shifted sampling boxes."""
    right = ceil(max_phase[0] * image.width / target_size[0])
    bottom = ceil(max_phase[1] * image.height / target_size[1])
    pixels = np.asarray(image)
    padding = ((0, bottom), (0, right)) + ((0, 0),) * (pixels.ndim - 2)
    return Image.fromarray(np.pad(pixels, padding, mode="edge"))


def resample_phase(
    padded: Image.Image, source_size: tuple[int, int],
    target_size: tuple[int, int], phase: tuple[float, float],
) -> Image.Image:
    width, height = source_size
    x = phase[0] * (width / target_size[0])
    y = phase[1] * (height / target_size[1])
    return padded.resize(target_size, Image.Resampling.BOX, box=(x, y, width + x, height + y))
