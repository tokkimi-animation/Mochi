from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "rig_tests"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "ep001_rig_blocking.mp4"
THUMB = OUT_DIR / "ep001_rig_blocking_thumb.png"

W, H = 1280, 720
SCALE = 2
FPS = 24
DURATION = 32


def font(size: int):
    for path in ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


FONT = font(26)
SMALL = font(18)


def ease(x: float) -> float:
    x = max(0, min(1, x))
    return x * x * (3 - 2 * x)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


@dataclass
class Bone:
    name: str
    parent: str | None
    x: float
    y: float
    length: float = 0
    rot: float = 0
    sx: float = 1
    sy: float = 1
    wx: float = 0
    wy: float = 0
    wrot: float = 0
    children: list[str] = field(default_factory=list)


class Rig:
    def __init__(self, data: dict):
        self.bones = {b["name"]: Bone(**b) for b in data["bones"]}
        for b in self.bones.values():
            if b.parent:
                self.bones[b.parent].children.append(b.name)

    def pose(self, t: float, root_x: float, root_y: float, root_rot: float = 0) -> None:
        root = self.bones["root"]
        root.x = root_x
        root.y = root_y
        root.rot = root_rot
        self._world("root", 0, 0, 0)

    def _world(self, name: str, px: float, py: float, prot: float) -> None:
        b = self.bones[name]
        if b.parent is None:
            b.wx, b.wy, b.wrot = b.x, b.y, b.rot
        else:
            cr, sr = math.cos(prot), math.sin(prot)
            b.wx = px + b.x * cr - b.y * sr
            b.wy = py + b.x * sr + b.y * cr
            b.wrot = prot + b.rot
        for child in b.children:
            self._world(child, b.wx, b.wy, b.wrot)


def load_rig(name: str) -> Rig:
    return Rig(json.loads((ROOT / "assets" / "rigs" / name).read_text(encoding="utf-8")))


def star_points(cx, cy, r1, r2, rot=0):
    pts = []
    for i in range(10):
        r = r1 if i % 2 == 0 else r2
        a = -math.pi / 2 + rot + i * math.pi / 5
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def plush_ellipse(layer, x, y, rx, ry, color1, color2, rot=0, alpha=255):
    pad = int(max(rx, ry) * 1.45)
    box = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(box)
    for i in range(pad, 0, -2):
        k = i / pad
        c = tuple(int(color1[j] * k + color2[j] * (1 - k)) for j in range(3)) + (alpha,)
        d.ellipse((pad - rx * k, pad - ry * k, pad + rx * k, pad + ry * k), fill=c)
    noise = Image.effect_noise((pad * 2, pad * 2), 42).convert("L")
    noise = noise.point(lambda v: int(max(0, min(70, v * .18))))
    texture = Image.new("RGBA", (pad * 2, pad * 2), (255, 255, 255, 0))
    texture.putalpha(noise)
    box.alpha_composite(texture)
    box = box.rotate(math.degrees(rot), resample=Image.Resampling.BICUBIC, expand=True)
    layer.alpha_composite(box, (int(x - box.width / 2), int(y - box.height / 2)))


def draw_line_limb(layer, a, b, width, color):
    d = ImageDraw.Draw(layer)
    d.line((a[0], a[1], b[0], b[1]), fill=color, width=width, joint="curve")
    plush_ellipse(layer, b[0], b[1], width * .52, width * .44, (255, 252, 240), (224, 206, 169), 0)


def bone_point(rig: Rig, name: str, dist: float = 0):
    b = rig.bones[name]
    return (b.wx + math.cos(b.wrot) * dist, b.wy + math.sin(b.wrot) * dist)


