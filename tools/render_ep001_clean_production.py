from __future__ import annotations

import asyncio
import csv
import math
import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import edge_tts
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "ep001_production_clean_10fps"
FRAMES = EXPORT / "frames"
KEYFRAMES = EXPORT / "keyframes"
VOICES = EXPORT / "voices"
FPS = 10
WIDTH = 1280
HEIGHT = 720
SECONDS = 180
TOTAL_FRAMES = FPS * SECONDS
PYTHON = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "python.exe"
DOWNLOADS = Path.home() / "Downloads"


SOURCE_IMAGES = [
    ("kf_001_store_wide.png", DOWNLOADS / "Image générée 1.png"),
    ("kf_002_store_wide_alt.png", DOWNLOADS / "Image générée 1 (1).png"),
    ("kf_003_store_wide_alt.png", DOWNLOADS / "Image générée 1 (2).png"),
    ("kf_004_store_wide_alt.png", DOWNLOADS / "Image générée 1 (3).png"),
    ("kf_005_door_meeting.png", DOWNLOADS / "Image générée 2.png"),
    ("kf_006_door_meeting_alt.png", DOWNLOADS / "Image générée 2 (1).png"),
    ("kf_007_star_chase.png", DOWNLOADS / "Image générée 3.png"),
    ("kf_008_emotional_pause.png", DOWNLOADS / "Image générée 4.png"),
]


@dataclass(frozen=True)
class Shot:
    shot_id: str
    start: float
    end: float
    image: str
    title: str
    action: str
    zoom0: float
    zoom1: float
    panx0: float
    panx1: float
    pany0: float
    pany1: float
    mood: str


@dataclass(frozen=True)
class Line:
    start: float
    end: float
    speaker: str
    text: str
    emotion: str


SHOTS = [
    Shot("001", 0, 8, "kf_001_store_wide.png", "비 오는 밤, 별빛 편의점 앞", "모치가 젖은 길 위에서 편의점 불빛을 발견한다.", 1.00, 1.06, -0.12, -0.06, 0.03, 0.00, "wonder"),
    Shot("002", 8, 16, "kf_002_store_wide_alt.png", "간판의 별", "간판의 작은 별들이 하나씩 따뜻하게 켜진다.", 1.05, 1.14, -0.08, 0.02, -0.02, -0.02, "wonder"),
    Shot("003", 16, 24, "kf_005_door_meeting.png", "주무의 푸른 꼬리", "주무가 빗속에서 날아와 모치 옆에 멈춘다.", 1.00, 1.08, 0.06, -0.03, 0.00, 0.00, "arrival"),
    Shot("004", 24, 32, "kf_006_door_meeting_alt.png", "문 센서의 반짝임", "자동문 센서가 별가루에 반응하며 빛난다.", 1.07, 1.16, 0.02, 0.06, -0.02, 0.02, "surprise"),
    Shot("005", 32, 42, "kf_007_star_chase.png", "안쪽 진열대", "별조각들이 삼각김밥과 컵라면 사이로 튄다.", 1.00, 1.10, -0.08, 0.03, 0.02, -0.02, "play"),
    Shot("006", 42, 52, "kf_007_star_chase.png", "미끄러운 바닥", "모치가 급히 따라가다 멈추고, 주무가 속도를 낮춘다.", 1.10, 1.18, 0.08, -0.06, 0.00, 0.01, "care"),
    Shot("007", 52, 62, "kf_008_emotional_pause.png", "불안한 작은 별", "가장 작은 별조각이 기운을 잃고 낮게 떨린다.", 1.00, 1.09, -0.04, 0.02, 0.00, 0.00, "soft"),
    Shot("008", 62, 72, "kf_008_emotional_pause.png", "모치의 따뜻한 숨", "모치가 천천히 숨을 쉬자 가슴 별빛이 부드럽게 번진다.", 1.08, 1.18, 0.00, -0.03, 0.00, -0.02, "breath"),
    Shot("009", 72, 82, "kf_005_door_meeting.png", "주무의 약속", "주무가 꼬리빛을 낮추고 작은 별이 겁먹지 않게 기다린다.", 1.06, 1.12, 0.03, -0.05, -0.01, 0.01, "promise"),
    Shot("010", 82, 92, "kf_007_star_chase.png", "천천히 움직이는 별", "작은 별이 다시 빛나며 바닥 위로 미끄러진다.", 1.13, 1.04, -0.03, 0.05, 0.02, -0.01, "hope"),
    Shot("011", 92, 102, "kf_006_door_meeting_alt.png", "자동문의 박자", "문이 열리고 닫히는 박자에 별조각들이 줄을 맞춘다.", 1.04, 1.13, 0.04, -0.04, 0.00, 0.00, "rhythm"),
    Shot("012", 102, 112, "kf_001_store_wide.png", "비와 네온", "밖의 비와 안의 빛이 유리문 위에서 섞인다.", 1.02, 1.10, -0.08, 0.02, 0.03, -0.02, "warm"),
    Shot("013", 112, 122, "kf_007_star_chase.png", "컵라면 기계 옆", "마지막 별조각이 뜨거운 물 기계 불빛 뒤에 숨는다.", 1.10, 1.18, 0.05, -0.05, -0.02, 0.02, "discovery"),
    Shot("014", 122, 132, "kf_008_emotional_pause.png", "손바닥 위의 빛", "모치가 손을 내밀자 별조각이 스스로 내려앉는다.", 1.05, 1.16, -0.02, 0.02, 0.00, -0.02, "trust"),
    Shot("015", 132, 144, "kf_005_door_meeting.png", "푸른 길", "주무가 안전한 푸른 빛길을 만들고 별조각들이 따라간다.", 1.00, 1.10, 0.06, -0.05, 0.02, -0.01, "guide"),
    Shot("016", 144, 156, "kf_006_door_meeting_alt.png", "밤하늘로", "자동문이 열리고 별조각들이 비 사이로 올라간다.", 1.08, 1.01, -0.04, 0.04, 0.00, 0.02, "release"),
    Shot("017", 156, 168, "kf_001_store_wide.png", "새로 빛나는 간판", "간판의 별이 조금 더 환해지고 거리의 물웅덩이에 반사된다.", 1.04, 1.10, -0.02, 0.02, 0.01, -0.01, "joy"),
    Shot("018", 168, 180, "kf_008_emotional_pause.png", "다음 모험의 약속", "모치와 주무가 웃고 마지막 별가루가 화면을 부드럽게 닫는다.", 1.00, 1.08, 0.00, 0.00, 0.00, -0.01, "ending"),
]


