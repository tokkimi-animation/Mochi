from __future__ import annotations

import csv
import math
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "exports" / "ep001_production_clean_10fps" / "keyframes"
EXPORT = ROOT / "exports" / "ep001_phrase_matched_10fps"
KEYS = EXPORT / "phrase_keyframes"
FRAMES = EXPORT / "frames"
FPS = 10
SECONDS = 180
TOTAL = FPS * SECONDS
WIDTH = 1280
HEIGHT = 720


@dataclass(frozen=True)
class Beat:
    idx: int
    start: float
    end: float
    speaker: str
    text: str
    source: str
    focus: str
    emotion: str
    action: str
    zoom: float
    panx: float
    pany: float
    light: str


BEATS = [
    Beat(1, 0.0, 4.4, "Mochi", "여기 봐, 주무. 밤인데 편의점이 별처럼 빛나.", "kf_001_store_wide.png", "mochi", "wonder", "Mochi notices the glowing Korean convenience store sign in the rain.", 1.18, -0.28, 0.04, "mochi"),
    Beat(2, 4.4, 8.0, "Zumu", "와아, 간판에 작은 별이 숨어 있어!", "kf_001_store_wide.png", "sign", "excited", "Cut toward the sign and warm star bulbs above the store.", 1.22, 0.22, -0.24, "stars"),
    Beat(3, 8.0, 11.5, "Mochi", "비 냄새도 나고, 따뜻한 우유 냄새도 나.", "kf_002_store_wide_alt.png", "mochi", "curious", "Mochi sniffs the warm air at the doorway, chest star glowing softly.", 1.24, -0.30, 0.03, "mochi"),
    Beat(4, 11.5, 16.4, "Zumu", "그럼 조심히 들어가 보자. 내 꼬리빛은 약하게 켤게.", "kf_005_door_meeting.png", "zumu", "careful", "Zumu floats closer with a dim blue comet tail.", 1.18, 0.25, -0.02, "zumu"),
    Beat(5, 16.4, 20.0, "Mochi", "잠깐, 문 위에서 뭔가 반짝였어.", "kf_006_door_meeting_alt.png", "sensor", "alert", "Mochi looks up at the automatic door sensor.", 1.26, -0.08, -0.20, "sensor"),
    Beat(6, 20.0, 24.2, "Zumu", "센서야. 그런데 오늘은 별가루를 먹은 것 같아.", "kf_006_door_meeting_alt.png", "zumu", "playful", "Zumu circles the sensor as gold dust flickers.", 1.20, 0.25, -0.04, "zumu"),
    Beat(7, 24.2, 27.6, "Mochi", "문아, 우리를 놀라게 하지 말아 줘.", "kf_006_door_meeting_alt.png", "mochi", "gentle", "Mochi raises a paw toward the door, asking gently.", 1.28, -0.25, 0.12, "mochi"),
    Beat(8, 27.6, 33.0, "Zumu", "괜찮아, 내가 먼저 살짝 날아가 볼게.", "kf_005_door_meeting.png", "zumu", "brave", "Zumu flies forward past the glass door.", 1.16, 0.30, 0.00, "zumu"),
    Beat(9, 33.0, 36.6, "Mochi", "앗! 별조각들이 컵라면 쪽으로 도망가!", "kf_007_star_chase.png", "mochi", "surprised", "Mochi reacts as star pieces bounce toward ramyeon shelves.", 1.25, -0.30, 0.02, "stars"),
    Beat(10, 36.6, 42.0, "Zumu", "잡자! 하지만 진열대는 건드리지 않기!", "kf_007_star_chase.png", "zumu", "leader", "Zumu leads the chase without knocking products down.", 1.20, 0.25, 0.00, "zumu"),
    Beat(11, 42.0, 45.8, "Mochi", "바닥이 미끄러워. 천천히 가야 해.", "kf_007_star_chase.png", "mochi", "careful", "Mochi slows down on the shiny wet floor.", 1.30, -0.30, 0.14, "mochi"),
    Beat(12, 45.8, 52.4, "Zumu", "좋아, 속도 줄일게. 반짝임만 따라와.", "kf_007_star_chase.png", "zumu", "supportive", "Zumu makes a slower blue trail.", 1.16, 0.32, -0.02, "zumu"),
    Beat(13, 52.4, 55.6, "Mochi", "저 작은 별은 왜 떨고 있을까?", "kf_008_emotional_pause.png", "mochi", "worried", "Mochi sees a tiny star trembling near the door.", 1.20, -0.30, 0.02, "mochi"),
    Beat(14, 55.6, 62.0, "Zumu", "너무 밝은 불빛이 무서웠나 봐.", "kf_008_emotional_pause.png", "zumu", "soft", "Zumu lowers his body and tail light, trying not to scare it.", 1.18, 0.25, -0.01, "zumu"),
    Beat(15, 62.0, 65.8, "Mochi", "괜찮아. 우리는 기다릴 수 있어.", "kf_008_emotional_pause.png", "mochi", "comfort", "Mochi breathes gently, small lights gathering around his cheeks and chest.", 1.32, -0.25, 0.10, "mochi_many"),
    Beat(16, 65.8, 72.0, "Zumu", "내 꼬리빛도 작게 만들게. 이렇게.", "kf_005_door_meeting.png", "zumu", "comfort", "Zumu demonstrates a smaller, softer comet tail.", 1.22, 0.26, 0.00, "zumu"),
    Beat(17, 72.0, 75.4, "Mochi", "봐, 조금씩 다시 빛나고 있어.", "kf_008_emotional_pause.png", "mochi", "hope", "The tiny star glows again while Mochi watches softly.", 1.24, -0.22, 0.05, "mochi_many"),
    Beat(18, 75.4, 82.0, "Zumu", "좋아. 이제 별들이 줄을 서면 문을 통과할 수 있어.", "kf_006_door_meeting_alt.png", "zumu", "clever", "Zumu points the star pieces toward the automatic door path.", 1.14, 0.20, -0.02, "zumu"),
    Beat(19, 82.0, 85.8, "Mochi", "문이 열릴 때마다 바람이 살짝 불어.", "kf_006_door_meeting_alt.png", "sensor", "observing", "Mochi notices the air rhythm from the sliding door.", 1.22, -0.12, -0.14, "sensor"),
    Beat(20, 85.8, 93.0, "Zumu", "그 바람을 박자로 쓰자. 하나, 둘, 반짝!", "kf_006_door_meeting_alt.png", "zumu", "rhythm", "Zumu turns the door rhythm into a little game.", 1.16, 0.28, 0.02, "stars"),
    Beat(21, 93.0, 96.4, "Mochi", "작은 별들아, 너무 서두르지 마.", "kf_008_emotional_pause.png", "mochi", "gentle", "Mochi speaks softly to the tiny star pieces.", 1.28, -0.24, 0.07, "mochi_many"),
    Beat(22, 96.4, 103.0, "Zumu", "내 푸른 길 위로 천천히 오면 돼.", "kf_005_door_meeting.png", "zumu", "guide", "Zumu paints a blue glowing path in the air.", 1.18, 0.30, -0.02, "zumu"),
    Beat(23, 103.0, 106.8, "Mochi", "밖은 차갑지만, 여기 빛은 따뜻해.", "kf_001_store_wide.png", "store", "warm", "Cutaway to warm store light and cold rain outside.", 1.10, 0.02, 0.02, "warm"),
    Beat(24, 106.8, 113.0, "Zumu", "그래서 별들이 길을 잃지 않는 거야.", "kf_001_store_wide.png", "sign", "warm", "The sign star reflects on the wet pavement like a guide.", 1.17, 0.24, -0.20, "stars"),
    Beat(25, 113.0, 116.8, "Mochi", "마지막 별이 라면 기계 뒤에 숨어 있어.", "kf_007_star_chase.png", "ramyeon", "discovery", "Mochi spots the last star near the hot water machine.", 1.27, -0.08, -0.08, "stars"),
    Beat(26, 116.8, 123.0, "Zumu", "뜨거운 물 소리가 커서 놀랐나 봐.", "kf_008_emotional_pause.png", "zumu", "understanding", "Zumu understands why the little star hid.", 1.18, 0.20, 0.00, "zumu"),
    Beat(27, 123.0, 127.0, "Mochi", "내 손 위에 앉아도 괜찮아. 아주 천천히.", "kf_008_emotional_pause.png", "mochi", "comfort", "Mochi offers his paw, surrounded by small warm lights.", 1.34, -0.24, 0.10, "mochi_many"),
    Beat(28, 127.0, 133.0, "Zumu", "모치 손은 따뜻해. 나도 옆에서 지켜볼게.", "kf_008_emotional_pause.png", "zumu", "supportive", "Zumu stays beside Mochi, calm and protective.", 1.20, 0.20, 0.02, "zumu"),
    Beat(29, 133.0, 136.8, "Mochi", "이제 모두 함께 나갈 준비 됐어?", "kf_005_door_meeting.png", "mochi", "ready", "Mochi looks to the group of star pieces near the door.", 1.20, -0.24, 0.04, "mochi"),
    Beat(30, 136.8, 144.4, "Zumu", "응! 파란 길을 만들게. 반짝반짝, 따라와!", "kf_005_door_meeting.png", "zumu", "excited", "Zumu creates the final blue light road outside.", 1.14, 0.32, -0.02, "zumu"),
    Beat(31, 144.4, 148.2, "Mochi", "문이 열린다. 하나씩, 조심조심.", "kf_006_door_meeting_alt.png", "door", "careful", "The automatic door opens and Mochi counts the stars out.", 1.16, -0.05, -0.08, "sensor"),
    Beat(32, 148.2, 156.2, "Zumu", "좋아! 모두 밤하늘 쪽으로 올라가고 있어!", "kf_006_door_meeting_alt.png", "zumu", "happy", "Zumu watches the star pieces rise into the rainy night.", 1.12, 0.30, -0.04, "zumu"),
    Beat(33, 156.2, 160.2, "Mochi", "간판의 별도 더 환해졌어.", "kf_001_store_wide.png", "sign", "happy", "The store sign star glows brighter.", 1.20, 0.20, -0.22, "stars"),
    Beat(34, 160.2, 168.4, "Zumu", "오늘 편의점은 별들의 정류장이었네.", "kf_001_store_wide.png", "store", "joy", "Wide warm shot of the store as the rain calms.", 1.04, 0.00, 0.02, "warm"),
    Beat(35, 168.4, 172.4, "Mochi", "주무, 내일도 같이 반짝임을 찾아볼까?", "kf_008_emotional_pause.png", "mochi", "ending", "Mochi smiles softly with small lights around him.", 1.30, -0.24, 0.08, "mochi_many"),
    Beat(36, 172.4, 180.0, "Zumu", "당연하지. 모치랑 가면 길이 무섭지 않아.", "kf_008_emotional_pause.png", "zumu", "ending", "Zumu smiles back as the final star dust fades.", 1.18, 0.20, 0.00, "zumu"),
]


