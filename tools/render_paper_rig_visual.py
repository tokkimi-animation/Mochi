from __future__ import annotations

import math
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "rig_tests"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "ep001_paper_rig_visual.mp4"
THUMB = OUT_DIR / "ep001_paper_rig_visual_thumb.png"

W, H = 1280, 720
FPS = 24
DURATION = 30


def font(size: int):
    for path in ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


FONT = font(30)
SMALL = font(18)


def ease(x: float) -> float:
    x = max(0, min(1, x))
    return x * x * (3 - 2 * x)


def cut_ellipse(src: Image.Image, box, soften=8, grow=0):
    crop = src.crop(box).convert("RGBA")
    w, h = crop.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((grow, grow, w - grow, h - grow), fill=255)
    if soften:
        mask = mask.filter(ImageFilter.GaussianBlur(soften))
    crop.putalpha(mask)
    return crop


def cut_round_rect(src: Image.Image, box, radius=60, soften=6):
    crop = src.crop(box).convert("RGBA")
    w, h = crop.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    if soften:
        mask = mask.filter(ImageFilter.GaussianBlur(soften))
    crop.putalpha(mask)
    return crop


def build_assets():
    mochi = Image.open(ROOT / "assets" / "characters" / "mochi_reference.png").convert("RGB")
    zumu = Image.open(ROOT / "assets" / "characters" / "zumu_reference.png").convert("RGB")
    return {
        "mochi_head": cut_ellipse(mochi, (82, 150, 800, 675), 10),
        "mochi_body": cut_ellipse(mochi, (190, 545, 700, 1098), 10),
        "mochi_arm_l": cut_ellipse(mochi, (150, 620, 338, 940), 8),
        "mochi_arm_r": cut_ellipse(mochi, (575, 430, 870, 785), 8),
        "mochi_leg_l": cut_ellipse(mochi, (342, 870, 478, 1160), 7),
        "mochi_leg_r": cut_ellipse(mochi, (480, 870, 615, 1160), 7),
        "mochi_star": cut_ellipse(mochi, (390, 660, 555, 825), 4),
        "zumu_body": cut_ellipse(zumu, (185, 305, 760, 840), 10),
        "zumu_tail": cut_ellipse(zumu, (100, 555, 470, 860), 8),
        "zumu_arm_l": cut_ellipse(zumu, (190, 555, 360, 760), 8),
        "zumu_arm_r": cut_ellipse(zumu, (675, 555, 820, 760), 8),
    }


def paste_part(canvas: Image.Image, part: Image.Image, pivot_local, pos, angle=0, scale=1.0):
    w, h = part.size
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    img = part.resize((nw, nh), Image.Resampling.LANCZOS)
    px, py = pivot_local[0] * scale, pivot_local[1] * scale
    pad = int(max(nw, nh) * .85)
    stage = Image.new("RGBA", (nw + pad * 2, nh + pad * 2), (0, 0, 0, 0))
    stage.alpha_composite(img, (pad, pad))
    center = (pad + px, pad + py)
    rotated = stage.rotate(math.degrees(angle), center=center, resample=Image.Resampling.BICUBIC, expand=True)
    # PIL changes canvas bounds when expand=True, so use the original pivot offset approximation.
    ox = pos[0] - rotated.width / 2 + (rotated.width / 2 - center[0])
    oy = pos[1] - rotated.height / 2 + (rotated.height / 2 - center[1])
    canvas.alpha_composite(rotated, (int(ox), int(oy)))


def draw_bg(t):
    bg = Image.open(ROOT / "assets" / "pilot_ep001" / "ep001_01_establishing.png").convert("RGB")
    iw, ih = bg.size
    base = max(W / iw, H / ih) * 1.03
    bg = bg.resize((int(iw * base), int(ih * base)), Image.Resampling.LANCZOS)
    frame = Image.new("RGBA", (W, H), (7, 9, 18, 255))
    frame.paste(bg, (int((W - bg.width) / 2), int((H - bg.height) / 2)))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 60))
    frame.alpha_composite(shade)
    return frame