LINES = [
    Line(1.0, 4.0, "Mochi", "여기 봐, 주무. 밤인데 편의점이 별처럼 빛나.", "soft wonder"),
    Line(4.4, 7.2, "Zumu", "와아, 간판에 작은 별이 숨어 있어!", "bright"),
    Line(8.0, 11.0, "Mochi", "비 냄새도 나고, 따뜻한 우유 냄새도 나.", "curious"),
    Line(11.5, 14.8, "Zumu", "그럼 조심히 들어가 보자. 내 꼬리빛은 약하게 켤게.", "careful"),
    Line(16.4, 19.6, "Mochi", "잠깐, 문 위에서 뭔가 반짝였어.", "alert"),
    Line(20.0, 23.0, "Zumu", "센서야. 그런데 오늘은 별가루를 먹은 것 같아.", "playful"),
    Line(24.2, 27.2, "Mochi", "문아, 우리를 놀라게 하지 말아 줘.", "gentle"),
    Line(27.6, 31.2, "Zumu", "괜찮아, 내가 먼저 살짝 날아가 볼게.", "brave"),
    Line(33.0, 36.2, "Mochi", "앗! 별조각들이 컵라면 쪽으로 도망가!", "surprised"),
    Line(36.6, 40.2, "Zumu", "잡자! 하지만 진열대는 건드리지 않기!", "leader"),
    Line(42.0, 45.4, "Mochi", "바닥이 미끄러워. 천천히 가야 해.", "careful"),
    Line(45.8, 49.2, "Zumu", "좋아, 속도 줄일게. 반짝임만 따라와.", "supportive"),
    Line(52.4, 55.2, "Mochi", "저 작은 별은 왜 떨고 있을까?", "worried"),
    Line(55.6, 59.4, "Zumu", "너무 밝은 불빛이 무서웠나 봐.", "soft"),
    Line(62.0, 65.4, "Mochi", "괜찮아. 우리는 기다릴 수 있어.", "comfort"),
    Line(65.8, 69.4, "Zumu", "내 꼬리빛도 작게 만들게. 이렇게.", "comfort"),
    Line(72.0, 75.0, "Mochi", "봐, 조금씩 다시 빛나고 있어.", "hope"),
    Line(75.4, 79.2, "Zumu", "좋아. 이제 별들이 줄을 서면 문을 통과할 수 있어.", "clever"),
    Line(82.0, 85.4, "Mochi", "문이 열릴 때마다 바람이 살짝 불어.", "observing"),
    Line(85.8, 89.8, "Zumu", "그 바람을 박자로 쓰자. 하나, 둘, 반짝!", "rhythm"),
    Line(93.0, 96.0, "Mochi", "작은 별들아, 너무 서두르지 마.", "gentle"),
    Line(96.4, 100.6, "Zumu", "내 푸른 길 위로 천천히 오면 돼.", "guide"),
    Line(103.0, 106.4, "Mochi", "밖은 차갑지만, 여기 빛은 따뜻해.", "warm"),
    Line(106.8, 110.6, "Zumu", "그래서 별들이 길을 잃지 않는 거야.", "warm"),
    Line(113.0, 116.4, "Mochi", "마지막 별이 라면 기계 뒤에 숨어 있어.", "discovery"),
    Line(116.8, 120.4, "Zumu", "뜨거운 물 소리가 커서 놀랐나 봐.", "understanding"),
    Line(123.0, 126.6, "Mochi", "내 손 위에 앉아도 괜찮아. 아주 천천히.", "comfort"),
    Line(127.0, 130.6, "Zumu", "모치 손은 따뜻해. 나도 옆에서 지켜볼게.", "supportive"),
    Line(133.0, 136.4, "Mochi", "이제 모두 함께 나갈 준비 됐어?", "ready"),
    Line(136.8, 141.0, "Zumu", "응! 파란 길을 만들게. 반짝반짝, 따라와!", "excited"),
    Line(144.4, 147.8, "Mochi", "문이 열린다. 하나씩, 조심조심.", "careful"),
    Line(148.2, 152.4, "Zumu", "좋아! 모두 밤하늘 쪽으로 올라가고 있어!", "happy"),
    Line(156.2, 159.8, "Mochi", "간판의 별도 더 환해졌어.", "happy"),
    Line(160.2, 164.0, "Zumu", "오늘 편의점은 별들의 정류장이었네.", "joy"),
    Line(168.4, 172.0, "Mochi", "주무, 내일도 같이 반짝임을 찾아볼까?", "ending"),
    Line(172.4, 176.0, "Zumu", "당연하지. 모치랑 가면 길이 무섭지 않아.", "ending"),
]