def setup() -> dict[str, Image.Image]:
    for path in [EXPORT, KEYS, FRAMES]:
        path.mkdir(parents=True, exist_ok=True)
    for old in KEYS.glob("*.jpg"):
        old.unlink()
    for old in FRAMES.glob("*.jpg"):
        old.unlink()
    return {p.name: Image.open(p).convert("RGB") for p in SRC.glob("*.png")}


def crop_cover(img: Image.Image, zoom: float, panx: float, pany: float) -> Image.Image:
    sw, sh = img.size
    ratio = WIDTH / HEIGHT
    if sw / sh > ratio:
        ch = sh
        cw = int(ch * ratio)
    else:
        cw = sw
        ch = int(cw / ratio)
    cw = int(cw / zoom)
    ch = int(ch / zoom)
    cx = sw / 2 + panx * sw * 0.38
    cy = sh / 2 + pany * sh * 0.38
    left = int(min(max(cx - cw / 2, 0), sw - cw))
    top = int(min(max(cy - ch / 2, 0), sh - ch))
    return img.crop((left, top, left + cw, top + ch)).resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def soft_glow(size: int, color: tuple[int, int, int], alpha: int) -> Image.Image:
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.ellipse((size * 0.24, size * 0.24, size * 0.76, size * 0.76), fill=(*color, alpha))
    return layer.filter(ImageFilter.GaussianBlur(size * 0.12))


