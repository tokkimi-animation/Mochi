from __future__ import annotations

import csv
import math
import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "ep001_full_frames_10fps"
FRAMES = EXPORT / "frames"
KEYFRAMES = EXPORT / "keyframes"
FPS = 10
WIDTH = 1280
HEIGHT = 720
SECONDS = 180
TOTAL_FRAMES = FPS * SECONDS

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
    start: int
    end: int
    image_name: str
    title_ko: str
    action_ko: str
    dialogue_ko: str
    sfx_ko: str
    prompt: str
    zoom0: float
    zoom1: float
    panx0: float
    panx1: float
    pany0: float
    pany1: float
    mood: str


SHOTS = [
    Shot("001", 0, 10, "kf_001_store_wide.png", "비 오는 밤의 편의점", "모치가 별빛 편의점 앞에서 멈춘다. 유리창 불빛과 젖은 바닥 반사가 살아난다.", "모치: 여기는... 아직 불이 켜져 있어.", "빗소리, 작은 발걸음", "wide exterior Korean convenience store at rainy night, plush character Mochi hesitates, warm neon reflections", 1.00, 1.05, -0.10, -0.02, 0.02, 0.00, "wonder"),
    Shot("002", 10, 20, "kf_002_store_wide_alt.png", "자동문 앞", "모치가 천천히 다가가고 가슴의 별빛이 약하게 숨 쉰다.", "모치: 안에 누가 있을까?", "문 센서 전자음, 발걸음", "slow push toward automatic door, chest star glow pulses softly, rain reflections", 1.04, 1.11, -0.05, 0.03, 0.02, -0.02, "curious"),
    Shot("003", 20, 30, "kf_005_door_meeting.png", "주무 등장", "주무가 푸른 꼬리빛을 남기며 유리문 밖에서 나타난다.", "주무: 모치! 나야, 주무!", "부드러운 별 꼬리 소리", "Zumu arrives outside glass door with comet tail, cute plush cinematic lighting", 1.00, 1.08, 0.05, -0.05, -0.01, 0.01, "relief"),
    Shot("004", 30, 40, "kf_006_door_meeting_alt.png", "문 센서의 장난", "문 위 센서가 반짝이고 작은 별조각들이 둥글게 맴돈다.", "모치: 문이 우리를 놀리는 것 같아.", "센서 삑, 작은 별소리", "automatic door sensor sparkles, little star fragments circle, plush characters surprised", 1.07, 1.13, 0.00, 0.04, -0.02, 0.02, "surprised"),
    Shot("005", 40, 50, "kf_007_star_chase.png", "별조각이 도망쳐", "가게 안으로 들어온 별조각들이 컵라면 진열대 사이로 튄다.", "주무: 잡자! 그런데 조심히!", "별 튐, 매장 조명 윙", "inside Korean convenience store, glowing star pieces bounce between ramyeon and kimbap shelves", 1.00, 1.09, -0.06, 0.04, 0.02, -0.02, "playful"),
    Shot("006", 50, 60, "kf_007_star_chase.png", "반짝이는 추격", "주무가 앞서 날고 모치는 짧은 발로 따라간다. 바닥 반사에 별빛이 지나간다.", "모치: 너무 빨라!", "빠른 발걸음, 부드러운 휙", "gentle chase, plush Mochi runs, Zumu flies, star trails on polished floor", 1.08, 1.16, 0.06, -0.08, -0.01, 0.01, "playful"),
    Shot("007", 60, 70, "kf_008_emotional_pause.png", "멈춘 별빛", "별조각 하나가 힘을 잃고 낮게 떠 있다. 모치와 주무가 걱정한다.", "주무: 저 별, 겁먹었나 봐.", "소리 줄어듦, 낮은 반짝임", "quiet emotional beat inside convenience store, small star loses glow, plush characters concerned", 1.00, 1.07, -0.04, 0.03, 0.00, 0.00, "tender"),
    Shot("008", 70, 80, "kf_008_emotional_pause.png", "모치의 숨", "모치가 천천히 숨을 고르고 가슴 별빛을 따뜻하게 밝힌다.", "모치: 괜찮아. 급하게 안 해도 돼.", "따뜻한 숨, 작은 빛 번짐", "Mochi breathes calmly, chest star grows warm, soft plush texture, emotional close up", 1.07, 1.17, 0.00, -0.02, 0.01, -0.02, "calm"),
    Shot("009", 80, 90, "kf_005_door_meeting.png", "주무의 약속", "주무가 꼬리빛을 작게 낮추고 별조각에게 천천히 다가간다.", "주무: 내가 천천히 빛날게. 넌 따라오기만 해.", "꼬리빛 웅, 조용한 별소리", "Zumu dims comet tail to guide a frightened little star, gentle character acting", 1.05, 1.13, 0.02, -0.04, -0.01, 0.01, "gentle"),
    Shot("010", 90, 100, "kf_007_star_chase.png", "다시 움직이는 별", "별조각이 조금씩 흔들리다 따뜻한 노란빛으로 움직인다.", "모치: 봐, 움직인다!", "작은 성공음", "little star regains glow, warm yellow light, convenience store reflections", 1.12, 1.04, -0.03, 0.05, 0.02, -0.01, "hope"),
    Shot("011", 100, 110, "kf_006_door_meeting_alt.png", "문이 열리는 리듬", "자동문이 열리고 닫히는 리듬에 맞춰 별조각들이 줄을 선다.", "주무: 삐, 쉬익, 반짝! 이 박자야.", "문 열림, 리듬 발소리", "automatic door rhythm becomes a game, star pieces line up with soft glowing trails", 1.04, 1.12, 0.03, -0.03, 0.00, 0.00, "clever"),
    Shot("012", 110, 120, "kf_001_store_wide.png", "밖의 비와 안의 빛", "카메라가 밖의 빗물 반사와 안의 따뜻한 매장을 부드럽게 연결한다.", "모치: 밖은 차갑지만, 안은 따뜻해.", "비, 네온 웅", "cinematic transition from rainy street reflection to warm convenience store interior", 1.02, 1.09, -0.08, 0.02, 0.03, -0.02, "warm"),
    Shot("013", 120, 130, "kf_007_star_chase.png", "마지막 별조각", "가장 작은 별조각이 컵라면 기계 불빛에 숨어 있다.", "모치: 거기 있었구나.", "뜨거운 물 기계 낮은 소리", "tiny star hiding near Korean ramyeon hot water machine, warm practical light", 1.10, 1.18, 0.05, -0.05, -0.02, 0.02, "discovery"),
    Shot("014", 130, 140, "kf_008_emotional_pause.png", "손바닥 위의 빛", "모치가 손을 내밀자 별조각이 손 위에 내려앉는다.", "모치: 같이 가자. 우리가 기다릴게.", "부드러운 착지음", "little star lands on Mochi's paw, plush tenderness, glowing reflections", 1.05, 1.15, -0.02, 0.02, 0.00, -0.02, "trust"),
    Shot("015", 140, 150, "kf_005_door_meeting.png", "주무의 길", "주무가 안전한 푸른 길을 만들고 별조각들이 따라간다.", "주무: 파란 길만 따라와!", "빛길 흐름, 작은 웃음", "Zumu creates safe blue comet trail, star pieces follow, Korean storefront outside", 1.00, 1.09, 0.06, -0.04, 0.02, -0.01, "active"),
    Shot("016", 150, 160, "kf_006_door_meeting_alt.png", "편의점 밖으로", "문이 열리고 별조각들이 밤하늘 쪽으로 나간다. 모치는 안심한다.", "모치: 모두 집으로 가고 있어.", "자동문, 빗소리 밝아짐", "stars exit through automatic door to Korean night sky, plush characters relieved", 1.08, 1.01, -0.04, 0.04, 0.00, 0.02, "release"),
    Shot("017", 160, 170, "kf_001_store_wide.png", "간판의 새 별", "편의점 간판의 별이 한 번 더 따뜻하게 반짝인다.", "주무: 오늘도 반짝이는 하루 됐네!", "간판 반짝, 잔잔한 음악", "store sign glows warmly, rainy Korean street, magical but grounded", 1.04, 1.10, -0.02, 0.02, 0.01, -0.01, "joy"),
    Shot("018", 170, 180, "kf_008_emotional_pause.png", "다음 모험으로", "모치와 주무가 서로를 보고 작게 웃는다. 마지막 별가루가 화면을 덮는다.", "모치: 내일도 같이 찾아보자.", "별가루, 부드러운 엔딩", "final warm smile, Mochi and Zumu, soft plush, star dust transition", 1.00, 1.08, 0.00, 0.00, 0.00, -0.01, "ending"),
]


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/malgunbd.ttf"),
        Path("C:/Windows/Fonts/NanumGothic.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


FONT_TITLE = font(28)
FONT_DIALOGUE = font(34)
FONT_SMALL = font(18)


def ensure_inputs() -> dict[str, Path]:
    EXPORT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    KEYFRAMES.mkdir(parents=True, exist_ok=True)
    copied = {}
    for name, src in SOURCE_IMAGES:
        if not src.exists():
            raise FileNotFoundError(src)
        dst = KEYFRAMES / name
        shutil.copy2(src, dst)
        copied[name] = dst
    return copied


def cover_image(img: Image.Image, zoom: float, panx: float, pany: float) -> Image.Image:
    img = img.convert("RGB")
    sw, sh = img.size
    target_ratio = WIDTH / HEIGHT
    src_ratio = sw / sh
    if src_ratio > target_ratio:
        crop_h = sh
        crop_w = int(crop_h * target_ratio)
    else:
        crop_w = sw
        crop_h = int(crop_w / target_ratio)

    crop_w = max(1, int(crop_w / zoom))
    crop_h = max(1, int(crop_h / zoom))
    max_x = sw - crop_w
    max_y = sh - crop_h
    cx = sw / 2 + panx * sw * 0.30
    cy = sh / 2 + pany * sh * 0.30
    left = int(min(max(cx - crop_w / 2, 0), max_x))
    top = int(min(max(cy - crop_h / 2, 0), max_y))
    return img.crop((left, top, left + crop_w, top + crop_h)).resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def add_vignette(frame: Image.Image, strength: float) -> Image.Image:
    y, x = np.ogrid[-1:1:HEIGHT * 1j, -1:1:WIDTH * 1j]
    radius = np.sqrt(x * x + y * y)
    mask = np.clip(1 - (radius - 0.30) * strength, 0.58, 1.0)
    arr = np.asarray(frame).astype(np.float32)
    arr *= mask[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def draw_glow(draw: ImageDraw.ImageDraw, x: float, y: float, r: float, color: tuple[int, int, int], alpha: int) -> None:
    for k in range(5, 0, -1):
        rr = r * k / 2.2
        a = int(alpha * (k / 5) ** 2 * 0.28)
        draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(*color, a))
    draw.ellipse((x - r, y - r, x + r, y + r), fill=(*color, alpha))


def add_light_and_motion(frame: Image.Image, frame_idx: int, shot: Shot, local_t: float) -> Image.Image:
    rgba = frame.convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    pulse = 0.5 + 0.5 * math.sin(frame_idx * 0.18)
    warm = int(55 + 40 * pulse)
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(255, 210, 130, warm // 8))

    # Rain and reflection shimmer: quiet, not noisy.
    rng = np.random.default_rng(frame_idx + int(shot.shot_id))
    if "비" in shot.title_ko or shot.start < 25 or shot.start >= 110:
        for _ in range(34):
            x = int(rng.integers(-80, WIDTH + 80))
            y = int(rng.integers(0, HEIGHT))
            length = int(rng.integers(10, 24))
            draw.line((x, y, x + 7, y + length), fill=(185, 215, 255, 42), width=1)
    for i in range(8):
        y = HEIGHT - 160 + i * 18 + 2 * math.sin(frame_idx * 0.05 + i)
        draw.line((0, y, WIDTH, y), fill=(255, 220, 120, 12), width=1)

    # Floating star particles. Their positions are deterministic per frame.
    star_count = 18 if shot.mood in {"playful", "active", "release"} else 10
    for i in range(star_count):
        phase = frame_idx * 0.017 + i * 1.618
        x = (WIDTH * (0.18 + ((i * 0.137 + local_t * 0.22) % 0.70))) + math.sin(phase) * 18
        y = HEIGHT * (0.18 + ((i * 0.211 + local_t * 0.11) % 0.58)) + math.cos(phase) * 11
        r = 2.0 + (i % 4) * 0.9 + pulse * 1.0
        draw_glow(draw, x, y, r, (255, 224, 105), int(95 + 75 * pulse))

    # A guided trail for Zumu and the star pieces.
    if shot.mood in {"playful", "active", "release", "clever"}:
        for i in range(5):
            x0 = WIDTH * (0.20 + local_t * 0.55) - i * 70
            y0 = HEIGHT * (0.36 + 0.12 * math.sin(local_t * math.pi * 2 + i))
            draw.line((x0 - 80, y0 + 45, x0, y0), fill=(95, 198, 255, 52), width=4)
            draw_glow(draw, x0, y0, 5 + i, (120, 225, 255), 105)

    # Soft breathing chest/star glow approximation: light only, no fake body deformation.
    if shot.mood in {"calm", "tender", "trust", "ending", "hope"}:
        draw_glow(draw, WIDTH * 0.44, HEIGHT * 0.56, 30 + pulse * 12, (255, 228, 120), 78)

    rgba = Image.alpha_composite(rgba, overlay)
    rgba = rgba.filter(ImageFilter.UnsharpMask(radius=1.2, percent=110, threshold=4))
    return rgba.convert("RGB")


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    line = ""
    for word in words:
        candidate = word if not line else f"{line} {word}"
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def add_labels(frame: Image.Image, shot: Shot, frame_idx: int) -> Image.Image:
    rgba = frame.convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    # Caption band.
    draw.rounded_rectangle((70, HEIGHT - 126, WIDTH - 70, HEIGHT - 38), radius=18, fill=(16, 18, 28, 138))
    lines = wrap_text(draw, shot.dialogue_ko, FONT_DIALOGUE, WIDTH - 190)
    y = HEIGHT - 113
    for line in lines[:2]:
        draw.text((95, y), line, font=FONT_DIALOGUE, fill=(255, 248, 220, 255))
        y += 39

    # Tiny shot/frame ID for validation.
    timecode = f"{frame_idx // FPS // 60:02d}:{frame_idx // FPS % 60:02d}.{frame_idx % FPS}"
    draw.rounded_rectangle((22, 18, 268, 54), radius=12, fill=(0, 0, 0, 92))
    draw.text((36, 25), f"EP001  {timecode}  SH{shot.shot_id}", font=FONT_SMALL, fill=(238, 246, 255, 230))

    return Image.alpha_composite(rgba, overlay).convert("RGB")


def shot_for_frame(frame_idx: int) -> Shot:
    sec = frame_idx / FPS
    for shot in SHOTS:
        if shot.start <= sec < shot.end:
            return shot
    return SHOTS[-1]


def render_frames(images: dict[str, Path]) -> None:
    cache = {name: Image.open(path).convert("RGB") for name, path in images.items()}
    manifest_path = EXPORT / "frame_manifest_10fps.csv"
    with manifest_path.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["frame", "timecode", "shot_id", "keyframe", "action_ko", "dialogue_ko", "sfx_ko", "openart_prompt"])
        for idx in range(TOTAL_FRAMES):
            shot = shot_for_frame(idx)
            local_t = ((idx / FPS) - shot.start) / max(0.001, shot.end - shot.start)
            eased = local_t * local_t * (3 - 2 * local_t)
            zoom = shot.zoom0 + (shot.zoom1 - shot.zoom0) * eased + math.sin(idx * 0.041) * 0.004
            panx = shot.panx0 + (shot.panx1 - shot.panx0) * eased
            pany = shot.pany0 + (shot.pany1 - shot.pany0) * eased
            base = cover_image(cache[shot.image_name], zoom, panx, pany)
            base = ImageEnhance.Color(base).enhance(1.04)
            base = ImageEnhance.Contrast(base).enhance(1.03)
            frame = add_light_and_motion(base, idx, shot, local_t)
            frame = add_vignette(frame, 0.72)
            frame = add_labels(frame, shot, idx)
            out = FRAMES / f"frame_{idx + 1:06d}.jpg"
            frame.save(out, quality=90, optimize=True, progressive=True)
            tc = f"{idx // FPS // 60:02d}:{idx // FPS % 60:02d}.{idx % FPS}"
            writer.writerow([idx + 1, tc, shot.shot_id, shot.image_name, shot.action_ko, shot.dialogue_ko, shot.sfx_ko, shot.prompt])
            if (idx + 1) % 100 == 0:
                print(f"frames {idx + 1}/{TOTAL_FRAMES}")


def write_shot_docs() -> None:
    shotlist = EXPORT / "EP001_SHOTLIST_3MIN_KO.md"
    prompts = EXPORT / "OPENART_PROMPTS.md"
    voice = EXPORT / "VOICE_AND_SOUND_PLAN_KO.md"
    sfx = EXPORT / "sfx_cues.csv"

    with shotlist.open("w", encoding="utf-8") as f:
        f.write("# EP001 - 별빛 편의점 / 3분 10fps 전체 플랜\n\n")
        f.write("총 길이: 180초 / 10fps / 1800프레임. 대사는 모두 한국어 기준입니다.\n\n")
        for shot in SHOTS:
            f.write(f"## SH{shot.shot_id}  {shot.start:02d}s-{shot.end:02d}s  {shot.title_ko}\n")
            f.write(f"- 액션: {shot.action_ko}\n")
            f.write(f"- 대사: {shot.dialogue_ko}\n")
            f.write(f"- 사운드: {shot.sfx_ko}\n")
            f.write(f"- 키프레임: `{shot.image_name}`\n\n")

    with prompts.open("w", encoding="utf-8") as f:
        f.write("# OpenArt / image-to-video prompts - EP001\n\n")
        f.write("Global style: premium 3D soft plush children's animated series, Octonauts-level clean character appeal, Korean convenience store at rainy night, warm neon reflections, consistent Mochi white plush with crescent horns and glowing chest star, consistent Zumu blue plush with orange eyes, tiny forehead star and glowing comet tail. Natural childlike character acting, no adult voices, no robotic movement.\n\n")
        f.write("Negative prompt: geometric body, stick figure, broken limbs, detached legs, deformed face, warped Korean signs, scary expression, plastic toy shine, noisy flicker, random character redesign, adult face, stiff puppet motion, bad hands, duplicated eyes, low quality.\n\n")
        for shot in SHOTS:
            f.write(f"## SH{shot.shot_id} {shot.start:02d}s-{shot.end:02d}s\n")
            f.write(f"Use keyframe `{shot.image_name}`. {shot.prompt}. Action: {shot.action_ko} Dialogue mood: {shot.dialogue_ko}\n\n")

    with voice.open("w", encoding="utf-8") as f:
        f.write("# 목소리와 사운드 계획\n\n")
        f.write("로컬 기계 TTS는 사용하지 않습니다. 목소리는 ElevenLabs/OpenArt/전문 성우 녹음 중 하나로 별도 제작해야 합니다.\n\n")
        f.write("- 모치: 8-10세 느낌, 작고 따뜻한 목소리, 숨이 살짝 섞인 조심스러운 톤. 성인처럼 낮게 말하지 않음.\n")
        f.write("- 주무: 9-11세 느낌, 밝고 빠르지만 날카롭지 않은 목소리. 꼬리빛이 움직일 때 약한 반짝임을 동반.\n")
        f.write("- 감정 규칙: 겁남은 작게, 기쁨은 둥글게, 놀람은 짧게. 소리를 지르지 않음.\n")
        f.write("- 이번 로컬 프리뷰에는 나쁜 로봇 목소리를 넣지 않고, 발걸음/문/별빛 효과음만 낮게 넣습니다.\n\n")
        for shot in SHOTS:
            f.write(f"SH{shot.shot_id}: {shot.dialogue_ko}\n")

    with sfx.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["time_seconds", "shot_id", "cue_ko", "mix_note"])
        for shot in SHOTS:
            writer.writerow([shot.start, shot.shot_id, shot.sfx_ko, "low volume, soft, no harsh high frequency"])


