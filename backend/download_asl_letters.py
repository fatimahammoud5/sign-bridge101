from __future__ import annotations

import string
from pathlib import Path

import requests


# ============================================================
# SETTINGS
# ============================================================

BACKEND_ROOT = Path(__file__).resolve().parent

LETTERS_DIR = (
    BACKEND_ROOT
    / "dictionary_data"
    / "letters"
)

LETTERS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


WIKIMEDIA_API = (
    "https://commons.wikimedia.org/w/api.php"
)

IMAGE_WIDTH = 700


HEADERS = {
    "User-Agent": (
        "SignBridge-Capstone/1.0 "
        "(educational ASL dictionary project)"
    ),
}


# ============================================================
# GET PNG URL
# ============================================================

def get_png_url(letter: str) -> tuple[str, str]:
    """
    Finds the Wikimedia Commons file:

        Sign language A.svg
        Sign language B.svg
        ...
        Sign language Z.svg

    and asks Wikimedia for a rendered PNG thumbnail.
    """

    title = (
        f"File:Sign language {letter}.svg"
    )

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": IMAGE_WIDTH,
        "titles": title,
    }

    response = requests.get(
        WIKIMEDIA_API,
        params=params,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    pages = (
        data
        .get("query", {})
        .get("pages", [])
    )

    if not pages:
        raise RuntimeError(
            f"No Wikimedia page found for {letter}"
        )

    page = pages[0]

    if page.get("missing"):
        raise RuntimeError(
            f"Image does not exist for {letter}"
        )

    image_info = page.get(
        "imageinfo",
        [],
    )

    if not image_info:
        raise RuntimeError(
            f"No image information for {letter}"
        )

    info = image_info[0]

    # For SVG files, requesting iiurlwidth normally
    # gives us a rendered PNG thumbnail.
    image_url = (
        info.get("thumburl")
        or info.get("url")
    )

    if not image_url:
        raise RuntimeError(
            f"No download URL for {letter}"
        )

    description_url = (
        info.get("descriptionurl")
        or (
            "https://commons.wikimedia.org/wiki/"
            f"File:Sign_language_{letter}.svg"
        )
    )

    return (
        image_url,
        description_url,
    )


# ============================================================
# DOWNLOAD ONE LETTER
# ============================================================

def download_letter(
    letter: str,
) -> dict:

    print()
    print(
        f"[{letter}] Looking up image..."
    )

    image_url, source_url = (
        get_png_url(letter)
    )

    response = requests.get(
        image_url,
        headers=HEADERS,
        timeout=60,
    )

    response.raise_for_status()

    content_type = (
        response.headers
        .get("Content-Type", "")
        .lower()
    )

    # Wikimedia thumbnails of SVG files
    # should normally be PNG.
    if (
        "image/png" not in content_type
        and "image" not in content_type
    ):
        raise RuntimeError(
            f"Unexpected content type: "
            f"{content_type}"
        )

    output_path = (
        LETTERS_DIR
        / f"{letter.lower()}.png"
    )

    output_path.write_bytes(
        response.content
    )

    size_kb = (
        output_path.stat().st_size
        / 1024
    )

    print(
        f"[{letter}] Saved: "
        f"{output_path.name} "
        f"({size_kb:.1f} KB)"
    )

    return {
        "letter": letter,
        "filename": output_path.name,
        "source": source_url,
        "size_kb": size_kb,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 72)
    print("SIGNBRIDGE - DOWNLOAD ASL LETTER IMAGES")
    print("=" * 72)

    print()
    print("Source:")
    print("Wikimedia Commons - ASL letters")

    print()
    print("Destination:")
    print(LETTERS_DIR)

    print()
    print(
        "The existing 120 word videos "
        "will NOT be changed."
    )

    print()

    downloaded = []
    failed = []

    for letter in string.ascii_uppercase:

        try:
            result = download_letter(
                letter
            )

            downloaded.append(
                result
            )

        except Exception as error:

            print(
                f"[{letter}] FAILED: {error}"
            )

            failed.append(
                (
                    letter,
                    str(error),
                )
            )

    print()
    print("=" * 72)
    print("RESULT")
    print("=" * 72)

    print(
        f"Downloaded : {len(downloaded)}/26"
    )

    print(
        f"Failed     : {len(failed)}"
    )

    print()
    print("Folder:")
    print(LETTERS_DIR)

    if failed:

        print()
        print("Failed letters:")

        for letter, error in failed:

            print(
                f"  {letter}: {error}"
            )

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()