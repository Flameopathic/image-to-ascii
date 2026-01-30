from math import ceil
from statistics import fmean

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

glyph_ratio = 2  # x / y


def divide_image(im: Image.Image, x_segs: int):
    x_step = im.width / x_segs
    y_step = x_step * glyph_ratio
    y_segs = ceil(im.height / y_step)

    # make image tall enough
    im = im.convert("RGBA")
    new_im = Image.new("RGBA", (im.width, int(y_step * y_segs)), "WHITE")
    new_im.paste(im, (0, 0), im)
    im = new_im.convert("L")

    segments = []
    for yi in range(y_segs):
        row = []
        for xi in range(x_segs):
            row.append(
                im.copy().crop(
                    (
                        xi * x_step,
                        yi * y_step,
                        min((xi + 1) * x_step, im.width),
                        min((yi + 1) * y_step, im.height),
                    )
                )
            )
        segments.append(row)

    return segments


def map2d(func, grid):
    return [[func(value) for value in row] for row in grid]


def get_char_brightness_dict(chars: str, font_path: str):
    font = ImageFont.truetype(font=font_path, size=50)
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

    def round_to_char(seg_brightness: float):
        return list(char_dict.keys())[
            list(char_dict.values()).index(
                min(
                    char_dict.values(),
                    key=lambda char_brightness: abs(char_brightness - seg_brightness),
                )
            )
        ]

    rows = ["".join(row) for row in map2d(lambda x: round_to_char(x), brightness_grid)]
    return "\n".join(rows)


def px_diff_converter(segments: list[list[Image.Image]], chars: str, font_path: str):
    font = ImageFont.truetype(font=font_path, size=50)

    width = max([int(font.getbbox(char)[2]) for char in chars])
    height = max([int(font.getbbox(char)[3]) for char in chars])

    char_dict = {}
    for char in chars:
        im = Image.new("L", (width, height), 255)
        draw = ImageDraw.Draw(im)
        draw.text((0, 0), char, 0, font=font)

        im = im.resize(segments[0][0].size)

        char_dict[char] = im

    def compare_to_char(seg: Image.Image):
        best_char = ""
        best_diff = -1
        for char in char_dict:
            diff = fmean(
                ImageStat.Stat(ImageChops.difference(seg, char_dict[char])).mean
            )
            if best_diff == -1 or diff < best_diff:
                best_diff = diff
                best_char = char
        return best_char

    rows = ["".join(row) for row in map2d(lambda x: compare_to_char(x), segments)]
    return "\n".join(rows)


if __name__ == "__main__":
    chars = " `1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?"
    font_path = "./GeistMono-Regular.otf"
    img_path = "./img.png"

    with Image.open(img_path).convert("RGBA") as im:
        # add white background to transparent images
        new_im = Image.new("RGBA", im.size, "WHITE")
        new_im.paste(im, (0, 0), im)
        im = new_im.convert("L")  # greyscale

        segments = divide_image(im, 300)

        # char_brightness_dict = get_char_brightness_dict(chars, font_path)
        # print(brightness_converter(segments, char_brightness_dict))

        print(px_diff_converter(segments, chars, font_path))
