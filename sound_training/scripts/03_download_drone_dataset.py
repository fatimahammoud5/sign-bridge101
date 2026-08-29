from pathlib import Path
import json
import urllib.request
import urllib.parse
import time


OWNER = "saraalemadi"
REPO = "DroneAudioDataset"
BRANCH = "master"

DRONE_SOURCE = "Binary_Drone_Audio/yes_drone"
UNKNOWN_SOURCE = "Binary_Drone_Audio/unknown"

DRONE_LIMIT = 200
UNKNOWN_LIMIT = 300

BASE_DIR = Path(__file__).resolve().parent.parent

DRONE_OUTPUT = BASE_DIR / "dataset" / "drone"
UNKNOWN_OUTPUT = BASE_DIR / "dataset" / "other"

API_BASE = (
    f"https://api.github.com/repos/"
    f"{OWNER}/{REPO}/contents/"
)

RAW_BASE = (
    f"https://raw.githubusercontent.com/"
    f"{OWNER}/{REPO}/{BRANCH}/"
)

AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
}


def make_request(url, retries=5):
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "SignBridge-Dataset-Downloader",
                    "Accept": "application/vnd.github+json",
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=120,
            ) as response:
                return response.read()

        except Exception as error:
            print(
                f"Request failed "
                f"(attempt {attempt}/{retries})"
            )
            print(error)

            if attempt == retries:
                raise

            print("Retrying in 3 seconds...")
            time.sleep(3)


def get_folder_files(folder_path):
    print()
    print("=" * 70)
    print(f"READING FOLDER: {folder_path}")
    print("=" * 70)

    encoded_path = urllib.parse.quote(
        folder_path,
        safe="/",
    )

    url = (
        API_BASE
        + encoded_path
        + f"?ref={BRANCH}"
    )

    raw_data = make_request(url)

    data = json.loads(
        raw_data.decode("utf-8")
    )

    if not isinstance(data, list):
        raise RuntimeError(
            "GitHub did not return a folder listing."
        )

    files = []

    for item in data:
        if item.get("type") != "file":
            continue

        name = item.get("name", "")

        suffix = Path(name).suffix.lower()

        if suffix not in AUDIO_EXTENSIONS:
            continue

        files.append(
            {
                "name": name,
                "path": item.get("path"),
                "download_url": item.get("download_url"),
            }
        )

    files.sort(
        key=lambda item: item["name"]
    )

    print(
        f"Audio files visible through API: "
        f"{len(files)}"
    )

    return files


def download_file(
    file_info,
    output_directory,
    index,
    total,
):
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = file_info["name"]

    destination = (
        output_directory
        / filename
    )

    if (
        destination.exists()
        and destination.stat().st_size > 0
    ):
        print(
            f"[{index:03d}/{total:03d}] "
            f"SKIP   {filename}"
        )
        return True

    url = file_info.get(
        "download_url"
    )

    if not url:
        encoded_path = urllib.parse.quote(
            file_info["path"],
            safe="/",
        )

        url = (
            RAW_BASE
            + encoded_path
        )

    try:
        data = make_request(
            url,
            retries=3,
        )

        if not data:
            raise ValueError(
                "Downloaded file is empty."
            )

        destination.write_bytes(
            data
        )

        size_kb = len(data) / 1024

        print(
            f"[{index:03d}/{total:03d}] "
            f"OK     {filename} "
            f"({size_kb:.1f} KB)"
        )

        return True

    except Exception as error:
        print(
            f"[{index:03d}/{total:03d}] "
            f"FAILED {filename}"
        )

        print(
            f"          {error}"
        )

        return False


def download_group(
    files,
    output_directory,
    group_name,
    limit,
):
    selected = files[:limit]

    print()
    print("=" * 70)
    print(f"DOWNLOADING: {group_name}")
    print("=" * 70)

    print(
        f"Available: {len(files)}"
    )

    print(
        f"Selected : {len(selected)}"
    )

    successful = 0
    failed = 0

    total = len(selected)

    for index, file_info in enumerate(
        selected,
        start=1,
    ):
        ok = download_file(
            file_info=file_info,
            output_directory=output_directory,
            index=index,
            total=total,
        )

        if ok:
            successful += 1
        else:
            failed += 1

        time.sleep(0.10)

    return successful, failed


def main():
    print("=" * 70)
    print("SIGNBRIDGE - DRONE DATASET DOWNLOADER V2")
    print("=" * 70)

    DRONE_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    UNKNOWN_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        drone_files = get_folder_files(
            DRONE_SOURCE
        )

        unknown_files = get_folder_files(
            UNKNOWN_SOURCE
        )

    except Exception as error:
        print()
        print(
            "ERROR: could not read "
            "GitHub folder."
        )

        print(error)

        return

    print()
    print("=" * 70)
    print("DOWNLOAD PLAN")
    print("=" * 70)

    print(
        f"Drone target : {DRONE_LIMIT}"
    )

    print(
        f"Other target : {UNKNOWN_LIMIT}"
    )

    drone_success, drone_failed = (
        download_group(
            files=drone_files,
            output_directory=DRONE_OUTPUT,
            group_name="DRONE",
            limit=DRONE_LIMIT,
        )
    )

    unknown_success, unknown_failed = (
        download_group(
            files=unknown_files,
            output_directory=UNKNOWN_OUTPUT,
            group_name="UNKNOWN / OTHER",
            limit=UNKNOWN_LIMIT,
        )
    )

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print(
        f"Drone successful : "
        f"{drone_success}"
    )

    print(
        f"Drone failed     : "
        f"{drone_failed}"
    )

    print(
        f"Other successful : "
        f"{unknown_success}"
    )

    print(
        f"Other failed     : "
        f"{unknown_failed}"
    )

    print()
    print(
        "Drone folder:"
    )
    print(DRONE_OUTPUT)

    print()
    print(
        "Other folder:"
    )
    print(UNKNOWN_OUTPUT)

    print("=" * 70)


if __name__ == "__main__":
    main()