def star_points(cx, cy, r1, r2, rot=0):
    pts = []
    for i in range(10):
        r = r1 if i % 2 == 0 else r2
        a = -math.pi / 2 + rot + i * math.pi / 5
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def draw_soft_fx(frame, t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(46):
        x = (i * 139 + t * (10 + i % 5)) % W
        y = 80 + ((i * 83 + math.sin(t + i) * 20) % 430)
        alpha = int(40 + 70 * math.sin(t * 1.4 + i) ** 2)
        d.polygon(star_points(x, y, 5 + i % 3, 2, i), fill=(255, 229, 135, alpha))
    frame.alpha_composite(layer.filter(ImageFilter.GaussianBlur(.6)))


def draw_mochi(frame, parts, t, x, y):
    breathe = math.sin(t * math.tau * .7)
    sad = ease((t - 13) / 8) * (1 - ease((t - 24) / 5))
    wave = math.sin(t * math.tau * 1.2)

    body_pos = (x, y + breathe * 3 + sad * 12)
    head_pos = (x, y - 116 + breathe * 1.5 + sad * 10)
    head_rot = math.radians(math.sin(t * 1.1) * 2 - sad * 8)

    # Back limbs, attached under body, no floating gap.
    paste_part(frame, parts["mochi_leg_l"], (68, 30), (x - 42, y + 128), math.radians(4 + wave * 4), .54)
    paste_part(frame, parts["mochi_leg_r"], (66, 30), (x + 42, y + 128), math.radians(-4 - wave * 4), .54)
    paste_part(frame, parts["mochi_arm_l"], (95, 42), (x - 92, y - 8), math.radians(20 + sad * 8), .58)
    paste_part(frame, parts["mochi_arm_r"], (72, 55), (x + 88, y - 35), math.radians(-24 + math.sin(t * 2) * 7), .52)

    paste_part(frame, parts["mochi_body"], (255, 125), body_pos, 0, .55 + breathe * .006)
    paste_part(frame, parts["mochi_star"], (82, 82), (x, y - 12), 0, .55 + breathe * .04)
    paste_part(frame, parts["mochi_head"], (360, 350), head_pos, head_rot, .50)

    # Tiny expression overlay so the face has life without destroying the image.
    d = ImageDraw.Draw(frame)
    if sad > .25:
        d.arc((x - 26, y - 118, x + 26, y - 80), 205, 335, fill=(75, 40, 36, 190), width=4)
    if math.sin(t * math.tau * .4) > .965:
        d.line((x - 54, y - 156, x - 24, y - 154), fill=(75, 40, 36, 170), width=4)
        d.line((x + 24, y - 154, x + 54, y - 156), fill=(75, 40, 36, 170), width=4)


def draw_zumu(frame, parts, t, x, y):
    bob = math.sin(t * math.tau * .85)
    tail = math.sin(t * math.tau * 1.1)
    paste_part(frame, parts["zumu_tail"], (310, 130), (x - 75 + tail * 6, y + 24 + bob * 4), math.radians(8 + tail * 5), .42)
    paste_part(frame, parts["zumu_arm_l"], (110, 60), (x - 58, y + 10), math.radians(16 + tail * 7), .40)
    paste_part(frame, parts["zumu_arm_r"], (30, 60), (x + 57, y + 10), math.radians(-16 - tail * 7), .40)
    paste_part(frame, parts["zumu_body"], (285, 260), (x, y + bob * 7), math.radians(tail * 3), .32)


def frame(t, parts):
    img = draw_bg(t)
    enter = ease(t / 8)
    mochi_x = 385 + ease(min(1, t / 9)) * 110
    draw_zumu(img, parts, t, 930 - enter * 220, 320 + math.sin(t * 2.4) * 12)
    draw_mochi(img, parts, t, mochi_x, 475)
    draw_soft_fx(img, t)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((22, 22, 470, 66), radius=18, fill=(0, 0, 0, 140), outline=(255, 216, 111, 170), width=2)
    d.text((42, 32), "VISUAL PAPER RIG TEST - real design parts", font=FONT, fill=(255, 247, 232, 255))
    d.rounded_rectangle((22, H - 28, W - 22, H - 18), radius=6, fill=(255, 255, 255, 42))
    d.rounded_rectangle((22, H - 28, 22 + (W - 44) * (t / DURATION), H - 18), radius=6, fill=(255, 216, 111, 220))
    return np.asarray(img.convert("RGB"))


def main():
    parts = build_assets()
    writer = imageio.get_writer(
        OUT,
        fps=FPS,
        codec="libx264",
        quality=8,
        macro_block_size=16,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    total = int(DURATION * FPS)
    try:
        for i in range(total):
            t = i / FPS
            writer.append_data(frame(t, parts))
            if i % (FPS * 8) == 0:
                print(f"paper rig {int(t)}s / {DURATION}s", flush=True)
    finally:
        writer.close()
    imageio.imwrite(THUMB, frame(14, parts))
    print(OUT)


if __name__ == "__main__":
    main()
