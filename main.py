from math import ceil
from statistics import fmean

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


def map2d(func, grid):
    return [[func(value) for value in row] for row in grid]


def get_char_brightness_dict(char_image_dict):
    char_brightness_dict = normalize_brightnesses(
        {char: get_brightness(char_image_dict[char]) for char in char_image_dict}
    )

    return char_brightness_dict


def brightness_converter(segments: list[list[Image.Image]], char_brightness_dict):
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

    rows = ["".join(row) for row in map2d(lambda x: round_to_char(x), brightness_grid)]
    return "\n".join(rows)


def px_diff_converter(segments: list[list[Image.Image]], char_image_dict):
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

    rows = ["".join(row) for row in map2d(lambda x: compare_to_char(x), segments)]
    return "\n".join(rows)


if __name__ == "__main__":
    chars = " `1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?"
    font_path = "./GeistMono-Regular.otf"
    font = ImageFont.truetype(font=font_path, size=50)
    img_path = "./img.png"

    with Image.open(img_path).convert("RGBA") as im:
        # add white background to transparent images
        new_im = Image.new("RGBA", im.size, "WHITE")
        new_im.paste(im, (0, 0), im)
        im = new_im.convert("L")  # greyscale

        char_image_dict: dict[str, Image.Image] = gen_char_images(chars, font)

        segments = divide_image(
            im,
            200,
            list(char_image_dict.values())[0].height
            / list(char_image_dict.values())[0].width,
        )

        char_image_dict = {
            char: char_image_dict[char].resize(segments[0][0].size)
            for char in char_image_dict
        }

        # char_brightness_dict = get_char_brightness_dict(char_image_dict)

        # print(char_brightness_dict)
        # print(brightness_converter(segments, char_brightness_dict))

        print(px_diff_converter(segments, char_image_dict))