def ensure_dirs() -> dict[str, Path]:
    for path in [EXPORT, FRAMES, KEYFRAMES, VOICES]:
        path.mkdir(parents=True, exist_ok=True)
    copied: dict[str, Path] = {}
    for name, src in SOURCE_IMAGES:
        if not src.exists():
            raise FileNotFoundError(src)
        dst = KEYFRAMES / name
        shutil.copy2(src, dst)
        copied[name] = dst
    return copied


def shot_for_frame(frame_idx: int) -> Shot:
    sec = frame_idx / FPS
    for shot in SHOTS:
        if shot.start <= sec < shot.end:
            return shot
    return SHOTS[-1]


def cover_image(img: Image.Image, zoom: float, panx: float, pany: float) -> Image.Image:
    sw, sh = img.size
    target_ratio = WIDTH / HEIGHT
    if sw / sh > target_ratio:
        crop_h = sh
        crop_w = int(crop_h * target_ratio)
    else:
        crop_w = sw
        crop_h = int(crop_w / target_ratio)
    crop_w = max(1, int(crop_w / zoom))
    crop_h = max(1, int(crop_h / zoom))
    cx = sw / 2 + panx * sw * 0.30
    cy = sh / 2 + pany * sh * 0.30
    left = int(min(max(cx - crop_w / 2, 0), sw - crop_w))
    top = int(min(max(cy - crop_h / 2, 0), sh - crop_h))
    return img.crop((left, top, left + crop_w, top + crop_h)).resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def glow_layer(size: tuple[int, int], cx: float, cy: float, radius: float, color: tuple[int, int, int], alpha: int) -> Image.Image:
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(*color, alpha))
    return layer.filter(ImageFilter.GaussianBlur(radius / 2.4))


