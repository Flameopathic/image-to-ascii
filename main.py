from math import ceil
from os import path

from PIL import Image, ImageDraw, ImageFont, ImageText

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
            char_dict[char] /= max

    return dict(sorted(char_dict.items(), key=lambda item: item[1]))


if __name__ == "__main__":
    chars = " `1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?"
    font = ImageFont.truetype(font="./GeistMono-Regular.otf", size=50)
    img_path = path.normpath("./img.png")

    with Image.open(img_path) as im:
        im.convert("L")

        divide_image(im, 20)

        char_dict = char_brightness_dict(chars, font)

        sorted_str = ""
        for char in char_dict.keys():
            sorted_str += char

        print(sorted_str)