def write_audio() -> Path:
    sr = 44100
    n = sr * SECONDS
    t = np.linspace(0, SECONDS, n, endpoint=False)
    audio = np.zeros(n, dtype=np.float32)
    # Soft rain bed.
    rng = np.random.default_rng(7)
    rain = rng.normal(0, 0.006, n).astype(np.float32)
    audio += rain
    # Gentle room hum.
    audio += 0.006 * np.sin(2 * np.pi * 110 * t)
    audio += 0.004 * np.sin(2 * np.pi * 220 * t)

    def add_tone(start: float, freq: float, dur: float, vol: float) -> None:
        s = int(start * sr)
        e = min(n, s + int(dur * sr))
        tt = np.linspace(0, dur, e - s, endpoint=False)
        env = np.sin(np.linspace(0, math.pi, e - s)) ** 2
        audio[s:e] += vol * np.sin(2 * np.pi * freq * tt) * env

    def add_step(start: float) -> None:
        s = int(start * sr)
        dur = int(0.12 * sr)
        e = min(n, s + dur)
        tt = np.linspace(0, 0.12, e - s, endpoint=False)
        env = np.exp(-tt * 28)
        audio[s:e] += 0.055 * np.sin(2 * np.pi * 95 * tt) * env

    for sec in [2.0, 3.1, 4.4, 12.0, 13.2, 14.3, 51.0, 51.6, 52.2, 53.0, 54.1, 55.0, 101.5, 103.0, 131.5]:
        add_step(sec)
    for sec in [20.4, 31.2, 42.0, 86.0, 96.5, 150.0, 166.0, 176.0]:
        add_tone(sec, 660, 0.42, 0.025)
        add_tone(sec + 0.08, 880, 0.36, 0.018)
    for sec in [30.0, 100.0, 150.0]:
        add_tone(sec, 440, 0.18, 0.020)

    audio = np.clip(audio, -0.75, 0.75)
    out = EXPORT / "ep001_soft_sfx.wav"
    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes((audio * 32767).astype("<i2").tobytes())
    return out


