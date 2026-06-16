from __future__ import annotations

import math
import wave
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "pilot_ep001"
OUT = ASSETS / "ep001_pilot_preview.mp4"
TMP_VIDEO = ASSETS / "_ep001_video_only.mp4"
TMP_AUDIO = ASSETS / "_ep001_audio.wav"
TTS = ASSETS / "tts"

W, H = 1280, 720
FPS = 24
DURATION = 180.0


SCENES = [
    (0, 22, "ep001_01_establishing.png", "모찌: 잠깐만. 저 별빛이 문 사이에 끼었어."),
    (22, 48, "ep001_02_door_incident.png", "주무: 가자 가자! 내가 빨리 빼낼게!"),
    (48, 82, "ep001_03_chase.png", "모찌: 내가 도와주려던 건데... 왜 더 무서워하지?"),
    (82, 126, "ep001_04_emotional_beat.png", "모찌: 잡는 게 아니라, 기다려 줘야 했어."),
    (126, 162, "ep001_05_resolution.png", "주무: 정답보다 중요한 걸 찾았네."),
    (162, 180, "ep001_05_resolution.png", "모찌: 다음엔 더 늦게, 더 잘 볼래."),
]

def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


FONT_SUB = font(34)
FONT_SMALL = font(20)
FONT_BADGE = font(18)


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def scene_at(t: float):
    for i, (start, end, img, sub) in enumerate(SCENES):
        if start <= t < end:
            p = (t - start) / (end - start)
            return i, start, end, img, sub, p
    i = len(SCENES) - 1
    start, end, img, sub = SCENES[-1]
    return i, start, end, img, sub, 1.0


def cover(im: Image.Image, scale: float, dx: float, dy: float) -> Image.Image:
    iw, ih = im.size
    base = max(W / iw, H / ih) * scale
    nw, nh = int(iw * base), int(ih * base)
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = int((W - nw) / 2 + dx)
    y = int((H - nh) / 2 + dy)
    frame = Image.new("RGB", (W, H), (5, 7, 16))
    frame.paste(resized, (x, y))
    return frame


def paste_living_crop(
    frame: Image.Image,
    source: Image.Image,
    box: tuple[int, int, int, int],
    t: float,
    amp_x: float,
    amp_y: float,
    phase: float = 0,
    scale_amp: float = 0.006,
) -> None:
    """Animate only a soft local character region, leaving the set locked."""
    x1, y1, x2, y2 = box
    crop = source.crop(box).convert("RGBA")
    w, h = crop.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((4, 4, w - 4, h - 4), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(9))
    crop.putalpha(mask)

    breath = math.sin(t * math.tau * .62 + phase)
    sx = 1 + scale_amp * breath
    sy = 1 + scale_amp * 1.35 * breath
    nw, nh = max(1, int(w * sx)), max(1, int(h * sy))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    dx = int(math.sin(t * math.tau * .28 + phase) * amp_x)
    dy = int(math.sin(t * math.tau * .55 + phase) * amp_y)
    px = int(x1 - (nw - w) / 2 + dx)
    py = int(y1 - (nh - h) / 2 + dy)
    frame.alpha_composite(crop, (px, py))


def draw_blink_and_mouth(layer: Image.Image, scene_idx: int, t: float) -> None:
    d = ImageDraw.Draw(layer)
    blink = math.sin(t * math.tau * .38) > .965
    if not blink:
        return
    # Soft eyelid strokes, scene-specific approximate positions.
    coords = {
        0: [((164, 382), (188, 385)), ((218, 365), (244, 362))],
        2: [((330, 360), (362, 360)), ((430, 360), (462, 360))],
        3: [((358, 278), (398, 282)), ((474, 278), (514, 282)), ((755, 332), (785, 335)), ((828, 332), (858, 335))],
        4: [((382, 296), (420, 298)), ((492, 296), (532, 298)), ((728, 316), (754, 318)), ((786, 316), (812, 318))],
        5: [((382, 296), (420, 298)), ((492, 296), (532, 298))]
    }.get(scene_idx, [])
    for a, b in coords:
        d.line((a, b), fill=(70, 38, 32, 170), width=5)


def draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r1: float, r2: float, fill):
    pts = []
    for i in range(10):
        r = r1 if i % 2 == 0 else r2
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    draw.polygon(pts, fill=fill)


