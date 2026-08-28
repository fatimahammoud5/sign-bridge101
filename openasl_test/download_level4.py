import os
import sys
import subprocess
from pathlib import Path

# ============================================================
# LEVEL 4 - ANIMALS
# Downloads the YouTube source, verifies it, then cuts clips.
# ============================================================

VIDEO_URL = "https://youtu.be/fN4baaByX9A?si=AAMmWEO6wflrCGzM"

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

SOURCE = BASE_DIR / "level4_source.mp4"

LEARN_DIR = (
    PROJECT_DIR
    / "assets"
    / "videos"
    / "education"
    / "level4"
    / "learn"
)

PREDICT_DIR = (
    PROJECT_DIR
    / "assets"
    / "videos"
    / "education"
    / "level4"
    / "predict"
)

COOKIES = BASE_DIR / "cookies.txt"

FFMPEG = (
    Path(os.environ.get("LOCALAPPDATA", ""))
    / "Microsoft"
    / "WinGet"
    / "Links"
    / "ffmpeg.exe"
)

# ------------------------------------------------------------
# Clips
# start and duration
# ------------------------------------------------------------

LEARN_CLIPS = [
    (
        "favorite_animal.mp4",
        "00:05:01.000",
        "00:00:24.000",
    ),
    (
        "birds_on_my_walk.mp4",
        "00:05:25.000",
        "00:00:25.000",
    ),
    (
        "lion_at_the_zoo.mp4",
        "00:05:50.000",
        "00:00:35.000",
    ),
]

PREDICT_CLIPS = [
    (
        "cat.mp4",
        "00:01:57.000",
        "00:00:07.000",
    ),
    (
        "dog.mp4",
        "00:02:45.000",
        "00:00:07.000",
    ),
    (
        "fish.mp4",
        "00:03:30.000",
        "00:00:08.000",
    ),
]


def run(command):
    print()
    print("=" * 70)
    print("RUNNING:")
    print(" ".join(str(x) for x in command))
    print("=" * 70)

    return subprocess.run(command)


def delete_old_source():
    patterns = [
        "level4_source.mp4",
        "level4_source.mp4.part",
        "level4_source.f*.mp4",
        "level4_source.f*.m4a",
        "level4_source.webm",
    ]

    for pattern in patterns:
        for path in BASE_DIR.glob(pattern):
            try:
                path.unlink()
                print(f"Deleted old file: {path.name}")
            except Exception:
                pass


