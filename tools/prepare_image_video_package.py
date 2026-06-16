from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports" / "elevenlabs_ep001_image_video"
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int):
    for path in ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


SHOTS = [
    {
        "id": "01",
        "src": "assets/pilot_ep001/ep001_01_establishing.png",
        "name": "01_convenience_store_establishing.png",
        "duration": "6-8s",
        "prompt": "Locked wide shot. Mochi stands outside a Korean night convenience store on wet pavement. Only animate gentle breathing, glowing belly star pulsing softly, tiny star particles drifting, neon reflections shimmering. Do not move limbs dramatically. Preserve Mochi's face, horns, plush texture and proportions exactly."
    },
    {
        "id": "02",
        "src": "assets/pilot_ep001/ep001_02_door_incident.png",
        "name": "02_door_incident.png",
        "duration": "6-8s",
        "prompt": "Mochi notices a small trapped starlight near the automatic glass door. Animate Mochi's eyes shifting first, then a small head tilt, belly star dim pulse, automatic door sensor light scanning left to right. Keep character identity stable and limbs connected."
    },
    {
        "id": "03",
        "src": "assets/pilot_ep001/ep001_03_chase.png",
        "name": "03_zumu_attempt.png",
        "duration": "6-8s",
        "prompt": "Zumu floats in quickly but gently, glowing comet tail trailing sparkles. Mochi reacts with concern. Animate Zumu tail wave and sparkle trail, Mochi small step back, automatic door reflection flicker. No warping, no disconnected body parts."
    },
    {
        "id": "04",
        "src": "assets/pilot_ep001/ep001_04_emotional_beat.png",
        "name": "04_emotional_pause.png",
        "duration": "6-8s",
        "prompt": "Quiet emotional close-up. Mochi stops trying to grab the starlight and breathes slowly. Animate subtle chest breathing, sad eyebrow change, belly star fading then warming. Zumu hovers quietly with tail glow dimmed. Soft Korean convenience store background remains stable."
    },
    {
        "id": "05",
        "src": "assets/pilot_ep001/ep001_05_resolution.png",
        "name": "05_resolution.png",
        "duration": "6-8s",
        "prompt": "Mochi waits with open palm while Zumu keeps a gentle rhythm. Animate starlight moving by itself toward Mochi's hand, Zumu tail sparkles flowing, door light syncing softly. Characters must keep plush 3D shape, exact face, connected legs and arms."
    },
]

GLOBAL_PROMPT = """Korean children's animated series, 3D soft plush render, Octonauts-like gentle quality.
Characters: Mochi is a white plush moon creature with crescent horns, glowing belly star, brown-orange eyes, rosy cheeks. Zumu is a blue plush comet creature with orange eyes and glowing comet tail.
Setting: Korean night convenience store, wet street reflections, warm neon, no real brand logos.
Preserve character identity, proportions, plush texture, facial features and lighting across every clip.
Avoid: warped face, extra limbs, disconnected legs, rubber body, scary mood, adult human characters, logo text, unreadable text artifacts, camera shake."""


def make_contact_sheet() -> None:
    thumbs = []
    for shot in SHOTS:
        img = Image.open(ROOT / shot["src"]).convert("RGB")
        img.thumbnail((420, 236), Image.Resampling.LANCZOS)
        card = Image.new("RGB", (460, 310), (15, 20, 32))
        card.paste(img, (20, 20))
        d = ImageDraw.Draw(card)
        d.text((20, 266), f"SHOT {shot['id']} - {shot['duration']}", font=font(22), fill=(255, 247, 232))
        thumbs.append(card)
    sheet = Image.new("RGB", (920, 930), (7, 8, 18))
    for i, card in enumerate(thumbs):
        sheet.paste(card, ((i % 2) * 460, (i // 2) * 310))
    sheet.save(OUT / "ep001_shot_contact_sheet.png")


def main() -> None:
    for shot in SHOTS:
        shutil.copy2(ROOT / shot["src"], OUT / shot["name"])
    shutil.copy2(ROOT / "assets" / "characters" / "mochi_reference.png", OUT / "character_reference_mochi.png")
    shutil.copy2(ROOT / "assets" / "characters" / "zumu_reference.png", OUT / "character_reference_zumu.png")
    make_contact_sheet()

    lines = ["# ElevenLabs image-to-video package - Mochi EP001", "", "## Global constraints", GLOBAL_PROMPT, ""]
    for shot in SHOTS:
        lines.extend([
            f"## Shot {shot['id']}",
            f"Image: `{shot['name']}`",
            f"Duration: {shot['duration']}",
            "",
            "Prompt:",
            shot["prompt"],
            "",
            "Negative prompt:",
            "warped face, floating limbs, disconnected legs, extra arms, extra eyes, melted plush, logo text, scary mood, realistic human, fast camera shake",
            "",
        ])
    (OUT / "PROMPTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