def glow_layer(t: float, scene_idx: int, p: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # Star particles
    count = 42 if scene_idx != 3 else 24
    for i in range(count):
        seed = i * 97.13
        x = (seed * 7 + t * (8 + i % 5) + math.sin(t * .7 + i) * 42) % W
        y = 42 + ((seed * 13 + math.cos(t * .42 + i) * 35) % (H - 180))
        alpha = int(50 + 80 * (math.sin(t * 1.6 + i) ** 2))
        draw_star(d, x, y, 6 + (i % 3), 2.5 + (i % 2), (255, 224, 128, alpha))

    # Door scanner / moving light
    if scene_idx in (1, 4):
        scan_x = int(W * (.36 + ((p * 2) % 1) * .22))
        d.rectangle((scan_x, 70, scan_x + 10, H - 80), fill=(130, 235, 255, 55))

    # Breathing belly star hint
    pulse = .5 + .5 * math.sin(t * math.tau * .8)
    if scene_idx in (0, 3, 4, 5):
        gx = int(W * (.18 if scene_idx == 0 else .45))
        gy = int(H * (.56 if scene_idx == 0 else .52))
        d.ellipse((gx - 36, gy - 36, gx + 36, gy + 36), fill=(255, 216, 90, int(24 + 38 * pulse)))

    layer = layer.filter(ImageFilter.GaussianBlur(1.1))
    return layer


def subtitle_layer(text: str) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    box = (105, H - 112, W - 105, H - 38)
    d.rounded_rectangle(box, radius=20, fill=(0, 0, 0, 150), outline=(255, 255, 255, 55), width=1)
    bbox = d.textbbox((0, 0), text, font=FONT_SUB)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((W - tw) / 2, H - 88), text, font=FONT_SUB, fill=(255, 248, 232, 255))
    return layer


def badge_layer(t: float, scene_idx: int) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    label = f"EP001 · SHOT {scene_idx + 1:02d}"
    d.rounded_rectangle((24, 24, 205, 60), radius=18, fill=(5, 8, 18, 145), outline=(255, 255, 255, 55))
    d.text((42, 32), label, font=FONT_BADGE, fill=(255, 247, 232, 255))
    d.rounded_rectangle((W - 214, 24, W - 24, 60), radius=18, fill=(5, 8, 18, 145), outline=(255, 255, 255, 55))
    d.text((W - 192, 32), "파일럿 영상 검수", font=FONT_BADGE, fill=(255, 247, 232, 255))
    d.rounded_rectangle((24, H - 28, W - 24, H - 18), radius=6, fill=(255, 255, 255, 50))
    d.rounded_rectangle((24, H - 28, 24 + (W - 48) * (t / DURATION), H - 18), radius=6, fill=(255, 216, 111, 210))
    return layer


def render_frame(t: float, imgs: dict[str, Image.Image]) -> np.ndarray:
    scene_idx, start, end, img_name, sub, p = scene_at(t)
    ep = ease(p)
    # Almost locked camera. Life comes from characters/effects, not fake global panning.
    cam = [
        (1.055, -18 + 18 * ep, -8),
        (1.08, -10, -12),
        (1.08, 0, 0),
        (1.05, 0, -6),
        (1.055, -8, -10),
        (1.10, 0, -24),
    ][scene_idx]
    base = cover(imgs[img_name], cam[0], cam[1], cam[2]).convert("RGBA")
    frame = base.copy()

    living_boxes = {
        0: [((72, 255, 286, 560), 2.0, 5.0, 0.2)],
        1: [((250, 210, 610, 618), 1.5, 4.0, 0.5), ((690, 205, 1040, 590), 4.0, 7.0, 1.4)],
        2: [((220, 175, 565, 650), 3.0, 8.0, 0.4)],
        3: [((260, 120, 570, 650), 1.5, 4.0, 0.2), ((650, 220, 975, 545), 5.0, 8.0, 1.1)],
        4: [((275, 135, 575, 640), 2.0, 5.0, 0.1), ((640, 210, 945, 560), 5.0, 8.0, 1.0)],
        5: [((275, 135, 575, 640), 1.5, 4.0, 0.1)],
    }
    for box, ax, ay, ph in living_boxes.get(scene_idx, []):
        paste_living_crop(frame, base, box, t, ax, ay, ph)

    # Slight breathing/living light grade.
    color = ImageEnhance.Color(frame).enhance(1.05)
    contrast = ImageEnhance.Contrast(color).enhance(1.03)
    frame = contrast
    frame.alpha_composite(glow_layer(t, scene_idx, p))
    fx = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_blink_and_mouth(fx, scene_idx, t)
    frame.alpha_composite(fx)
    frame.alpha_composite(subtitle_layer(sub))
    frame.alpha_composite(badge_layer(t, scene_idx))
    return np.asarray(frame.convert("RGB"))


def main() -> None:
    imgs = {p.name: Image.open(p).convert("RGB") for p in ASSETS.glob("ep001_*.png")}
    writer = imageio.get_writer(
        TMP_VIDEO,
        fps=FPS,
        codec="libx264",
        quality=8,
        macro_block_size=16,
        ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    try:
        total = int(DURATION * FPS)
        for frame_no in range(total):
            t = frame_no / FPS
            writer.append_data(render_frame(t, imgs))
            if frame_no % (FPS * 15) == 0:
                print(f"render {int(t):03d}s / 180s", flush=True)
    finally:
        writer.close()
    if OUT.exists():
        OUT.unlink()
    TMP_VIDEO.replace(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
