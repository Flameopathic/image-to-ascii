from enum import Enum
from math import ceil
from statistics import fmean
from typing import Annotated

import typer
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat


def divide_image(im: Image.Image, x_segs: int, glyph_ratio: float):
    x_step = im.width / x_segs
    y_step = x_step * glyph_ratio
    y_segs = ceil(im.height / y_step)
    mode = im.mode

    # make image tall enough
    im = im.convert("RGBA")
    new_im = Image.new("RGBA", (im.width, int(y_step * y_segs)), "WHITE")
    new_im.paste(im, (0, 0), im)
    im = new_im.convert(mode)

    segments = []
    for yi in range(y_segs):
        row = []
        for xi in range(x_segs):
            row.append(
                im.copy().crop(
                    (
                        round(xi * x_step),
                        round(yi * y_step),
                        round(min((xi + 1) * x_step, im.width)),
                        round(min((yi + 1) * y_step, im.height)),
                    )
                )
            )
        segments.append(row)

    return segments


def gen_char_images(chars, font):
    width = max([int(font.getbbox(char)[2]) for char in chars])
    height = max([int(font.getbbox(char)[3]) for char in chars])
    char_image_dict = {}
    for char in chars:
        im = Image.new("L", (width, height), 255)
        draw = ImageDraw.Draw(im)
        draw.text((0, 0), char, 0, font=font)

        char_image_dict[char] = im

    return char_image_dict


def get_brightness(im: Image.Image):
    return fmean(ImageStat.Stat(im.convert("L")).mean) / 255


def normalize_brightnesses(char_brightness_dict: dict[str, float]):
    char_brightness_dict = dict(
        sorted(char_brightness_dict.items(), key=lambda item: item[1])
    )
    min_value = list(char_brightness_dict.values())[0]
    char_brightness_dict = {
        char: char_brightness_dict[char] - min_value for char in char_brightness_dict
    }
    max_value = list(char_brightness_dict.values())[-1]
    char_brightness_dict = {
        char: char_brightness_dict[char] / max_value for char in char_brightness_dict
    }
    return char_brightness_dict


def map2d(func, grid, do_print=False):
    if do_print:
        for i, row in enumerate(grid):
            for j, value in enumerate(row):
                grid[i][j] = func(value)
                print(grid[i][j], end="")
            print()
        return grid
    return [[func(value) for value in row] for row in grid]


def get_char_brightness_dict(char_image_dict):
    char_brightness_dict = normalize_brightnesses(
        {char: get_brightness(char_image_dict[char]) for char in char_image_dict}
    )

    return char_brightness_dict


def brightness_converter(
    segments: list[list[Image.Image]], char_brightness_dict, serial=False
):
    brightness_grid = map2d(lambda im: fmean(ImageStat.Stat(im).mean) / 255, segments)

    def round_to_char(seg_brightness: float):
        return list(char_brightness_dict.keys())[
            list(char_brightness_dict.values()).index(
                min(
                    char_brightness_dict.values(),
                    key=lambda char_brightness: abs(char_brightness - seg_brightness),
                )
            )
        ]

    rows = [
        "".join(row)
        for row in map2d(lambda x: round_to_char(x), brightness_grid, serial)
    ]
    return "\n".join(rows)


def px_diff_converter(segments: list[list[Image.Image]], char_image_dict, serial=False):
    def compare_to_char(seg: Image.Image):
        best_char = ""
        best_diff = -1
        for char in char_image_dict:
            diff = fmean(
                ImageStat.Stat(ImageChops.difference(seg, char_image_dict[char])).mean
            )
            if best_diff == -1 or diff < best_diff:
                best_diff = diff
                best_char = char
        return best_char

    rows = [
        "".join(row) for row in map2d(lambda x: compare_to_char(x), segments, serial)
    ]
    return "\n".join(rows)


def combine_bstr_diffstr(bstr: str, diffstr: str, serial=False):
    bmap = [[char for char in row] for row in bstr.splitlines()]
    diffmap = [[char for char in row] for row in diffstr.splitlines()]
    combination = ""
    for i, (brow, diffrow) in enumerate(zip(bmap, diffmap)):
        for j, (bchar, diffchar) in enumerate(zip(brow, diffrow)):
            if diffchar == " " or any(
                [
                    any(
                        [
                            i + di < 0
                            or i + di > len(diffmap) - 1
                            or j + dj < 0
                            or j + dj > len(diffrow) - 1
                            or diffmap[i + di][j + dj] == " "
                            for dj in range(-1, 2, 2)
                        ]
                    )
                    for di in range(-1, 2, 2)
                ]
            ):
                combination += diffchar
                if serial:
                    print(diffchar, end="")
            else:
                combination += bchar
                if serial:
                    print(bchar, end="")
        combination += "\n"
        if serial:
            print()
    return combination


class Algorithm(str, Enum):
    brightness = "brightness"
    px_diff = "px_diff"
    combo = "combo"


def main(
    algorithm: Annotated[
        Algorithm, typer.Argument(help="Algorithm used for conversion")
    ],
    image: Annotated[str, typer.Argument(help="Path to image to process")],
    size: Annotated[
        int, typer.Option(help="Number of characters per line of output")
    ] = 80,
    chars: Annotated[
        str, typer.Option(help="Set of characters used to form the output")
    ] = " `1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?",
    font: Annotated[
        str, typer.Option(help="Path to font used as reference for the output")
    ] = "./GeistMono-Regular.otf",
):
    image_font = ImageFont.truetype(font=font, size=50)

    with Image.open(image).convert("RGBA") as im:
        # add white background to transparent images
        new_im = Image.new("RGBA", im.size, "WHITE")
        new_im.paste(im, (0, 0), im)
        im = new_im.convert("L")  # greyscale

        char_image_dict: dict[str, Image.Image] = gen_char_images(chars, image_font)

        segments = divide_image(
            im,
            size,
            list(char_image_dict.values())[0].height
            / list(char_image_dict.values())[0].width,
        )
        char_image_dict = {
            char: char_image_dict[char].resize(segments[0][0].size)
            for char in char_image_dict
        }
        char_brightness_dict = get_char_brightness_dict(char_image_dict)

        match algorithm:
            case Algorithm.brightness:
                brightness_converter(segments, char_brightness_dict, True)
            case Algorithm.px_diff:
                px_diff_converter(segments, char_image_dict, True)
            case Algorithm.combo:
                combine_bstr_diffstr(
                    brightness_converter(segments, char_brightness_dict),
                    px_diff_converter(segments, char_image_dict),
                    True,
                )


if __name__ == "__main__":
    typer.run(main)
