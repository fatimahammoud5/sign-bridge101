from __future__ import annotations

import math
import shutil
import sys

from pathlib import Path

import cv2
import yt_dlp


# ============================================================
# PATHS
# ============================================================

# sign_bridge/backend
BACKEND_ROOT = Path(__file__).resolve().parent

# Original OpenASL-related downloads
OPENASL_ROOT = (
    BACKEND_ROOT
    / "education_source"
    / "OpenASL"
)

RAW_VIDEO_DIR = (
    OPENASL_ROOT
    / "raw_selected_videos"
)

# Final clips used by Flutter / Education API
EDUCATION_VIDEO_DIR = (
    BACKEND_ROOT
    / "education_data"
    / "videos"
)


# ============================================================
# SELECTED OPENASL LEVEL 1 SENTENCES
# ============================================================

SELECTED_SENTENCES = [
    {
        "lesson": 1,

        "sentence":
            "My name is Cayden.",

        "yid":
            "0KcUZlotmlo",

        "start":
            "00:11:57.360",

        "end":
            "00:12:00.360",

        "output":
            "l1_01_my_name_cayden.mp4",
    },

    {
        "lesson": 2,

        "sentence":
            "Hello, what's your name?",

        "yid":
            "fNT8a6e1gx8",

        "start":
            "00:04:20.100",

        "end":
            "00:04:21.233",

        "output":
            "l1_02_whats_your_name.mp4",
    },

    {
        "lesson": 3,

        "sentence":
            "Nice to meet you!",

        "yid":
            "jFh4BZRJLRI",

        "start":
            "00:01:45.599",

        "end":
            "00:01:47.799",

        "output":
            "l1_03_nice_to_meet_you.mp4",
    },

    {
        "lesson": 4,

        "sentence":
            "I am deaf.",

        "yid":
            "A0TqKW_XJZg",

        "start":
            "00:07:14.079",

        "end":
            "00:07:16.000",

        "output":
            "l1_04_i_am_deaf.mp4",
    },

    {
        "lesson": 5,

        "sentence":
            "I live in Texas.",

        "yid":
            "e1ufQQzu6Xw",

        "start":
            "00:00:16.518",

        "end":
            "00:00:22.995",

        "output":
            "l1_05_i_live_in_texas.mp4",
    },

    {
        "lesson": 6,

        "sentence":
            "Where are you from?",

        "yid":
            "0KcUZlotmlo",

        "start":
            "00:09:49.080",

        "end":
            "00:09:50.159",

        "output":
            "l1_06_where_are_you_from.mp4",
    },
]


# ============================================================
# SETTINGS
# ============================================================

# Maximum source quality.
# 720p is more than enough for our Education cards.
MAX_HEIGHT = 720

# We intentionally do not include audio in final clips.
# The Education feature teaches visual ASL.
OUTPUT_FOURCC = "mp4v"


# ============================================================
# HELPERS
# ============================================================

def time_to_seconds(
    value: str,
) -> float:
    """
    Convert:
        00:11:57.360

    into seconds.
    """

    parts = value.strip().split(":")

    if len(parts) != 3:
        raise ValueError(
            f"Invalid timestamp: {value}"
        )

    hours = float(
        parts[0]
    )

    minutes = float(
        parts[1]
    )

    seconds = float(
        parts[2]
    )

    return (
        hours * 3600
        + minutes * 60
        + seconds
    )


def find_downloaded_source(
    yid: str,
) -> Path | None:
    """
    Locate any source video that yt-dlp successfully downloaded.
    """

    allowed_extensions = [
        ".mp4",
        ".webm",
        ".mkv",
        ".mov",
    ]

    for extension in allowed_extensions:
        candidate = (
            RAW_VIDEO_DIR
            / f"{yid}{extension}"
        )

        if candidate.exists():
            return candidate

    # General fallback.
    matches = list(
        RAW_VIDEO_DIR.glob(
            f"{yid}.*"
        )
    )

    for match in matches:
        if (
            match.is_file()
            and match.suffix.lower()
            in allowed_extensions
        ):
            return match

    return None


# ============================================================
# DOWNLOAD SOURCE VIDEO
# ============================================================