def animate_mochi(rig: Rig, t: float):
    run = max(0, min(1, (t - 8) / 7)) * (1 - max(0, min(1, (t - 16) / 3)))
    sad = ease(max(0, min(1, (t - 18) / 5))) * (1 - ease(max(0, min(1, (t - 27) / 4))))
    reach = ease(max(0, min(1, (t - 4) / 4))) * (1 - ease(max(0, min(1, (t - 14) / 4))))
    breathe = math.sin(t * math.tau * .55)
    root_x = lerp(360, 520, ease(max(0, min(1, t / 8)))) + math.sin(t * 5) * 10 * run
    root_y = 498 + breathe * 2 - abs(math.sin(t * math.tau * 1.8)) * 12 * run + sad * 18
    rig.bones["body"].rot = math.radians(math.sin(t * 1.7) * 1.5 - sad * 5)
    rig.bones["body"].sy = 1 + breathe * .025
    rig.bones["head"].rot = math.radians(math.sin(t * 1.2) * 3 - sad * 14)
    rig.bones["horn_left"].rot = math.radians(-22 + breathe * 2 + sad * 4)
    rig.bones["horn_right"].rot = math.radians(22 - breathe * 2 - sad * 4)
    rig.bones["arm_left_upper"].rot = math.radians(-135 + reach * -22 + sad * 24)
    rig.bones["arm_left_lower"].rot = math.radians(38 + reach * -38)
    rig.bones["arm_right_upper"].rot = math.radians(-40 + reach * 58 + math.sin(t * 7) * 9 * run)
    rig.bones["arm_right_lower"].rot = math.radians(30 - reach * 58)
    rig.bones["leg_left"].rot = math.radians(88 + math.sin(t * 9) * 22 * run)
    rig.bones["leg_right"].rot = math.radians(92 - math.sin(t * 9) * 22 * run)
    rig.pose(t, root_x, root_y)
    return sad, reach, run


def animate_zumu(rig: Rig, t: float):
    enter = ease(max(0, min(1, (t - 2) / 10)))
    slow = ease(max(0, min(1, (t - 18) / 6)))
    x = lerp(1040, 755, enter) + math.sin(t * 2.8) * (22 - slow * 15)
    y = 310 + math.sin(t * 3.6) * 20 + slow * 36
    rig.bones["body"].rot = math.radians(math.sin(t * 3.5) * 5 * (1 - slow))
    rig.bones["stub_arm_left"].rot = math.radians(150 + math.sin(t * 5) * 12)
    rig.bones["stub_arm_right"].rot = math.radians(30 + math.sin(t * 5 + 1) * 12)
    rig.bones["tail_01"].rot = math.radians(170 + math.sin(t * 3.0) * 10)
    rig.bones["tail_02"].rot = math.radians(math.sin(t * 3.0 - .6) * 14)
    rig.bones["tail_03"].rot = math.radians(math.sin(t * 3.0 - 1.2) * 18)
    rig.pose(t, x, y)
    return slow


