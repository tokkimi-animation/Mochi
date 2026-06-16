from __future__ import annotations

import csv
import math
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "ep001_phrase_sheets_36"
POSES = EXPORT / "poses_360"
FRAMES = EXPORT / "frames_1800"
FPS = 10
SECONDS = 180
TOTAL = FPS * SECONDS
WIDTH = 1280
HEIGHT = 720


DIALOGUE = [
    (1.0, 4.0, "Mochi"), (4.4, 7.2, "Zumu"), (8.0, 11.0, "Mochi"), (11.5, 14.8, "Zumu"),
    (16.4, 19.6, "Mochi"), (20.0, 23.0, "Zumu"), (24.2, 27.2, "Mochi"), (27.6, 31.2, "Zumu"),
    (33.0, 36.2, "Mochi"), (36.6, 40.2, "Zumu"), (42.0, 45.4, "Mochi"), (45.8, 49.2, "Zumu"),
    (52.4, 55.2, "Mochi"), (55.6, 59.4, "Zumu"), (62.0, 65.4, "Mochi"), (65.8, 69.4, "Zumu"),
    (72.0, 75.0, "Mochi"), (75.4, 79.2, "Zumu"), (82.0, 85.4, "Mochi"), (85.8, 89.8, "Zumu"),
    (93.0, 96.0, "Mochi"), (96.4, 100.6, "Zumu"), (103.0, 106.4, "Mochi"), (106.8, 110.6, "Zumu"),
    (113.0, 116.4, "Mochi"), (116.8, 120.4, "Zumu"), (123.0, 126.6, "Mochi"), (127.0, 130.6, "Zumu"),
    (133.0, 136.4, "Mochi"), (136.8, 141.0, "Zumu"), (144.4, 147.8, "Mochi"), (148.2, 152.4, "Zumu"),
    (156.2, 159.8, "Mochi"), (160.2, 164.0, "Zumu"), (168.4, 172.0, "Mochi"), (172.4, 176.0, "Zumu"),
]


PHRASE_WINDOWS = []
for i in range(36):
    start = DIALOGUE[i][0]
    end = DIALOGUE[i + 1][0] if i < 35 else 180.0
    PHRASE_WINDOWS.append((start, end, DIALOGUE[i][2]))


def phrase_for(sec: float) -> tuple[int, float, str]:
    if sec < PHRASE_WINDOWS[0][0]:
        return 1, 0.0, "Mochi"
    for idx, (start, end, speaker) in enumerate(PHRASE_WINDOWS, 1):
        if start <= sec < end:
            return idx, (sec - start) / max(0.001, end - start), speaker
    return 36, 1.0, "Zumu"


def glow(size: int, color: tuple[int, int, int], alpha: int) -> Image.Image:
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.ellipse((size * 0.25, size * 0.25, size * 0.75, size * 0.75), fill=(*color, alpha))
    return layer.filter(ImageFilter.GaussianBlur(size * 0.12))


def add_glow(layer: Image.Image, x: float, y: float, radius: int, color: tuple[int, int, int], alpha: int) -> None:
    g = glow(radius * 2, color, alpha)
    layer.alpha_composite(g, (int(x - radius), int(y - radius)))


def add_life(frame: Image.Image, sec: float, phrase: int, local: float, speaker: str) -> Image.Image:
    rgba = frame.convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay, "RGBA")
    pulse = 0.5 + 0.5 * math.sin(sec * 5.0)
    d.rectangle((0, 0, WIDTH, HEIGHT), fill=(255, 218, 150, int(7 + 8 * pulse)))

    if speaker == "Mochi" or phrase in {13, 15, 17, 23, 27, 35}:
        cx, cy = WIDTH * 0.36, HEIGHT * 0.55
        add_glow(overlay, cx, cy, int(72 + pulse * 16), (255, 226, 120), 56)
        count = 14 if phrase in {13, 15, 17, 27, 35} else 8
        for i in range(count):
            a = sec * 1.8 + i * 0.72
            add_glow(overlay, cx + math.cos(a) * (74 + i % 4 * 12), cy - 82 + math.sin(a * 1.1) * (40 + i % 3 * 7), 8 + i % 3 * 2, (255, 232, 135), 92)

    if speaker == "Zumu" or phrase in {18, 20, 22, 30, 32, 36}:
        cx, cy = WIDTH * 0.64, HEIGHT * 0.42
        add_glow(overlay, cx, cy, int(88 + pulse * 18), (90, 205, 255), 48)
        for i in range(8):
            add_glow(overlay, cx - i * 46 - local * 32, cy + math.sin(sec + i) * 16, 9, (110, 222, 255), 72)

    if phrase in {9, 10, 18, 20, 21, 22, 24, 29, 30, 31, 32, 33, 36}:
        for i in range(18):
            x = WIDTH * (0.12 + ((i * 0.131 + local * 0.35) % 0.76))
            y = HEIGHT * (0.16 + ((i * 0.181 + local * 0.22) % 0.60))
            add_glow(overlay, x, y, 7 + (i % 4) * 2, (255, 226, 112), 76)

    if phrase in {1, 2, 23, 24, 32, 33, 34, 35, 36}:
        rng = np.random.default_rng(int(sec * 100) + phrase)
        for _ in range(20):
            x = int(rng.integers(-60, WIDTH + 60))
            y = int(rng.integers(0, HEIGHT))
            d.line((x, y, x + 7, y + 20), fill=(190, 220, 255, 24), width=1)

    for i in range(6):
        y = HEIGHT - 145 + i * 20 + math.sin(sec * 3 + i) * 2
        d.line((0, y, WIDTH, y), fill=(255, 224, 135, 8), width=1)

    out = Image.alpha_composite(rgba, overlay).convert("RGB")
    out = ImageEnhance.Color(out).enhance(1.035)
    return ImageEnhance.Contrast(out).enhance(1.025)


