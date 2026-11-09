"""アイコン生成：インディゴのグラデーションに「FE」の文字。python3 tools/make_icons.py で icons/ を作り直す。"""
from PIL import Image, ImageDraw, ImageFont
import os

FONT = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
TOP, BOTTOM = (99, 102, 241), (55, 48, 163)  # #6366f1 → #3730a3
OUT = os.path.join(os.path.dirname(__file__), '..', 'icons')


def gradient(size):
    im = Image.new('RGB', (size, size))
    px = im.load()
    for y in range(size):
        t = y / (size - 1)
        c = tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
        for x in range(size):
            px[x, y] = c
    return im


def draw_text(im, ratio):
    size = im.size[0]
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, int(size * ratio))
    box = d.textbbox((0, 0), 'FE', font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((size - w) / 2 - box[0], (size - h) / 2 - box[1]), 'FE', font=f, fill=(255, 255, 255))


def rounded(im, radius_ratio):
    size = im.size[0]
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), int(size * radius_ratio), fill=255)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out.paste(im.convert('RGBA'), (0, 0), mask)
    return out


def make(size, name, ratio, round_corner):
    im = gradient(size)
    draw_text(im, ratio)
    if round_corner:
        rounded(im, 0.22).save(os.path.join(OUT, name))
    else:
        im.save(os.path.join(OUT, name))


os.makedirs(OUT, exist_ok=True)
make(192, 'icon-192.png', 0.46, True)
make(512, 'icon-512.png', 0.46, True)
make(512, 'icon-512-maskable.png', 0.34, False)   # 端が切り取られても文字が残るよう小さめ・角丸なし
make(180, 'apple-touch-icon.png', 0.46, False)     # iOS が角を丸める
print('done')