def draw_mochi(layer, rig: Rig, sad: float, debug: bool):
    # Back limbs
    for side in ["left", "right"]:
        p = bone_point(rig, f"leg_{side}", 0)
        q = bone_point(rig, f"leg_{side}", 56)
        draw_line_limb(layer, p, q, 38, (244, 228, 194, 255))

    for side in ["left", "right"]:
        p = bone_point(rig, f"arm_{side}_upper", 0)
        mid = bone_point(rig, f"arm_{side}_upper", 52)
        low = rig.bones[f"arm_{side}_lower"]
        low.wx, low.wy = mid
        q = (mid[0] + math.cos(low.wrot) * 44, mid[1] + math.sin(low.wrot) * 44)
        draw_line_limb(layer, p, mid, 34, (250, 237, 209, 255))
        draw_line_limb(layer, mid, q, 32, (250, 237, 209, 255))

    body = rig.bones["body"]
    plush_ellipse(layer, body.wx, body.wy - 40, 88, 122, (255, 253, 243), (228, 211, 178), body.wrot)
    star = rig.bones["belly_star"]
    d = ImageDraw.Draw(layer)
    d.polygon(star_points(star.wx, star.wy - 55, 28, 13, 0), fill=(255, 218, 82, int(210 - sad * 80)))

    head = rig.bones["head"]
    for name, flip in [("horn_left", -1), ("horn_right", 1)]:
        h = rig.bones[name]
        d.pieslice((h.wx - 34, h.wy - 42, h.wx + 34, h.wy + 42), 205 if flip < 0 else -25, 30 if flip < 0 else 210, fill=(246, 220, 139, 255))
    plush_ellipse(layer, head.wx, head.wy, 118, 96, (255, 253, 244), (232, 214, 180), head.wrot)

    d = ImageDraw.Draw(layer)
    for eye in ["eye_left", "eye_right"]:
        e = rig.bones[eye]
        d.ellipse((e.wx - 17, e.wy - 23, e.wx + 17, e.wy + 23), fill=(96, 48, 18, 255))
        d.ellipse((e.wx - 9, e.wy - 15, e.wx + 12, e.wy + 17), fill=(176, 93, 28, 255))
        d.ellipse((e.wx - 8, e.wy - 15, e.wx + 1, e.wy - 6), fill=(255, 255, 255, 240))
    for cheek in ["cheek_left", "cheek_right"]:
        c = rig.bones[cheek]
        d.ellipse((c.wx - 20, c.wy - 12, c.wx + 20, c.wy + 12), fill=(255, 138, 160, 120))
    m = rig.bones["mouth"]
    if sad > .25:
        d.arc((m.wx - 22, m.wy - 2, m.wx + 22, m.wy + 34), 205, 335, fill=(96, 52, 42, 255), width=5)
    else:
        d.arc((m.wx - 24, m.wy - 24, m.wx + 24, m.wy + 18), 30, 150, fill=(96, 52, 42, 255), width=5)
    for brow in ["brow_left", "brow_right"]:
        b = rig.bones[brow]
        angle = -sad * 12 if brow.endswith("left") else sad * 12
        d.line((b.wx - 17, b.wy + angle, b.wx + 17, b.wy - angle), fill=(94, 60, 45, 210), width=5)
    if debug:
        draw_bones(layer, rig, (255, 80, 140, 230))


def draw_zumu(layer, rig: Rig, slow: float, debug: bool):
    d = ImageDraw.Draw(layer)
    # Tail chain
    tail_points = [bone_point(rig, "body"), bone_point(rig, "tail_01", 84), bone_point(rig, "tail_02", 84), bone_point(rig, "tail_03", 84)]
    for i in range(len(tail_points) - 1, 0, -1):
        d.line((tail_points[i - 1], tail_points[i]), fill=(125, 225, 255, int(120 - i * 18)), width=50 - i * 8)
    for i, p in enumerate(tail_points[1:]):
        d.polygon(star_points(p[0], p[1], 10 - i, 4, i), fill=(255, 238, 130, 150))

    b = rig.bones["body"]
    plush_ellipse(layer, b.wx, b.wy, 74, 68, (152, 244, 255), (60, 177, 216), b.wrot)
    for arm in ["stub_arm_left", "stub_arm_right"]:
        p = bone_point(rig, arm, 0)
        q = bone_point(rig, arm, 32)
        draw_line_limb(layer, p, q, 26, (98, 197, 228, 255))
    d = ImageDraw.Draw(layer)
    d.polygon(star_points(rig.bones["star_mark"].wx, rig.bones["star_mark"].wy, 14, 6), fill=(255, 220, 80, 230))
    for eye in ["eye_left", "eye_right"]:
        e = rig.bones[eye]
        d.ellipse((e.wx - 14, e.wy - 18, e.wx + 14, e.wy + 18), fill=(120, 54, 16, 255))
        d.ellipse((e.wx - 7, e.wy - 12, e.wx + 11, e.wy + 14), fill=(220, 129, 33, 255))
        d.ellipse((e.wx - 6, e.wy - 12, e.wx + 2, e.wy - 5), fill=(255, 255, 255, 245))
    m = rig.bones["mouth"]
    d.ellipse((m.wx - 13, m.wy - 10, m.wx + 13, m.wy + 10 + slow * 4), fill=(90, 38, 52, 245))
    for cheek in ["cheek_left", "cheek_right"]:
        c = rig.bones[cheek]
        d.ellipse((c.wx - 16, c.wy - 9, c.wx + 16, c.wy + 9), fill=(255, 132, 160, 110))
    if debug:
        draw_bones(layer, rig, (90, 220, 255, 230))