def make_sfx() -> Path:
    sr = 44100
    n = sr * SECONDS
    t = np.linspace(0, SECONDS, n, endpoint=False)
    rng = np.random.default_rng(99)
    audio = rng.normal(0, 0.002, n).astype(np.float32)
    audio += 0.004 * np.sin(2 * np.pi * 196 * t) + 0.003 * np.sin(2 * np.pi * 294 * t)

    def tone(start: float, freq: float, dur: float, vol: float) -> None:
        s = int(start * sr)
        e = min(n, s + int(dur * sr))
        tt = np.linspace(0, dur, e - s, endpoint=False)
        env = np.sin(np.linspace(0, math.pi, e - s)) ** 2
        audio[s:e] += vol * np.sin(2 * np.pi * freq * tt) * env

    def step(start: float) -> None:
        s = int(start * sr)
        e = min(n, s + int(0.12 * sr))
        tt = np.linspace(0, 0.12, e - s, endpoint=False)
        audio[s:e] += 0.028 * np.sin(2 * np.pi * 86 * tt) * np.exp(-tt * 30)

    for i, (start, _, speaker) in enumerate(DIALOGUE, 1):
        if speaker == "Mochi":
            step(start + 0.25)
        tone(start + 0.12, 620 if speaker == "Mochi" else 740, 0.22, 0.010)
    out = EXPORT / "ep001_final_lights_sfx.wav"
    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes((np.clip(audio, -0.75, 0.75) * 32767).astype("<i2").tobytes())
    return out


def render_frames() -> None:
    FRAMES.mkdir(parents=True, exist_ok=True)
    for old in FRAMES.glob("*.jpg"):
        old.unlink()
    pose_cache = {p.name: Image.open(p).convert("RGB") for p in POSES.glob("*.jpg")}
    with (EXPORT / "final_frame_manifest_10fps.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "time", "phrase", "pose_a", "pose_b", "speaker"])
        for idx in range(TOTAL):
            sec = idx / FPS
            phrase, local, speaker = phrase_for(sec)
            pose_float = min(8.999, max(0.0, local * 9.0))
            pose_i = int(math.floor(pose_float)) + 1
            blend = pose_float - (pose_i - 1)
            a_name = f"phrase_{phrase:02d}_pose_{pose_i:02d}.jpg"
            b_name = f"phrase_{phrase:02d}_pose_{min(10, pose_i + 1):02d}.jpg"
            frame = Image.blend(pose_cache[a_name], pose_cache[b_name], blend)
            frame = add_life(frame, sec, phrase, local, speaker)
            frame.save(FRAMES / f"frame_{idx + 1:06d}.jpg", quality=91, optimize=True, progressive=True)
            writer.writerow([idx + 1, f"{sec:06.1f}", phrase, a_name, b_name, speaker])
            if (idx + 1) % 100 == 0:
                print(f"frames {idx + 1}/{TOTAL}")


def render_video(audio: Path) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    voice = ROOT / "exports" / "ep001_production_clean_10fps" / "ep001_clean_audio_mix.m4a"
    out = EXPORT / "ep001_36phrases_frame_by_frame_10fps.mp4"
    cmd = [
        ffmpeg, "-y", "-framerate", str(FPS), "-i", str(FRAMES / "frame_%06d.jpg"),
        "-i", str(voice), "-i", str(audio),
        "-filter_complex", "[1:a]volume=0.90[v];[2:a]volume=0.45[s];[v][s]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.92[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "144k", "-shortest", str(out)
    ]
    subprocess.run(cmd, check=True)
    return out


def write_html(video: Path) -> None:
    grid = "\n".join(
        f'<a href="exports/ep001_phrase_sheets_36/source_sheets/phrase_{i:02d}.png"><img src="exports/ep001_phrase_sheets_36/source_sheets/phrase_{i:02d}.png"></a>'
        for i in range(1, 37)
    )
    (ROOT / "ep001_36phrases_frame_by_frame.html").write_text(
        f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EP001 36 phrases frame by frame</title><style>
body{{margin:0;background:#10131b;color:#fff7dc;font-family:Arial,sans-serif}}main{{max-width:1200px;margin:auto;padding:28px}}video{{width:100%;border-radius:8px;background:#000}}.links{{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 26px}}.links a{{background:#ffe28a;color:#171717;padding:10px 12px;border-radius:6px;text-decoration:none;font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}}img{{width:100%;display:block;border-radius:6px}}p{{color:#d8dded}}</style></head><body><main>
<h1>EP001 - 36 phrases / 360 poses / 1800 frames</h1>
<p>Chaque phrase a sa planche de 10 poses. Aucun texte n'est incrusté dans les images; les sous-titres seront ajoutés en overlay final.</p>
<video src="exports/ep001_phrase_sheets_36/{video.name}" controls preload="metadata"></video>
<div class="links"><a href="exports/ep001_phrase_sheets_36/source_sheets/">36 planches</a><a href="exports/ep001_phrase_sheets_36/poses_360/">360 poses</a><a href="exports/ep001_phrase_sheets_36/frames_1800/">1800 frames</a><a href="exports/ep001_phrase_sheets_36/final_frame_manifest_10fps.csv">Manifest frames</a></div>
<div class="grid">{grid}</div></main></body></html>""",
        encoding="utf-8",
    )


def main() -> None:
    render_frames()
    audio = make_sfx()
    video = render_video(audio)
    write_html(video)
    print(video)


if __name__ == "__main__":
    main()