def add_vignette(frame: Image.Image) -> Image.Image:
    y, x = np.ogrid[-1:1:HEIGHT * 1j, -1:1:WIDTH * 1j]
    mask = np.clip(1 - (np.sqrt(x * x + y * y) - 0.25) * 0.74, 0.62, 1.0)
    arr = np.asarray(frame).astype(np.float32)
    arr *= mask[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def add_lighting(frame: Image.Image, idx: int, shot: Shot, local_t: float) -> Image.Image:
    rgba = frame.convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    pulse = 0.5 + 0.5 * math.sin(idx * 0.16)

    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(255, 210, 150, int(8 + pulse * 12)))

    # Soft chest/star light zones. These are broad light passes, not visible UI dots.
    if shot.mood in {"breath", "soft", "trust", "hope", "ending"}:
        overlay = Image.alpha_composite(overlay, glow_layer((WIDTH, HEIGHT), WIDTH * 0.42, HEIGHT * 0.57, 95 + 22 * pulse, (255, 223, 112), 58))
    if shot.mood in {"arrival", "guide", "release", "play", "rhythm"}:
        overlay = Image.alpha_composite(overlay, glow_layer((WIDTH, HEIGHT), WIDTH * (0.57 + 0.25 * local_t), HEIGHT * (0.42 - 0.08 * math.sin(local_t * math.pi)), 115, (90, 202, 255), 56))

    # Rain, glass shimmer, and reflections.
    rng = np.random.default_rng(idx * 19 + int(shot.shot_id))
    if shot.start < 24 or shot.start > 100:
        for _ in range(22):
            x = int(rng.integers(-100, WIDTH + 100))
            y = int(rng.integers(0, HEIGHT))
            draw.line((x, y, x + 8, y + 22), fill=(190, 220, 255, 26), width=1)
    for i in range(9):
        y = HEIGHT - 150 + i * 17 + 2 * math.sin(idx * 0.06 + i)
        draw.line((0, y, WIDTH, y), fill=(255, 225, 150, 8), width=1)

    # Star dust as blurred warm light, kept subtle.
    if shot.mood in {"play", "rhythm", "guide", "release", "joy", "ending", "hope"}:
        for i in range(14):
            x = WIDTH * (0.18 + ((i * 0.091 + local_t * 0.42) % 0.70))
            y = HEIGHT * (0.22 + ((i * 0.163 + local_t * 0.19) % 0.54))
            r = 7 + (i % 4) * 3 + pulse * 3
            overlay = Image.alpha_composite(overlay, glow_layer((WIDTH, HEIGHT), x, y, r, (255, 226, 112), 70))

    rgba = Image.alpha_composite(rgba, overlay)
    rgba = rgba.filter(ImageFilter.UnsharpMask(radius=1.0, percent=105, threshold=4))
    return add_vignette(rgba.convert("RGB"))


def render_frames(images: dict[str, Path]) -> None:
    for old in FRAMES.glob("frame_*.jpg"):
        old.unlink()
    cache = {name: Image.open(path).convert("RGB") for name, path in images.items()}
    manifest = EXPORT / "frame_manifest_10fps.csv"
    with manifest.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["frame", "timecode", "shot", "keyframe", "action_ko", "no_burned_text"])
        for idx in range(TOTAL_FRAMES):
            shot = shot_for_frame(idx)
            local_t = ((idx / FPS) - shot.start) / max(0.001, shot.end - shot.start)
            eased = local_t * local_t * (3 - 2 * local_t)
            zoom = shot.zoom0 + (shot.zoom1 - shot.zoom0) * eased + math.sin(idx * 0.033) * 0.003
            panx = shot.panx0 + (shot.panx1 - shot.panx0) * eased
            pany = shot.pany0 + (shot.pany1 - shot.pany0) * eased
            frame = cover_image(cache[shot.image], zoom, panx, pany)
            frame = ImageEnhance.Color(frame).enhance(1.045)
            frame = ImageEnhance.Contrast(frame).enhance(1.035)
            frame = add_lighting(frame, idx, shot, local_t)
            frame.save(FRAMES / f"frame_{idx + 1:06d}.jpg", quality=91, optimize=True, progressive=True)
            tc = f"{idx // FPS // 60:02d}:{idx // FPS % 60:02d}.{idx % FPS}"
            writer.writerow([idx + 1, tc, shot.shot_id, shot.image, shot.action, "yes"])
            if (idx + 1) % 100 == 0:
                print(f"frames {idx + 1}/{TOTAL_FRAMES}")