def paste_glow(base: Image.Image, x: float, y: float, radius: int, color: tuple[int, int, int], alpha: int) -> None:
    g = soft_glow(radius * 2, color, alpha)
    base.alpha_composite(g, (int(x - radius), int(y - radius)))


def add_phrase_lights(frame: Image.Image, beat: Beat, phase: float) -> Image.Image:
    rgba = frame.convert("RGBA")
    pulse = 0.5 + 0.5 * math.sin(phase * math.pi * 2)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(255, 210, 145, int(8 + 10 * pulse)))

    if beat.light in {"mochi", "mochi_many"}:
        center = (WIDTH * 0.36, HEIGHT * 0.55)
        paste_glow(overlay, center[0], center[1], int(82 + 16 * pulse), (255, 224, 112), 80)
        count = 18 if beat.light == "mochi_many" else 9
        for i in range(count):
            a = phase * math.pi * 2 + i * 0.72
            rx = 80 + (i % 4) * 18
            ry = 54 + (i % 3) * 14
            x = center[0] + math.cos(a) * rx
            y = center[1] + math.sin(a * 1.2) * ry - 80
            paste_glow(overlay, x, y, 10 + (i % 3) * 3, (255, 232, 135), 115)

    if beat.light == "zumu":
        center = (WIDTH * 0.66, HEIGHT * 0.45)
        paste_glow(overlay, center[0], center[1], int(105 + 16 * pulse), (83, 202, 255), 72)
        for i in range(10):
            x = center[0] - i * 42 - phase * 55
            y = center[1] + math.sin(i + phase * 4) * 18
            paste_glow(overlay, x, y, 12, (100, 218, 255), 95)

    if beat.light in {"stars", "sensor", "warm"}:
        color = (255, 225, 112) if beat.light != "sensor" else (255, 190, 88)
        for i in range(16):
            x = WIDTH * (0.18 + ((i * 0.113 + phase * 0.25) % 0.68))
            y = HEIGHT * (0.18 + ((i * 0.191 + phase * 0.16) % 0.58))
            paste_glow(overlay, x, y, 9 + (i % 4) * 3, color, 95)

    # Subtle rain/reflection, kept quiet.
    rng = np.random.default_rng(beat.idx * 1000 + int(phase * 100))
    if beat.idx < 9 or beat.idx > 22:
        for _ in range(20):
            x = int(rng.integers(-80, WIDTH + 80))
            y = int(rng.integers(0, HEIGHT))
            draw.line((x, y, x + 7, y + 22), fill=(190, 220, 255, 25), width=1)
    for i in range(7):
        y = HEIGHT - 155 + i * 19 + math.sin(phase * 8 + i) * 2
        draw.line((0, y, WIDTH, y), fill=(255, 224, 120, 10), width=1)

    out = Image.alpha_composite(rgba, overlay).convert("RGB")
    out = ImageEnhance.Contrast(out).enhance(1.035)
    out = ImageEnhance.Color(out).enhance(1.045)
    return out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=105, threshold=4))