def check_ffmpeg():
    if not FFMPEG.exists():
        print()
        print("[ERROR] FFmpeg was not found here:")
        print(FFMPEG)
        print()
        sys.exit(1)

    result = subprocess.run(
        [str(FFMPEG), "-version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if result.returncode != 0:
        print("[ERROR] FFmpeg cannot run.")
        sys.exit(1)

    print("[OK] FFmpeg found.")


def verify_video(path):
    if not path.exists():
        return False

    size = path.stat().st_size

    print()
    print(f"Checking: {path.name}")
    print(f"Size: {size / 1024 / 1024:.2f} MB")

    # A 6+ minute source of this type should not be a few hundred KB.
    if size < 2_000_000:
        print("[BAD] File is suspiciously small.")
        return False

    result = subprocess.run(
        [
            str(FFMPEG),
            "-v",
            "error",
            "-i",
            str(path),
            "-f",
            "null",
            "-",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        print("[BAD] FFmpeg found an error:")
        print(result.stderr.strip())
        return False

    print("[OK] Video is valid.")
    return True


def download_attempt(name, extra_args):
    print()
    print("#" * 70)
    print(f"DOWNLOAD METHOD: {name}")
    print("#" * 70)

    delete_old_source()

    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--js-runtimes",
        "node",
        "--remote-components",
        "ejs:github",
        "--no-playlist",
        "--force-overwrites",
    ]

    if COOKIES.exists():
        command += [
            "--cookies",
            str(COOKIES),
        ]

    command += extra_args

    command += [
        VIDEO_URL,
        "-o",
        str(SOURCE),
    ]

    result = run(command)

    if result.returncode != 0:
        print(f"[FAILED] {name}")
        return False

    return verify_video(SOURCE)


def download_source():
    methods = [
        (
            "METHOD 1 - Default yt-dlp",
            [
                "-f",
                "best[ext=mp4][height<=720]/best[height<=720]/best",
            ],
        ),

        (
            "METHOD 2 - mweb + PO provider",
            [
                "--extractor-args",
                "youtube:player_client=mweb",
                "-f",
                "best[ext=mp4][height<=720]/best",
            ],
        ),

        (
            "METHOD 3 - web_safari HLS",
            [
                "--extractor-args",
                "youtube:player_client=web_safari",
                "-f",
                "best[protocol^=m3u8][height<=720]/best[protocol^=m3u8]",
            ],
        ),
    ]

    for name, args in methods:
        if download_attempt(name, args):
            print()
            print("=" * 70)
            print("SOURCE DOWNLOAD SUCCESSFUL")
            print("=" * 70)
            return True

    return False


def cut_clip(start, duration, output):
    output.parent.mkdir(parents=True, exist_ok=True)

    command = [
        str(FFMPEG),
        "-y",

        "-ss",
        start,

        "-i",
        str(SOURCE),

        "-t",
        duration,

        "-c:v",
        "libx264",

        "-preset",
        "fast",

        "-crf",
        "22",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-movflags",
        "+faststart",

        str(output),
    ]

    result = run(command)

    if result.returncode != 0:
        print()
        print(f"[ERROR] Failed to create {output.name}")
        return False

    if not output.exists() or output.stat().st_size < 10_000:
        print()
        print(f"[ERROR] Output looks invalid: {output.name}")
        return False

    print()
    print(f"[OK] Created: {output.name}")

    return True


def create_all_clips():
    LEARN_DIR.mkdir(parents=True, exist_ok=True)
    PREDICT_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 70)
    print("CREATING LEARN CLIPS")
    print("=" * 70)

    for filename, start, duration in LEARN_CLIPS:
        if not cut_clip(
            start,
            duration,
            LEARN_DIR / filename,
        ):
            return False

    print()
    print("=" * 70)
    print("CREATING CAN YOU GUESS CLIPS")
    print("=" * 70)

    for filename, start, duration in PREDICT_CLIPS:
        if not cut_clip(
            start,
            duration,
            PREDICT_DIR / filename,
        ):
            return False

    return True


def print_result():
    print()
    print("=" * 70)
    print("LEVEL 4 COMPLETED")
    print("=" * 70)

    print()
    print("LEARN:")
    for file in LEARN_DIR.glob("*.mp4"):
        print(
            f"  {file.name:<35} "
            f"{file.stat().st_size / 1024 / 1024:.2f} MB"
        )

    print()
    print("CAN YOU GUESS:")
    for file in PREDICT_DIR.glob("*.mp4"):
        print(
            f"  {file.name:<35} "
            f"{file.stat().st_size / 1024 / 1024:.2f} MB"
        )

    print()
    print("Expected structure:")
    print()
    print("level4/learn/")
    print("  favorite_animal.mp4")
    print("  birds_on_my_walk.mp4")
    print("  lion_at_the_zoo.mp4")
    print()
    print("level4/predict/")
    print("  cat.mp4")
    print("  dog.mp4")
    print("  fish.mp4")


def main():
    print("=" * 70)
    print("SIGNBRIDGE - LEVEL 4 VIDEO BUILDER")
    print("=" * 70)

    check_ffmpeg()

    if verify_video(SOURCE):
        print()
        print("Existing level4_source.mp4 is valid.")
        print("No download needed.")
    else:
        print()
        print("A valid Level 4 source was not found.")
        print("Starting automatic download...")

        if not download_source():
            print()
            print("=" * 70)
            print("DOWNLOAD FAILED")
            print("=" * 70)
            print()
            print(
                "All automatic YouTube download methods were blocked."
            )
            print(
                "Do NOT continue trying random formats."
            )
            print()
            sys.exit(2)

    if not create_all_clips():
        print()
        print("[ERROR] Clip creation failed.")
        sys.exit(3)

    print_result()


if __name__ == "__main__":
    main()