def srt_time(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_docs() -> None:
    (EXPORT / "EP001_SCENARIO_KO.md").write_text(
        "# EP001 별빛 편의점\n\n"
        "러닝타임: 3분. 배경은 한국의 비 오는 밤, 24시간 편의점. 모치와 주무는 길 잃은 별조각들을 겁주지 않고 집으로 돌려보낸다.\n\n"
        + "\n".join(f"- SH{shot.shot_id} {shot.start:05.1f}-{shot.end:05.1f}s: {shot.title} / {shot.action}" for shot in SHOTS)
        + "\n\n## 대사\n\n"
        + "\n".join(f"- {line.start:05.1f}-{line.end:05.1f}s {line.speaker}: {line.text}" for line in LINES)
        + "\n",
        encoding="utf-8",
    )
    with (EXPORT / "EP001_SUBTITLES_KO.srt").open("w", encoding="utf-8") as f:
        for i, line in enumerate(LINES, 1):
            f.write(f"{i}\n{srt_time(line.start)} --> {srt_time(line.end)}\n{line.speaker}: {line.text}\n\n")
    with (EXPORT / "EP001_SUBTITLES_KO.vtt").open("w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for line in LINES:
            start = srt_time(line.start).replace(",", ".")
            end = srt_time(line.end).replace(",", ".")
            f.write(f"{start} --> {end}\n{line.speaker}: {line.text}\n\n")
    (EXPORT / "VOICE_CASTING.md").write_text(
        "# Voice casting\n\n"
        "- Mochi: `ko-KR-SunHiNeural`, rate +18%, pitch +8Hz, warm and small.\n"
        "- Zumu: `ko-KR-HyunsuMultilingualNeural`, rate +20%, pitch +10Hz, bright and quick.\n"
        "- No local robotic Windows TTS. If final budget allows, replace these with ElevenLabs/OpenArt custom childlike character voices using the same Korean lines.\n",
        encoding="utf-8",
    )


async def synthesize_voices() -> list[tuple[float, Path, str]]:
    clips: list[tuple[float, Path, str]] = []
    for i, line in enumerate(LINES, 1):
        voice = "ko-KR-SunHiNeural" if line.speaker == "Mochi" else "ko-KR-HyunsuMultilingualNeural"
        rate = "+18%" if line.speaker == "Mochi" else "+20%"
        pitch = "+8Hz" if line.speaker == "Mochi" else "+10Hz"
        out = VOICES / f"{i:03d}_{line.speaker.lower()}.mp3"
        communicate = edge_tts.Communicate(line.text, voice=voice, rate=rate, pitch=pitch, volume="+0%")
        await communicate.save(str(out))
        clips.append((line.start, out, line.speaker))
        print(f"voice {i}/{len(LINES)} {line.speaker}")
    return clips


def write_music_and_sfx() -> Path:
    sr = 44100
    n = sr * SECONDS
    t = np.linspace(0, SECONDS, n, endpoint=False)
    rng = np.random.default_rng(22)
    audio = rng.normal(0, 0.0035, n).astype(np.float32)
    # Quiet lullaby pad, low and soft.
    audio += 0.010 * np.sin(2 * np.pi * 196 * t)
    audio += 0.008 * np.sin(2 * np.pi * 247 * t)
    audio += 0.006 * np.sin(2 * np.pi * 330 * t)

    def tone(start: float, freq: float, dur: float, vol: float) -> None:
        s = int(start * sr)
        e = min(n, s + int(dur * sr))
        tt = np.linspace(0, dur, e - s, endpoint=False)
        env = np.sin(np.linspace(0, math.pi, e - s)) ** 2
        audio[s:e] += vol * np.sin(2 * np.pi * freq * tt) * env

    def step(start: float) -> None:
        s = int(start * sr)
        e = min(n, s + int(0.13 * sr))
        tt = np.linspace(0, 0.13, e - s, endpoint=False)
        audio[s:e] += 0.045 * np.sin(2 * np.pi * 90 * tt) * np.exp(-tt * 30)

    for sec in [2, 3.1, 4.2, 9.8, 10.9, 12.0, 42.2, 43.0, 44.0, 45.2, 94.0, 96.0, 124.5, 145.5]:
        step(sec)
    for sec in [16.0, 24.0, 31.8, 52.0, 72.0, 82.0, 112.0, 132.0, 144.0, 156.0, 174.0]:
        tone(sec, 622, 0.36, 0.020)
        tone(sec + 0.08, 784, 0.30, 0.014)
    for sec in [24.2, 92.4, 144.2]:
        tone(sec, 392, 0.22, 0.018)

    audio = np.clip(audio, -0.7, 0.7)
    out = EXPORT / "music_sfx_soft.wav"
    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes((audio * 32767).astype("<i2").tobytes())
    return out


def mix_audio(base: Path, clips: list[tuple[float, Path, str]]) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out = EXPORT / "ep001_clean_audio_mix.m4a"
    cmd = [ffmpeg, "-y", "-i", str(base)]
    for _, clip, _ in clips:
        cmd += ["-i", str(clip)]
    parts = ["[0:a]volume=0.62[base]"]
    labels = ["[base]"]
    for i, (start, _, speaker) in enumerate(clips, 1):
        delay = int(start * 1000)
        volume = "1.20" if speaker == "Mochi" else "1.13"
        parts.append(f"[{i}:a]adelay={delay}:all=1,volume={volume}[v{i}]")
        labels.append(f"[v{i}]")
    filter_complex = ";".join(parts) + ";" + "".join(labels) + f"amix=inputs={len(labels)}:duration=longest:normalize=0,alimiter=limit=0.92[mix]"
    cmd += ["-filter_complex", filter_complex, "-map", "[mix]", "-t", str(SECONDS), "-c:a", "aac", "-b:a", "160k", str(out)]
    subprocess.run(cmd, check=True)
    return out


def render_video(audio: Path) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out = EXPORT / "ep001_clean_final_10fps.mp4"
    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(FRAMES / "frame_%06d.jpg"),
        "-i",
        str(audio),
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
        "160k",
        "-shortest",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def write_html(video: Path) -> None:
    samples = [1, 80, 160, 240, 360, 520, 620, 720, 920, 1120, 1320, 1440, 1560, 1680, 1800]
    grid = "\n".join(
        f'<a href="exports/ep001_production_clean_10fps/frames/frame_{i:06d}.jpg"><img src="exports/ep001_production_clean_10fps/frames/frame_{i:06d}.jpg" alt="frame {i}"></a>'
        for i in samples
    )
    (ROOT / "ep001_production_clean.html").write_text(
        f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mochi EP001 - clean production</title>
  <style>
    body {{ margin:0; font-family: Arial, sans-serif; background:#10131b; color:#fff6dc; }}
    main {{ max-width:1180px; margin:auto; padding:28px; }}
    video {{ width:100%; border-radius:8px; background:#000; }}
    .links {{ display:flex; flex-wrap:wrap; gap:10px; margin:18px 0 26px; }}
    .links a {{ background:#ffe082; color:#171717; padding:10px 12px; border-radius:6px; text-decoration:none; font-weight:700; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); gap:10px; }}
    img {{ width:100%; display:block; border-radius:6px; }}
    p {{ color:#d8dded; }}
  </style>
</head>
<body>
<main>
  <h1>EP001 clean - frames sans texte + voix + sons</h1>
  <p>Version propre: les sous-titres ne sont pas incrustés dans les images. GitHub/YouTube peut utiliser le fichier SRT séparé.</p>
  <video src="exports/ep001_production_clean_10fps/{video.name}" controls preload="metadata">
    <track src="exports/ep001_production_clean_10fps/EP001_SUBTITLES_KO.vtt" kind="subtitles" srclang="ko" label="한국어" default>
  </video>
  <div class="links">
    <a href="exports/ep001_production_clean_10fps/frames/">1800 frames clean</a>
    <a href="exports/ep001_production_clean_10fps/EP001_SUBTITLES_KO.srt">Sous-titres SRT</a>
    <a href="exports/ep001_production_clean_10fps/EP001_SUBTITLES_KO.vtt">Sous-titres VTT</a>
    <a href="exports/ep001_production_clean_10fps/EP001_SCENARIO_KO.md">Scénario coréen</a>
    <a href="exports/ep001_production_clean_10fps/VOICE_CASTING.md">Voix</a>
    <a href="exports/ep001_production_clean_10fps/frame_manifest_10fps.csv">Manifeste frames</a>
  </div>
  <div class="grid">{grid}</div>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )


async def main() -> None:
    images = ensure_dirs()
    write_docs()
    render_frames(images)
    base_audio = write_music_and_sfx()
    voice_clips = await synthesize_voices()
    final_audio = mix_audio(base_audio, voice_clips)
    video = render_video(final_audio)
    write_html(video)
    print(f"done video: {video}")
    print(f"frames: {FRAMES}")


if __name__ == "__main__":
    asyncio.run(main())