def keyframe_for(beat: Beat, images: dict[str, Image.Image]) -> Image.Image:
    base = crop_cover(images[beat.source], beat.zoom, beat.panx, beat.pany)
    return add_phrase_lights(base, beat, 0.18)


def beat_for_time(sec: float) -> Beat:
    for beat in BEATS:
        if beat.start <= sec < beat.end:
            return beat
    return BEATS[-1]


def make_sfx() -> Path:
    sr = 44100
    n = sr * SECONDS
    t = np.linspace(0, SECONDS, n, endpoint=False)
    rng = np.random.default_rng(41)
    audio = rng.normal(0, 0.0028, n).astype(np.float32)
    audio += 0.006 * np.sin(2 * np.pi * 196 * t) + 0.004 * np.sin(2 * np.pi * 294 * t)

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
        audio[s:e] += 0.04 * np.sin(2 * np.pi * 88 * tt) * np.exp(-tt * 31)

    for beat in BEATS:
        if beat.speaker == "Mochi":
            step(beat.start + 0.4)
        if beat.light in {"stars", "mochi_many", "zumu", "sensor"}:
            tone(beat.start + 0.25, 620, 0.32, 0.016)
            tone(beat.start + 0.38, 830, 0.25, 0.010)
    audio = np.clip(audio, -0.75, 0.75)
    out = EXPORT / "scratch_music_sfx.wav"
    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes((audio * 32767).astype("<i2").tobytes())
    return out


