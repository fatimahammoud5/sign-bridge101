from pathlib import Path
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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

MISSING_LETTERS = [
    "Q",
    "R",
    "S",
    "X",
    "Y",
    "Z",
]

HEADERS = {
    "User-Agent": (
        "SignBridge-Capstone/1.0 "
        "ASL educational dictionary"
    )
}


# ============================================================
# SESSION WITH RETRIES
# ============================================================

def create_session():

    retry = Retry(
        total=8,
        connect=8,
        read=8,
        status=8,
        backoff_factor=1.5,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],
        allowed_methods=frozenset(
            ["GET"]
        ),
    )

    adapter = HTTPAdapter(
        max_retries=retry
    )

    session = requests.Session()

    session.mount(
        "https://",
        adapter,
    )

    session.headers.update(
        HEADERS
    )

    return session


# ============================================================
# GET THUMBNAIL URL
# ============================================================

def get_png_url(
    session,
    letter: str,
):

    title = (
        f"File:Sign language {letter}.svg"
    )

    # Try several rendered widths.
    # Wikimedia will render the SVG as PNG.
    for width in [
        600,
        500,
        400,
        300,
    ]:

        print(
            f"    Trying Wikimedia "
            f"thumbnail width {width}px..."
        )

        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": width,
            "titles": title,
        }

        try:

            response = session.get(
                WIKIMEDIA_API,
                params=params,
                timeout=60,
            )

            response.raise_for_status()

            data = response.json()

            pages = (
                data
                .get("query", {})
                .get("pages", [])
            )

            if not pages:
                continue

            page = pages[0]

            if page.get("missing"):
                continue

            imageinfo = page.get(
                "imageinfo",
                [],
            )

            if not imageinfo:
                continue

            info = imageinfo[0]

            thumb_url = info.get(
                "thumburl"
            )

            if thumb_url:
                return thumb_url

        except Exception as error:

            print(
                f"    API attempt failed: "
                f"{error}"
            )

        time.sleep(1)

    return None


# ============================================================
# DOWNLOAD ONE LETTER
# ============================================================

def download_letter(
    session,
    letter: str,
):

    print()
    print("=" * 60)
    print(
        f"LETTER {letter}"
    )
    print("=" * 60)

    destination = (
        LETTERS_DIR
        / f"{letter.lower()}.png"
    )

    png_url = get_png_url(
        session,
        letter,
    )

    if not png_url:

        print(
            f"[FAILED] Could not obtain "
            f"PNG URL for {letter}"
        )

        return False

    print(
        "    PNG URL found."
    )

    try:

        response = session.get(
            png_url,
            timeout=90,
        )

        response.raise_for_status()

        content = response.content

    except Exception as error:

        print(
            f"[FAILED] Download error: "
            f"{error}"
        )

        return False

    # --------------------------------------------------------
    # VERIFY REAL PNG
    # --------------------------------------------------------

    png_signature = (
        b"\x89PNG\r\n\x1a\n"
    )

    if not content.startswith(
        png_signature
    ):

        print(
            "[FAILED] Downloaded file "
            "is not a valid PNG."
        )

        print(
            "Content-Type:",
            response.headers.get(
                "Content-Type",
                "",
            ),
        )

        return False

    if len(content) < 1000:

        print(
            "[FAILED] PNG is too small."
        )

        return False

    destination.write_bytes(
        content
    )

    print(
        f"[OK] Saved:"
    )

    print(
        f"     {destination}"
    )

    print(
        f"     "
        f"{len(content) / 1024:.1f} KB"
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 72)
    print(
        "SIGNBRIDGE - MISSING ASL LETTERS"
    )
    print("=" * 72)

    print()
    print(
        "Only these letters will be attempted:"
    )

    print(
        ", ".join(
            MISSING_LETTERS
        )
    )

    session = create_session()

    successful = []
    failed = []

    for letter in MISSING_LETTERS:

        result = download_letter(
            session,
            letter,
        )

        if result:

            successful.append(
                letter
            )

        else:

            failed.append(
                letter
            )

        # Be gentle with Wikimedia.
        time.sleep(1)

    # --------------------------------------------------------
    # FINAL CHECK A-Z
    # --------------------------------------------------------

    valid_letters = []

    missing_final = []

    for code in range(
        ord("A"),
        ord("Z") + 1,
    ):

        letter = chr(code)

        path = (
            LETTERS_DIR
            / f"{letter.lower()}.png"
        )

        if (
            path.exists()
            and path.stat().st_size > 1000
        ):

            valid_letters.append(
                letter
            )

        else:

            missing_final.append(
                letter
            )

    print()
    print("=" * 72)
    print("RESULT")
    print("=" * 72)

    print(
        "Downloaded now :",
        len(successful),
    )

    if successful:

        print(
            "Successful     :",
            ", ".join(successful),
        )

    print(
        "Failed now     :",
        len(failed),
    )

    if failed:

        print(
            "Failed         :",
            ", ".join(failed),
        )

    print()
    print(
        f"Valid images   : "
        f"{len(valid_letters)}/26"
    )

    print(
        f"Missing        : "
        f"{len(missing_final)}"
    )

    if missing_final:

        print(
            "Missing letters:",
            ", ".join(
                missing_final
            ),
        )

    else:

        print()
        print(
            "SUCCESS: ALL A-Z IMAGES "
            "ARE READY."
        )

    print("=" * 72)
    print()


if __name__ == "__main__":
    main()