def download_source_video(
    yid: str,
) -> Path | None:
    """
    Download only one original YouTube video.

    We first check whether it has already been downloaded,
    so rerunning this script does not unnecessarily download
    the same video again.
    """

    existing = (
        find_downloaded_source(
            yid
        )
    )

    if existing is not None:
        print(
            f"[FOUND] Existing source: "
            f"{existing.name}"
        )

        return existing

    url = (
        "https://www.youtube.com/watch?v="
        + yid
    )

    output_template = str(
        RAW_VIDEO_DIR
        / "%(id)s.%(ext)s"
    )

    print()
    print(
        f"[DOWNLOAD] {yid}"
    )

    print(
        f"URL: {url}"
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # We prefer a single already-combined MP4 format.
    #
    # This avoids requiring a separate FFmpeg installation
    # just to merge video + audio streams.
    #
    # Audio is not needed for the final ASL clips.
    # --------------------------------------------------------

    options = {
        "outtmpl":
            output_template,

        "noplaylist":
            True,

        "quiet":
            False,

        "no_warnings":
            False,

        "retries":
            5,

        "fragment_retries":
            5,

        "format": (
            f"best[ext=mp4]"
            f"[height<=?{MAX_HEIGHT}]"
            f"/best[height<=?{MAX_HEIGHT}]"
            f"/best"
        ),
    }

    try:
        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download(
                [url]
            )

    except Exception as error:
        print()
        print(
            "[DOWNLOAD FAILED]"
        )

        print(
            f"Video: {yid}"
        )

        print(
            f"Reason: {error}"
        )

        return None

    downloaded = (
        find_downloaded_source(
            yid
        )
    )

    if downloaded is None:
        print(
            "[ERROR] yt-dlp finished "
            "but source file was not found."
        )

        return None

    print(
        "[OK] Downloaded:"
    )

    print(
        downloaded
    )

    return downloaded


# ============================================================
# VALIDATE SOURCE VIDEO
# ============================================================

def validate_source_video(
    video_path: Path,
) -> bool:

    capture = cv2.VideoCapture(
        str(video_path)
    )

    try:
        if not capture.isOpened():
            return False

        frame_count = int(
            capture.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        fps = float(
            capture.get(
                cv2.CAP_PROP_FPS
            )
        )

        width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        if frame_count <= 0:
            return False

        if fps <= 0:
            return False

        if width <= 0:
            return False

        if height <= 0:
            return False

        return True

    finally:
        capture.release()


# ============================================================
# TRIM OPENASL CLIP
# ============================================================

def trim_clip(
    source_path: Path,
    start_time: str,
    end_time: str,
    output_path: Path,
) -> bool:

    start_seconds = (
        time_to_seconds(
            start_time
        )
    )

    end_seconds = (
        time_to_seconds(
            end_time
        )
    )

    if (
        end_seconds
        <= start_seconds
    ):
        print(
            "[ERROR] Invalid clip duration."
        )

        return False

    capture = cv2.VideoCapture(
        str(source_path)
    )

    if not capture.isOpened():
        print(
            f"[ERROR] Could not open "
            f"{source_path}"
        )

        capture.release()

        return False

    try:
        fps = float(
            capture.get(
                cv2.CAP_PROP_FPS
            )
        )

        width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        if (
            not math.isfinite(fps)
            or fps <= 1
            or fps > 240
        ):
            fps = 30.0

        if width <= 0 or height <= 0:
            print(
                "[ERROR] Invalid video dimensions."
            )

            return False

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # Seek to OpenASL start timestamp.
        # ----------------------------------------------------

        capture.set(
            cv2.CAP_PROP_POS_MSEC,
            start_seconds * 1000.0,
        )

        fourcc = cv2.VideoWriter_fourcc(
            *OUTPUT_FOURCC
        )

        writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            fps,
            (
                width,
                height,
            ),
        )

        if not writer.isOpened():
            print(
                "[ERROR] Could not create output MP4."
            )

            writer.release()

            return False

        frames_written = 0

        try:
            while True:
                current_msec = capture.get(
                    cv2.CAP_PROP_POS_MSEC
                )

                current_seconds = (
                    current_msec
                    / 1000.0
                )

                if (
                    current_seconds
                    >= end_seconds
                ):
                    break

                success, frame = (
                    capture.read()
                )

                if not success:
                    break

                if frame is None:
                    continue

                writer.write(
                    frame
                )

                frames_written += 1

        finally:
            writer.release()

        if frames_written <= 0:
            print(
                "[ERROR] No frames were written."
            )

            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    pass

            return False

        # ----------------------------------------------------
        # Validate output
        # ----------------------------------------------------

        verify = cv2.VideoCapture(
            str(output_path)
        )

        try:
            if not verify.isOpened():
                print(
                    "[ERROR] Output clip cannot be opened."
                )

                return False

            output_frames = int(
                verify.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )
            )

            if output_frames <= 0:
                print(
                    "[ERROR] Output clip contains no frames."
                )

                return False

        finally:
            verify.release()

        return True

    finally:
        capture.release()


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 76)
    print(
        "SIGNBRIDGE - OPENASL LEVEL 1 DOWNLOADER"
    )
    print("=" * 76)

    print()
    print("Raw OpenASL sources:")
    print(RAW_VIDEO_DIR)

    print()
    print("Education output:")
    print(EDUCATION_VIDEO_DIR)

    print()

    RAW_VIDEO_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    EDUCATION_VIDEO_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # UNIQUE SOURCE VIDEOS
    # ========================================================

    unique_yids = []

    for lesson in SELECTED_SENTENCES:
        yid = lesson["yid"]

        if yid not in unique_yids:
            unique_yids.append(
                yid
            )

    print(
        f"Selected lessons : "
        f"{len(SELECTED_SENTENCES)}"
    )

    print(
        f"Source videos    : "
        f"{len(unique_yids)}"
    )

    print()

    # ========================================================
    # DOWNLOAD ONLY NEEDED SOURCES
    # ========================================================

    sources = {}

    for index, yid in enumerate(
        unique_yids,
        start=1,
    ):
        print()
        print("=" * 76)

        print(
            f"SOURCE {index}/{len(unique_yids)}"
        )

        print("=" * 76)

        source = (
            download_source_video(
                yid
            )
        )

        if source is None:
            sources[yid] = None
            continue

        if not validate_source_video(
            source
        ):
            print(
                "[ERROR] Source video is invalid."
            )

            sources[yid] = None

            continue

        sources[yid] = source

    # ========================================================
    # CREATE FINAL CLIPS
    # ========================================================

    print()
    print()
    print("=" * 76)
    print(
        "CREATING EDUCATION CLIPS"
    )
    print("=" * 76)

    successful = []

    failed = []

    for lesson in SELECTED_SENTENCES:

        print()
        print("-" * 76)

        print(
            f"LESSON {lesson['lesson']}"
        )

        print(
            f"Sentence: "
            f"{lesson['sentence']}"
        )

        print(
            f"YID     : "
            f"{lesson['yid']}"
        )

        print(
            f"Start   : "
            f"{lesson['start']}"
        )

        print(
            f"End     : "
            f"{lesson['end']}"
        )

        source = sources.get(
            lesson["yid"]
        )

        if source is None:
            print(
                "[SKIP] Source was not downloaded."
            )

            failed.append(
                lesson
            )

            continue

        output_path = (
            EDUCATION_VIDEO_DIR
            / lesson["output"]
        )

        print(
            f"Output  : "
            f"{output_path.name}"
        )

        success = trim_clip(
            source_path=source,

            start_time=(
                lesson["start"]
            ),

            end_time=(
                lesson["end"]
            ),

            output_path=(
                output_path
            ),
        )

        if success:
            print(
                "[SUCCESS] Clip created."
            )

            successful.append(
                lesson
            )

        else:
            print(
                "[FAILED] Could not create clip."
            )

            failed.append(
                lesson
            )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print()
    print("=" * 76)
    print(
        "OPENASL LEVEL 1 RESULT"
    )
    print("=" * 76)

    print()
    print(
        f"Requested clips : "
        f"{len(SELECTED_SENTENCES)}"
    )

    print(
        f"Created clips   : "
        f"{len(successful)}"
    )

    print(
        f"Failed clips    : "
        f"{len(failed)}"
    )

    print()

    if successful:
        print(
            "SUCCESSFUL:"
        )

        for lesson in successful:
            print(
                f"  [OK] "
                f"{lesson['sentence']}"
            )

            print(
                f"       "
                f"{lesson['output']}"
            )

    if failed:
        print()
        print(
            "FAILED:"
        )

        for lesson in failed:
            print(
                f"  [X] "
                f"{lesson['sentence']}"
            )

            print(
                f"      YID: "
                f"{lesson['yid']}"
            )

    print()
    print(
        "Final Education videos:"
    )

    print(
        EDUCATION_VIDEO_DIR
    )

    print()
    print("=" * 76)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()