def render(images: dict[str, Image.Image]) -> None:
    key_paths = {}
    for beat in BEATS:
        kf = keyframe_for(beat, images)
        path = KEYS / f"phrase_{beat.idx:02d}_{beat.speaker.lower()}.jpg"
        kf.save(path, quality=93, optimize=True, progressive=True)
        key_paths[beat.idx] = path

    with (EXPORT / "phrase_manifest.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["phrase", "start", "end", "speaker", "text_ko", "source", "keyframe", "action"])
        for beat in BEATS:
            writer.writerow([beat.idx, beat.start, beat.end, beat.speaker, beat.text, beat.source, key_paths[beat.idx].name, beat.action])

    frame_manifest = EXPORT / "frame_manifest_10fps.csv"
    with frame_manifest.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "time", "phrase", "speaker", "keyframe", "text_ko"])
        for i in range(TOTAL):
            sec = i / FPS
            beat = beat_for_time(sec)
            local = (sec - beat.start) / max(0.001, beat.end - beat.start)
            zoom = beat.zoom + math.sin(local * math.pi * 2) * 0.018
            panx = beat.panx + math.sin(local * math.pi) * 0.022 * (1 if beat.speaker == "Zumu" else -1)
            pany = beat.pany + math.cos(local * math.pi * 2) * 0.010
            frame = crop_cover(images[beat.source], zoom, panx, pany)
            frame = add_phrase_lights(frame, beat, local)
            frame.save(FRAMES / f"frame_{i + 1:06d}.jpg", quality=91, optimize=True, progressive=True)
            writer.writerow([i + 1, f"{sec:06.1f}", beat.idx, beat.speaker, key_paths[beat.idx].name, beat.text])
            if (i + 1) % 100 == 0:
                print(f"frames {i + 1}/{TOTAL}")


def mux_video(audio: Path) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    voice_mix = ROOT / "exports" / "ep001_production_clean_10fps" / "ep001_clean_audio_mix.m4a"
    out = EXPORT / "ep001_phrase_matched_10fps.mp4"
    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(FRAMES / "frame_%06d.jpg"),
        "-i",
        str(voice_mix if voice_mix.exists() else audio),
        "-i",
        str(audio),
        "-filter_complex",
        "[1:a]volume=1.0[v];[2:a]volume=0.45[s];[v][s]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.92[a]",
        "-map",
        "0:v",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "20",
        "-preset",
        "medium",
        "-c:a",
        "aac",
        "-b:a",
        "144k",
        "-shortest",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def write_html(video: Path) -> None:
    grid = "\n".join(
        f'<a href="exports/ep001_phrase_matched_10fps/phrase_keyframes/phrase_{b.idx:02d}_{b.speaker.lower()}.jpg"><img src="exports/ep001_phrase_matched_10fps/phrase_keyframes/phrase_{b.idx:02d}_{b.speaker.lower()}.jpg" alt="phrase {b.idx}"></a>'
        for b in BEATS
    )
    (ROOT / "ep001_phrase_matched.html").write_text(
        f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mochi EP001 - phrase matched</title>
  <style>
    body {{ margin:0; font-family:Arial,sans-serif; background:#10131b; color:#fff8dd; }}
    main {{ max-width:1200px; margin:auto; padding:28px; }}
    video {{ width:100%; border-radius:8px; background:#000; }}
    .links {{ display:flex; flex-wrap:wrap; gap:10px; margin:18px 0 26px; }}
    .links a {{ background:#ffe28a; color:#171717; padding:10px 12px; border-radius:6px; text-decoration:none; font-weight:700; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:10px; }}
    img {{ width:100%; display:block; border-radius:6px; }}
    p {{ color:#d8dded; }}
  </style>
</head>
<body>
<main>
  <h1>EP001 - image différente par phrase</h1>
  <p>Chaque réplique a son image clé, son cadrage, son émotion et ses lumières. Les voix restent une maquette à remplacer par des voix custom.</p>
  <video src="exports/ep001_phrase_matched_10fps/{video.name}" controls preload="metadata"></video>
  <div class="links">
    <a href="exports/ep001_phrase_matched_10fps/phrase_keyframes/">36 images clés</a>
    <a href="exports/ep001_phrase_matched_10fps/frames/">1800 frames</a>
    <a href="exports/ep001_phrase_matched_10fps/phrase_manifest.csv">Manifest phrases</a>
    <a href="exports/ep001_phrase_matched_10fps/frame_manifest_10fps.csv">Manifest frames</a>
  </div>
  <div class="grid">{grid}</div>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    images = setup()
    render(images)
    audio = make_sfx()
    video = mux_video(audio)
    write_html(video)
    print(video)


if __name__ == "__main__":
    main()