def render_video(audio_path: Path) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out = EXPORT / "ep001_full_10fps_animatic.mp4"
    pattern = str(FRAMES / "frame_%06d.jpg")
    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        pattern,
        "-i",
        str(audio_path),
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
        "128k",
        "-shortest",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def write_preview_html(video_path: Path) -> None:
    html = ROOT / "ep001_full_frames.html"
    sample = "\n".join(
        f'<a href="exports/ep001_full_frames_10fps/frames/frame_{i:06d}.jpg"><img src="exports/ep001_full_frames_10fps/frames/frame_{i:06d}.jpg" alt="frame {i}"></a>'
        for i in list(range(1, 31)) + [100, 200, 300, 450, 600, 750, 900, 1050, 1200, 1350, 1500, 1650, 1800]
    )
    html.write_text(
        f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mochi EP001 - 1800 frames</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #10141f; color: #f7f4e9; }}
    main {{ max-width: 1180px; margin: auto; padding: 28px; }}
    video {{ width: 100%; background: #000; border-radius: 8px; }}
    .links {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 18px 0 26px; }}
    .links a {{ color: #10141f; background: #ffe28a; padding: 10px 12px; border-radius: 6px; text-decoration: none; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 10px; }}
    .grid img {{ width: 100%; border-radius: 6px; display: block; }}
    h1 {{ font-size: 28px; margin: 0 0 14px; }}
    p {{ color: #d9dded; }}
  </style>
</head>
<body>
<main>
  <h1>Mochi EP001 - vidéo complète en 1800 frames</h1>
  <p>Export de validation: 3 minutes, 10 images/seconde, 1280x720. Les voix robotisées ne sont pas incluses; cette version garde seulement les ambiances, pas, porte et étoiles.</p>
  <video src="exports/ep001_full_frames_10fps/{video_path.name}" controls preload="metadata"></video>
  <div class="links">
    <a href="exports/ep001_full_frames_10fps/frames/">Ouvrir les 1800 frames</a>
    <a href="exports/ep001_full_frames_10fps/frame_manifest_10fps.csv">Manifeste frame par frame</a>
    <a href="exports/ep001_full_frames_10fps/EP001_SHOTLIST_3MIN_KO.md">Shotlist coréenne</a>
    <a href="exports/ep001_full_frames_10fps/OPENART_PROMPTS.md">Prompts OpenArt</a>
    <a href="exports/ep001_full_frames_10fps/VOICE_AND_SOUND_PLAN_KO.md">Plan voix/sons</a>
  </div>
  <div class="grid">
    {sample}
  </div>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    images = ensure_inputs()
    write_shot_docs()
    render_frames(images)
    audio = write_audio()
    video = render_video(audio)
    write_preview_html(video)
    print(f"done: {video}")
    print(f"frames: {FRAMES}")


if __name__ == "__main__":
    main()