def draw_bones(layer, rig: Rig, color):
    d = ImageDraw.Draw(layer)
    for b in rig.bones.values():
        if b.parent:
            p = rig.bones[b.parent]
            d.line((p.wx, p.wy, b.wx, b.wy), fill=color, width=3)
        d.ellipse((b.wx - 5, b.wy - 5, b.wx + 5, b.wy + 5), fill=color)
        d.text((b.wx + 7, b.wy - 7), b.name, font=SMALL, fill=color)


def background(t: float):
    img = Image.new("RGBA", (W * SCALE, H * SCALE), (7, 9, 18, 255))
    d = ImageDraw.Draw(img)
    for y in range(H * SCALE):
        k = y / (H * SCALE)
        c = (int(13 + 22 * (1 - k)), int(18 + 18 * (1 - k)), int(34 + 42 * (1 - k)), 255)
        d.line((0, y, W * SCALE, y), fill=c)
    # Convenience store block
    d.rounded_rectangle((120*SCALE, 86*SCALE, 1160*SCALE, 560*SCALE), radius=18*SCALE, fill=(30, 39, 54, 255), outline=(220, 245, 255, 80), width=3*SCALE)
    d.rounded_rectangle((170*SCALE, 118*SCALE, 1110*SCALE, 182*SCALE), radius=10*SCALE, fill=(60, 160, 104, 255))
    d.rectangle((170*SCALE, 166*SCALE, 1110*SCALE, 182*SCALE), fill=(238, 126, 49, 255))
    d.text((430*SCALE, 126*SCALE), "STAR CONVENIENCE", font=font(40*SCALE), fill=(255, 232, 158, 255))
    d.rectangle((180*SCALE, 230*SCALE, 1100*SCALE, 552*SCALE), fill=(175, 225, 255, 32), outline=(230, 250, 255, 90), width=3*SCALE)
    d.rectangle((0, 560*SCALE, W*SCALE, H*SCALE), fill=(28, 32, 42, 255))
    for i in range(20):
        x = (i * 91 + 80) * SCALE
        y = (90 + (i * 47) % 300) * SCALE
        d.ellipse((x-2*SCALE, y-2*SCALE, x+2*SCALE, y+2*SCALE), fill=(255, 235, 150, 130))
    return img.resize((W, H), Image.Resampling.LANCZOS)


def frame(t: float):
    debug = t < 5 or 15 < t < 19
    mochi = load_rig("mochi_rig.json")
    zumu = load_rig("zumu_rig.json")
    sad, reach, run = animate_mochi(mochi, t)
    slow = animate_zumu(zumu, t)
    img = background(t)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_zumu(layer, zumu, slow, debug)
    draw_mochi(layer, mochi, sad, debug)
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    if debug:
        d.rounded_rectangle((24, 24, 480, 72), radius=18, fill=(0, 0, 0, 150), outline=(255, 216, 111, 180), width=2)
        d.text((44, 35), "RIG BLOCKING: bones + fixed pivots visible", font=FONT, fill=(255, 246, 220, 255))
    else:
        d.rounded_rectangle((24, 24, 380, 72), radius=18, fill=(0, 0, 0, 120), outline=(255, 255, 255, 60), width=2)
        d.text((44, 35), "RIGGED CHARACTER TEST", font=FONT, fill=(255, 246, 220, 255))
    bar_w = int((W - 48) * (t / DURATION))
    d.rounded_rectangle((24, H - 28, W - 24, H - 18), radius=6, fill=(255, 255, 255, 42))
    d.rounded_rectangle((24, H - 28, 24 + bar_w, H - 18), radius=6, fill=(255, 216, 111, 220))
    return np.asarray(img.convert("RGB"))


def main():
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
            writer.append_data(frame(t))
            if i % (FPS * 8) == 0:
                print(f"rig render {int(t)}s / {DURATION}s", flush=True)
    finally:
        writer.close()
    imageio.imwrite(THUMB, frame(16))
    print(OUT)


if __name__ == "__main__":
    main()
