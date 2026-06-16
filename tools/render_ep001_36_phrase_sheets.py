from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "ep001_phrase_sheets_36"
SOURCE = EXPORT / "source_sheets"
POSES = EXPORT / "poses_360"
WIDTH = 1280
HEIGHT = 720


def crop_to_16x9(img: Image.Image) -> Image.Image:
    sw, sh = img.size
    ratio = WIDTH / HEIGHT
    if sw / sh > ratio:
        crop_h = sh
        crop_w = int(crop_h * ratio)
    else:
        crop_w = sw
        crop_h = int(crop_w / ratio)
    left = (sw - crop_w) // 2
    top = (sh - crop_h) // 2
    return img.crop((left, top, left + crop_w, top + crop_h)).resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def required_sheets() -> list[Path]:
    return [SOURCE / f"phrase_{i:02d}.png" for i in range(1, 37)]


def main() -> None:
    missing = [p.name for p in required_sheets() if not p.exists()]
    if missing:
        (EXPORT / "MISSING_SHEETS.txt").write_text("\n".join(missing) + "\n", encoding="utf-8")
        raise SystemExit(
            "Cannot render final 3-minute frame-by-frame episode yet. "
            f"{len(missing)} phrase sheets are missing. See {EXPORT / 'MISSING_SHEETS.txt'}"
        )

    POSES.mkdir(parents=True, exist_ok=True)
    for old in POSES.glob("*.jpg"):
        old.unlink()

    manifest = EXPORT / "poses_360_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["phrase", "pose", "source_sheet", "pose_file"])
        for phrase_idx, sheet_path in enumerate(required_sheets(), 1):
            sheet = Image.open(sheet_path).convert("RGB")
            sw, sh = sheet.size
            cell_w = sw / 5
            cell_h = sh / 2
            for row in range(2):
                for col in range(5):
                    pose = row * 5 + col + 1
                    panel = sheet.crop(
                        (
                            int(round(col * cell_w)),
                            int(round(row * cell_h)),
                            int(round((col + 1) * cell_w)),
                            int(round((row + 1) * cell_h)),
                        )
                    )
                    out = POSES / f"phrase_{phrase_idx:02d}_pose_{pose:02d}.jpg"
                    crop_to_16x9(panel).save(out, quality=93, optimize=True, progressive=True)
                    writer.writerow([phrase_idx, pose, sheet_path.name, out.name])
    print(f"Rendered 360 poses to {POSES}")


if __name__ == "__main__":
    main()
