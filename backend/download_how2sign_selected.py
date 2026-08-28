from __future__ import annotations

import json
from pathlib import Path

import duckdb
import requests


# ============================================================
# PATHS
# ============================================================

BACKEND_ROOT = Path(__file__).resolve().parent

OUTPUT_DIR = (
    BACKEND_ROOT
    / "education_data"
    / "videos"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DATASET
# ============================================================

DATASET_ID = (
    "bdanko/"
    "how2sign-rgb-front-clips_256x256_15fps"
)

PARQUET_API = (
    "https://datasets-server.huggingface.co/parquet"
)


# ============================================================
# LEVEL 1 VIDEOS
# ============================================================

TARGETS = [
    {
        "sentence":
            "Hi, my name is Elliot Kwong.",

        "sentence_name":
            "G2dND014Ps4_0-5-rgb_front",

        "output_name":
            "l1_01_introduction.mp4",
    },

    {
        "sentence":
            "Okay, thank you.",

        "sentence_name":
            "-g0sqksgyc4_10-2-rgb_front",

        "output_name":
            "l1_02_okay_thank_you.mp4",
    },

    {
        "sentence":
            "This way please.",

        "sentence_name":
            "g3X3XE6M2_A_12-3-rgb_front",

        "output_name":
            "l1_03_this_way_please.mp4",
    },

    {
        "sentence":
            "Thank you for being with me.",

        "sentence_name":
            "g0TkUiO7t4I_13-8-rgb_front",

        "output_name":
            "l1_04_thank_you_for_being_with_me.mp4",
    },
]


# ============================================================
# GET TEST PARQUET FILES
# ============================================================

def get_test_parquet_urls() -> list[str]:

    print()
    print("Getting Parquet file list...")

    response = requests.get(
        PARQUET_API,
        params={
            "dataset": DATASET_ID,
        },
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    urls = []

    for item in data.get(
        "parquet_files",
        [],
    ):

        if (
            item.get("config") == "default"
            and item.get("split") == "test"
        ):

            url = item.get("url")

            if url:
                urls.append(url)

    return urls


# ============================================================
# DUCKDB
# ============================================================

def create_connection():

    con = duckdb.connect()

    # Allows DuckDB to query HTTPS Parquet files.
    con.execute(
        "INSTALL httpfs;"
    )

    con.execute(
        "LOAD httpfs;"
    )

    return con


# ============================================================
# SQL STRING ESCAPE
# ============================================================

def sql_string(
    value: str,
) -> str:

    return (
        "'"
        + value.replace(
            "'",
            "''",
        )
        + "'"
    )


# ============================================================
# FIND ONE CLIP
# ============================================================

def find_clip(
    con,
    parquet_urls: list[str],
    sentence_name: str,
):

    target_sql = sql_string(
        sentence_name
    )

    for index, url in enumerate(
        parquet_urls,
        start=1,
    ):

        print(
            f"  Checking Parquet "
            f"{index}/{len(parquet_urls)}..."
        )

        url_sql = sql_string(
            url
        )

        # First request only metadata columns.
        #
        # Important:
        # We do NOT request the MP4 column until
        # the target row is found.
        query = f"""
            SELECT
                "__key__",
                "json"
            FROM read_parquet({url_sql})
            WHERE "__key__" = {target_sql}
            LIMIT 1
        """

        rows = con.execute(
            query
        ).fetchall()

        if not rows:
            continue

        key_value = rows[0][0]
        json_value = rows[0][1]

        print()
        print("[FOUND METADATA]")

        print(
            f"Key: {key_value}"
        )

        metadata = None

        if isinstance(
            json_value,
            dict,
        ):
            metadata = json_value

        elif isinstance(
            json_value,
            str,
        ):
            try:
                metadata = json.loads(
                    json_value
                )
            except Exception:
                metadata = None

        if metadata:

            print(
                "Dataset sentence:"
            )

            print(
                metadata.get(
                    "SENTENCE",
                    "",
                )
            )

            print(
                "Sentence ID:"
            )

            print(
                metadata.get(
                    "SENTENCE_ID",
                    "",
                )
            )

            print(
                "Sentence Name:"
            )

            print(
                metadata.get(
                    "SENTENCE_NAME",
                    "",
                )
            )

        # ====================================================
        # NOW FETCH ONLY THIS VIDEO
        # ====================================================

        print()
        print(
            "Downloading only the matched MP4..."
        )

        video_query = f"""
            SELECT
                "mp4"
            FROM read_parquet({url_sql})
            WHERE "__key__" = {target_sql}
            LIMIT 1
        """

        video_rows = con.execute(
            video_query
        ).fetchall()

        if not video_rows:
            return None, metadata

        video_data = video_rows[0][0]

        return (
            video_data,
            metadata,
        )

    return None, None


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 90)

    print(
        "SIGNBRIDGE - SELECTED HOW2SIGN "
        "PARQUET DOWNLOADER"
    )

    print("=" * 90)

    print()
    print(
        f"Dataset: {DATASET_ID}"
    )

    # ========================================================
    # GET ONLY TEST PARQUETS
    # ========================================================

    try:

        parquet_urls = (
            get_test_parquet_urls()
        )

    except Exception as error:

        print()
        print(
            "[ERROR] Could not get "
            "Parquet file list."
        )

        print(error)

        return

    print()
    print(
        f"Test Parquet files found: "
        f"{len(parquet_urls)}"
    )

    if not parquet_urls:

        print()
        print(
            "[ERROR] No Test Parquet "
            "files were returned."
        )

        return

    # ========================================================
    # CREATE DUCKDB
    # ========================================================

    try:

        con = create_connection()

    except Exception as error:

        print()
        print(
            "[ERROR] Could not start DuckDB."
        )

        print(error)

        return

    downloaded = 0
    missing = 0

    # ========================================================
    # TARGETS
    # ========================================================

    for number, target in enumerate(
        TARGETS,
        start=1,
    ):

        print()
        print("=" * 90)

        print(
            f"[{number}/{len(TARGETS)}]"
        )

        print(
            target["sentence"]
        )

        print(
            target["sentence_name"]
        )

        print("=" * 90)

        output_path = (
            OUTPUT_DIR
            / target["output_name"]
        )

        # -----------------------------------------------
        # Skip if already downloaded
        # -----------------------------------------------

        if (
            output_path.exists()
            and output_path.stat().st_size > 0
        ):

            size_mb = (
                output_path.stat().st_size
                / 1024
                / 1024
            )

            print(
                f"[ALREADY EXISTS] "
                f"{size_mb:.2f} MB"
            )

            downloaded += 1

            continue

        try:

            video_data, metadata = (
                find_clip(
                    con,
                    parquet_urls,
                    target[
                        "sentence_name"
                    ],
                )
            )

        except Exception as error:

            print()
            print(
                "[ERROR WHILE SEARCHING]"
            )

            print(error)

            missing += 1

            continue

        if video_data is None:

            print()
            print(
                "[NOT FOUND]"
            )

            missing += 1

            continue

        # ====================================================
        # SAVE MP4
        # ====================================================

        try:

            if isinstance(
                video_data,
                memoryview,
            ):

                video_data = (
                    video_data.tobytes()
                )

            elif isinstance(
                video_data,
                bytearray,
            ):

                video_data = bytes(
                    video_data
                )

            if not isinstance(
                video_data,
                bytes,
            ):

                raise TypeError(
                    "MP4 column was not returned "
                    "as binary bytes. "
                    f"Type: {type(video_data)}"
                )

            output_path.write_bytes(
                video_data
            )

            size_mb = (
                output_path.stat().st_size
                / 1024
                / 1024
            )

            print()
            print(
                "[SUCCESS]"
            )

            print(
                output_path
            )

            print(
                f"Size: {size_mb:.2f} MB"
            )

            downloaded += 1

        except Exception as error:

            print()
            print(
                "[SAVE ERROR]"
            )

            print(error)

            missing += 1

    con.close()

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("=" * 90)

    print(
        "FINISHED"
    )

    print("=" * 90)

    print()
    print(
        f"Downloaded: {downloaded}"
    )

    print(
        f"Missing   : {missing}"
    )

    print()
    print(
        "Output folder:"
    )

    print(
        OUTPUT_DIR
    )


if __name__ == "__main__":
    main()