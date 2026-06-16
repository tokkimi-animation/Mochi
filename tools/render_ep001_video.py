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

VOICE_EVENTS = [
    (2.6, "line_01_mochi.wav"),
    (24.0, "line_02_zumu.wav"),
    (61.0, "line_03_mochi.wav"),
    (91.0, "line_04_mochi.wav"),
    (144.0, "line_05_zumu.wav"),
    (164.0, "line_06_mochi.wav"),
    (176.0, "line_07_mochi.wav"),
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
    cam = [
        (1.03 + .11 * ep, -52 + 110 * ep, 6 - 34 * ep),
        (1.10 + .04 * math.sin(p * math.pi), 34 - 92 * ep, -18),
        (1.13, -74 + 154 * ep, 8 + math.sin(t * 3.0) * 4),
        (1.06 + .12 * ep, 10, -8 + 30 * ep),
        (1.07 + .08 * ep, -58 + 102 * ep, -14),
        (1.18 + .03 * ep, 6, -34),
    ][scene_idx]
    frame = cover(imgs[img_name], cam[0], cam[1], cam[2]).convert("RGBA")

    # Slight breathing/living light grade.
    color = ImageEnhance.Color(frame).enhance(1.05)
    contrast = ImageEnhance.Contrast(color).enhance(1.03)
    frame = contrast
    frame.alpha_composite(glow_layer(t, scene_idx, p))
    frame.alpha_composite(subtitle_layer(sub))
    frame.alpha_composite(badge_layer(t, scene_idx))
    return np.asarray(frame.convert("RGB"))


def read_wav(path: Path, sr: int) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        frames = w.readframes(w.getnframes())
        data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        if w.getnchannels() == 2:
            data = data.reshape(-1, 2).mean(axis=1)
        source_sr = w.getframerate()
    if source_sr != sr:
        x_old = np.linspace(0, 1, len(data), endpoint=False)
        x_new = np.linspace(0, 1, int(len(data) * sr / source_sr), endpoint=False)
        data = np.interp(x_new, x_old, data).astype(np.float32)
    return data


def build_audio() -> None:
    sr = 44100
    samples = np.zeros(int(DURATION * sr), dtype=np.float32)

    # Soft ambient bed.
    t = np.arange(samples.size) / sr
    samples += 0.015 * np.sin(2 * np.pi * 220 * t)
    samples += 0.009 * np.sin(2 * np.pi * 330 * t + .6)

    # Door, steps, star tones.
    for sec, freq, dur, amp in [
        (22, 660, .18, .08), (22.22, 980, .18, .05),
        (50, 115, .08, .08), (51.1, 135, .08, .07),
        (126, 740, .18, .05), (128, 880, .18, .05),
        (155, 1040, .5, .05), (176, 1320, .35, .04),
    ]:
        start = int(sec * sr)
        n = int(dur * sr)
        env = np.linspace(1, 0.001, n)
        tone = amp * np.sin(2 * np.pi * freq * np.arange(n) / sr) * env
        samples[start:start + n] += tone[: max(0, min(n, samples.size - start))]

    for sec, filename in VOICE_EVENTS:
        path = TTS / filename
        if not path.exists():
            continue
        data = read_wav(path, sr) * .9
        start = int(sec * sr)
        end = min(samples.size, start + data.size)
        samples[start:end] += data[: end - start]

    samples = np.clip(samples, -1, 1)
    with wave.open(str(TMP_AUDIO), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((samples * 32767).astype(np.int16).tobytes())


def mux_video_audio() -> None:
    import imageio_ffmpeg
    import subprocess

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, "-y",
        "-i", str(TMP_VIDEO),
        "-i", str(TMP_AUDIO),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "160k",
        "-shortest",
        str(OUT),
    ]
    subprocess.run(cmd, check=True)


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
    build_audio()
    mux_video_audio()
    print(OUT)


if __name__ == "__main__":
    main()
