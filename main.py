from math import ceil
from os import path
from statistics import fmean

from PIL import Image, ImageDraw, ImageFont, ImageStat

glyph_ratio = 2  # x / y


def divide_image(img: Image.Image, x_segs: int):
    x_step = img.width / x_segs
    y_step = x_step * glyph_ratio
    y_segs = ceil(img.height / y_step)

    segments = []
    for yi in range(y_segs):
        row = []
        for xi in range(x_segs):
            row.append(
                img.copy().crop(
                    (
                        xi * x_step,
                        yi * y_step,
                        min((xi + 1) * x_step, img.width),
                        min((yi + 1) * y_step, img.height),
                    )
                )
            )
        segments.append(row)

    return segments


def map2d(func, grid):
    return [[func(value) for value in row] for row in grid]


def char_brightness_dict(chars: str, font: ImageFont.FreeTypeFont):
    char_dict: dict[str, float] = {}

    for char in chars:
        box = font.getbbox(char)
        width = int(box[2])
        height = int(box[3])

        im = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(im)
        draw.text((0, 0), char, 255, font=font)
        colors = im.getcolors()

        total = 0
        if type(colors) is list:
            for c in colors:
                if type(c[0]) is int and type(c[1]) is int:
                    total += c[0] * c[1]

        char_dict[char] = total

    max = 0
    for char in char_dict:
        if char_dict[char] > max:
            max = char_dict[char]

    if max != 0:
        for char in char_dict:
            char_dict[char] = 1 - (char_dict[char] / max)

    return dict(sorted(char_dict.items(), key=lambda item: item[1]))


def brightness_converter(segments: list[list[Image.Image]], char_dict):
    brightness_grid = map2d(lambda im: fmean(ImageStat.Stat(im).mean) / 255, segments)

    def round_to_char(seg_brightness: float, char_dict: dict[str, float]):
        return list(char_dict.keys())[
            list(char_dict.values()).index(
                min(
                    char_dict.values(),
                    key=lambda char_brightness: abs(char_brightness - seg_brightness),
                )
            )
        ]

    rows = [
        "".join(row)
        for row in map2d(lambda x: round_to_char(x, char_dict), brightness_grid)
    ]
    return "\n".join(rows)


if __name__ == "__main__":
    chars = " `1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?"
    font = ImageFont.truetype(font="./GeistMono-Regular.otf", size=50)
    img_path = path.normpath("./img.png")

    with Image.open(img_path).convert("L") as im:
        segments = divide_image(im, 100)
        char_dict = char_brightness_dict(chars, font)

        print(brightness_converter(segments, char_dict))
