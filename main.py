from math import ceil
from os import path

from PIL import Image

glyph_ratio = 2  # x / y


def divide_image(img: Image.Image, x_segs: int):
    x_step = img.width / x_segs
    y_step = x_step * glyph_ratio
    y_segs = ceil(img.height / y_step)

    segments = [[]]
    for xi in range(x_segs):
        row = []
        for yi in range(y_segs):
            row.append(
                img.copy().crop(
                    (xi * x_step, yi * y_step, (xi + 1) * x_step, ((yi + 1) * y_step))
                )
            )
        segments.append(row)

    return segments


if __name__ == "__main__":
    img_path = path.normpath("./img.png")

    with Image.open(img_path) as im:
        im.convert("L")

        divide_image(im, 20)
