from __future__ import annotations

import string
import time
from pathlib import Path

import requests

BACKEND_ROOT = Path(__file__).resolve().parent
LETTERS_DIR = BACKEND_ROOT / "dictionary_data" / "letters"
LETTERS_DIR.mkdir(parents=True, exist_ok=True)

API = "https://commons.wikimedia.org/w/api.php"
WIDTH = 700
HEADERS = {
    "User-Agent": "SignBridge-Capstone/1.0 (educational ASL dictionary project)"
}


def get_thumb_url(session: requests.Session, letter: str) -> str:
    title = f"File:Sign language {letter}.svg"
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": WIDTH,
        "titles": title,
    }
    response = session.get(API, params=params, timeout=45)
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        raise RuntimeError(f"Wikimedia file not found: {title}")
    info = pages[0].get("imageinfo", [])
    if not info:
        raise RuntimeError(f"No image information for {title}")
    url = info[0].get("thumburl")
    if not url:
        raise RuntimeError(f"No PNG thumbnail URL for {title}")
    return url


def valid_png(path: Path) -> bool:
    try:
        if not path.exists() or path.stat().st_size < 1000:
            return False
        return path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    except Exception:
        return False


def download_one(session: requests.Session, letter: str) -> Path:
    destination = LETTERS_DIR / f"{letter.lower()}.png"
    if valid_png(destination):
        print(f"[{letter}] EXISTS  {destination.name}")
        return destination

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            print(f"[{letter}] downloading (attempt {attempt}/3)...")
            url = get_thumb_url(session, letter)
            response = session.get(url, timeout=60)
            response.raise_for_status()
            destination.write_bytes(response.content)
            if not valid_png(destination):
                destination.unlink(missing_ok=True)
                raise RuntimeError("Downloaded file is not a valid PNG")
            print(f"[{letter}] OK      {destination.name} ({destination.stat().st_size / 1024:.1f} KB)")
            return destination
        except Exception as exc:
            last_error = exc
            destination.unlink(missing_ok=True)
            time.sleep(1.5 * attempt)

    raise RuntimeError(str(last_error))


def main() -> None:
    print("=" * 72)
    print("SIGNBRIDGE - REPAIR ASL LETTER IMAGES")
    print("=" * 72)
    print("Folder:", LETTERS_DIR)
    print("Existing valid PNG files are kept; only missing/broken files are downloaded.")
    print()

    session = requests.Session()
    session.headers.update(HEADERS)

    failed: list[tuple[str, str]] = []
    for letter in string.ascii_uppercase:
        try:
            download_one(session, letter)
        except Exception as exc:
            failed.append((letter, str(exc)))
            print(f"[{letter}] FAILED  {exc}")

    valid_letters = [
        letter
        for letter in string.ascii_uppercase
        if valid_png(LETTERS_DIR / f"{letter.lower()}.png")
    ]
    missing = [letter for letter in string.ascii_uppercase if letter not in valid_letters]

    print()
    print("=" * 72)
    print("RESULT")
    print("=" * 72)
    print(f"Valid images : {len(valid_letters)}/26")
    print(f"Missing      : {len(missing)}")
    if missing:
        print("Missing letters:", ", ".join(missing))
    print("=" * 72)


if __name__ == "__main__":
    main()