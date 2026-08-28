from __future__ import annotations

import importlib.util
import re
import sqlite3
import sys
import threading
import time

from collections import deque
from pathlib import Path

import cv2
import mediapipe as mp

from flask import (
    Flask,
    Response,
    g,
    jsonify,
    request,
    send_from_directory,
    url_for,
)

from education_backend import education_bp
from chatbot_backend import chatbot_bp


# ============================================================
# PATHS
# ============================================================

# sign_bridge/backend
BACKEND_ROOT = Path(__file__).resolve().parent

# sign_bridge
SIGNBRIDGE_ROOT = BACKEND_ROOT.parent

# sign_bridge/ASL-Smart-Video-Translator
AI_PROJECT_ROOT = (
    SIGNBRIDGE_ROOT
    / "ASL-Smart-Video-Translator"
)

# Existing AI live translator
LIVE_TRANSLATOR_FILE = (
    AI_PROJECT_ROOT
    / "src_v2"
    / "06_live_translator.py"
)


# ============================================================
# DICTIONARY PATHS
# ============================================================

DICTIONARY_DIR = (
    BACKEND_ROOT
    / "dictionary_data"
)

DICTIONARY_VIDEOS_DIR = (
    DICTIONARY_DIR
    / "videos"
)

DICTIONARY_LETTERS_DIR = (
    DICTIONARY_DIR
    / "letters"
)

DICTIONARY_DB_PATH = (
    DICTIONARY_DIR
    / "dictionary.db"
)


# ============================================================
# PATH DEBUG
# ============================================================

print()
print("=" * 72)
print("SIGNBRIDGE BACKEND PATH CHECK")
print("=" * 72)

print("Backend root:")
print(BACKEND_ROOT)

print()
print("SignBridge root:")
print(SIGNBRIDGE_ROOT)

print()
print("AI project root:")
print(AI_PROJECT_ROOT)

print()
print("Live translator:")
print(LIVE_TRANSLATOR_FILE)

print(
    "Live translator exists:",
    LIVE_TRANSLATOR_FILE.exists(),
)

print()
print("Dictionary database:")
print(DICTIONARY_DB_PATH)

print(
    "Dictionary database exists:",
    DICTIONARY_DB_PATH.exists(),
)

print()
print("Dictionary videos:")
print(DICTIONARY_VIDEOS_DIR)

print(
    "Dictionary videos folder exists:",
    DICTIONARY_VIDEOS_DIR.exists(),
)

print()
print("Dictionary letter images:")
print(DICTIONARY_LETTERS_DIR)

print(
    "Dictionary letters folder exists:",
    DICTIONARY_LETTERS_DIR.exists(),
)

print("=" * 72)
print()


# ============================================================
# MAKE SURE AI MODULES CAN BE IMPORTED
# ============================================================

if str(AI_PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(AI_PROJECT_ROOT),
    )

AI_SRC_ROOT = (
    AI_PROJECT_ROOT
    / "src_v2"
)

if str(AI_SRC_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(AI_SRC_ROOT),
    )


# ============================================================
# LOAD EXISTING LIVE TRANSLATOR
# ============================================================

def load_live_translator():
    if not LIVE_TRANSLATOR_FILE.exists():
        raise FileNotFoundError(
            "Could not find live translator:\n"
            f"{LIVE_TRANSLATOR_FILE}"
        )

    spec = importlib.util.spec_from_file_location(
        "asl_live_runtime",
        LIVE_TRANSLATOR_FILE,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Could not load 06_live_translator.py"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


print("=" * 72)
print("Loading SignBridge AI...")
print("=" * 72)

live = load_live_translator()

print("AI model loaded successfully.")
print()


# ============================================================
# TRANSLATOR SERVICE
# ============================================================

class SignTranslationService:
    def __init__(self):
        self.lock = threading.Lock()

        self.running = False
        self.enabled = False

        self.thread = None
        self.camera = None

        self.latest_frame = None
        self.state = "READY"

        self.label = None
        self.confidence = 0.0
        self.reason = ""

        self.hand_count = 0
        self.motion = 0.0

        self.history: list[str] = []

    # --------------------------------------------------------
    # START BACKGROUND SERVICE
    # --------------------------------------------------------

    def start(self):
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._run,
            daemon=True,
        )

        self.thread.start()

    # --------------------------------------------------------
    # ENABLE / DISABLE TRANSLATION
    # --------------------------------------------------------

    def set_enabled(
        self,
        enabled: bool,
    ):
        with self.lock:
            self.enabled = enabled

            if enabled:
                self.state = "WAITING"
                self.label = None
                self.confidence = 0.0
                self.reason = ""

            else:
                self.state = "PAUSED"
                self.label = None
                self.confidence = 0.0
                self.reason = ""

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    def get_status(self):
        with self.lock:
            return {
                "running":
                    self.running,

                "enabled":
                    self.enabled,

                "state":
                    self.state,

                "label":
                    self.label,

                "confidence":
                    float(self.confidence),

                "reason":
                    self.reason,

                "hands":
                    int(self.hand_count),

                "motion":
                    float(self.motion),

                "history":
                    list(self.history),
            }

    # --------------------------------------------------------
    # FRAME
    # --------------------------------------------------------

    def get_frame(self):
        with self.lock:
            if self.latest_frame is None:
                return None

            return self.latest_frame

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    def reset_result(self):
        with self.lock:
            self.label = None
            self.confidence = 0.0
            self.reason = ""

            self.history.clear()

            if self.enabled:
                self.state = "WAITING"
            else:
                self.state = "PAUSED"

    # --------------------------------------------------------
    # MAIN AI LOOP
    # --------------------------------------------------------

    def _run(self):
        camera = None

        try:
            camera = live.LatestFrameCamera(
                live.CAMERA_INDEX
            )

            self.camera = camera

            extractor = (
                live.HandFeatureExtractor()
            )

            pre_roll = deque(
                maxlen=live.PRE_ROLL_FRAMES
            )

            captured_frames = []

            previous_features = None

            recording = False

            movement_streak = 0
            still_streak = 0
            no_hand_streak = 0

            cooldown_until = 0.0

            previous_timestamp = -1
            last_camera_frame_number = -1

            start_time = (
                time.perf_counter()
            )

            with live.HandLandmarker.create_from_options(
                live.hand_options
            ) as detector:

                print(
                    "Camera and MediaPipe are ready."
                )

                while self.running:
                    (
                        camera_frame_number,
                        raw_frame,
                    ) = camera.read()

                    if raw_frame is None:
                        time.sleep(0.005)
                        continue

                    if (
                        camera_frame_number
                        == last_camera_frame_number
                    ):
                        time.sleep(0.001)
                        continue

                    last_camera_frame_number = (
                        camera_frame_number
                    )

                    current_time = (
                        time.perf_counter()
                    )

                    # ----------------------------------------
                    # DISPLAY FRAME
                    # ----------------------------------------

                    display_frame = cv2.flip(
                        raw_frame,
                        1,
                    )

                    with self.lock:
                        translation_enabled = (
                            self.enabled
                        )

                    # ----------------------------------------
                    # TRANSLATION OFF
                    # ----------------------------------------

                    if not translation_enabled:
                        self._save_frame(
                            display_frame
                        )

                        time.sleep(0.01)
                        continue

                    # ----------------------------------------
                    # MEDIAPIPE
                    # ----------------------------------------

                    rgb_frame = cv2.cvtColor(
                        raw_frame,
                        cv2.COLOR_BGR2RGB,
                    )

                    mp_image = mp.Image(
                        image_format=(
                            mp.ImageFormat.SRGB
                        ),
                        data=rgb_frame,
                    )

                    timestamp = int(
                        (
                            current_time
                            - start_time
                        )
                        * 1000
                    )

                    if timestamp <= previous_timestamp:
                        timestamp = (
                            previous_timestamp
                            + 1
                        )

                    previous_timestamp = (
                        timestamp
                    )

                    detection = (
                        detector.detect_for_video(
                            mp_image,
                            timestamp,
                        )
                    )

                    (
                        features,
                        has_hand,
                        hand_count,
                    ) = extractor.extract(
                        detection
                    )

                    # ----------------------------------------
                    # DRAW HANDS
                    # ----------------------------------------

                    live.draw_detected_hands(
                        display_frame,
                        detection,
                    )

                    # ----------------------------------------
                    # MOTION
                    # ----------------------------------------

                    if has_hand:
                        no_hand_streak = 0

                        motion = (
                            live.calculate_frame_motion(
                                previous_features,
                                features,
                            )
                        )

                        previous_features = (
                            features.copy()
                        )

                    else:
                        no_hand_streak += 1
                        motion = 0.0

                    with self.lock:
                        self.hand_count = (
                            hand_count
                        )

                        self.motion = (
                            motion
                        )

                    # ----------------------------------------
                    # WAITING
                    # ----------------------------------------

                    if not recording:
                        if has_hand:
                            pre_roll.append(
                                features.copy()
                            )

                            if (
                                current_time
                                >= cooldown_until
                            ):
                                if (
                                    motion
                                    >= live.START_MOTION_THRESHOLD
                                ):
                                    movement_streak += 1

                                else:
                                    movement_streak = max(
                                        0,
                                        movement_streak - 1,
                                    )

                                if (
                                    movement_streak
                                    >= live.START_MOTION_FRAMES
                                ):
                                    recording = True

                                    captured_frames = list(
                                        pre_roll
                                    )

                                    still_streak = 0
                                    movement_streak = 0

                                    with self.lock:
                                        self.state = (
                                            "RECORDING"
                                        )

                        else:
                            movement_streak = 0

                            if no_hand_streak >= 3:
                                pre_roll.clear()

                                previous_features = None

                                extractor.reset()

                            if (
                                current_time
                                >= cooldown_until
                            ):
                                with self.lock:
                                    self.state = (
                                        "WAITING"
                                    )

                    # ----------------------------------------
                    # RECORDING SIGN
                    # ----------------------------------------

                    else:
                        captured_frames.append(
                            features.copy()
                        )

                        if not has_hand:
                            still_streak += 2

                        elif (
                            motion
                            <= live.STOP_MOTION_THRESHOLD
                        ):
                            still_streak += 1

                        else:
                            still_streak = 0

                        with self.lock:
                            self.state = "RECORDING"

                        long_enough = (
                            len(captured_frames)
                            >= live.MIN_CAPTURE_FRAMES
                        )

                        ended_by_stillness = (
                            long_enough
                            and still_streak
                            >= live.END_STILL_FRAMES
                        )

                        ended_by_limit = (
                            len(captured_frames)
                            >= live.MAX_CAPTURE_FRAMES
                        )

                        if (
                            ended_by_stillness
                            or ended_by_limit
                        ):
                            removable_still = max(
                                0,
                                still_streak - 2,
                            )

                            usable_length = max(
                                live.MIN_CAPTURE_FRAMES,
                                len(captured_frames)
                                - removable_still,
                            )

                            sign_frames = (
                                captured_frames[
                                    :usable_length
                                ]
                            )

                            try:
                                result = (
                                    live.predict_sign(
                                        sign_frames
                                    )
                                )

                                accepted = (
                                    result["accepted"]
                                )

                                if accepted:
                                    label = (
                                        result["label"]
                                    )

                                    confidence = float(
                                        result[
                                            "confidence"
                                        ]
                                    )

                                    with self.lock:
                                        self.state = (
                                            "ACCEPTED"
                                        )

                                        self.label = (
                                            label
                                        )

                                        self.confidence = (
                                            confidence
                                        )

                                        self.reason = (
                                            result["reason"]
                                        )

                                        if (
                                            not self.history
                                            or self.history[-1]
                                            != label
                                        ):
                                            self.history.append(
                                                label
                                            )

                                        self.history = (
                                            self.history[-8:]
                                        )

                                    print(
                                        "Accepted:",
                                        label,
                                        f"{confidence:.1%}",
                                    )

                                else:
                                    with self.lock:
                                        self.state = (
                                            "UNKNOWN"
                                        )

                                        self.label = (
                                            "Unknown Sign"
                                        )

                                        self.confidence = float(
                                            result[
                                                "confidence"
                                            ]
                                        )

                                        self.reason = (
                                            result["reason"]
                                        )

                                    print(
                                        "Rejected:",
                                        result["label"],
                                        result["reason"],
                                    )

                            except Exception as error:
                                print(
                                    "Prediction error:",
                                    error,
                                )

                                with self.lock:
                                    self.state = (
                                        "ERROR"
                                    )

                                    self.label = (
                                        "Prediction Error"
                                    )

                                    self.confidence = 0.0

                                    self.reason = str(
                                        error
                                    )

                            recording = False

                            captured_frames = []

                            pre_roll.clear()

                            movement_streak = 0
                            still_streak = 0

                            cooldown_until = (
                                current_time
                                + live.RESULT_COOLDOWN_SECONDS
                            )

                    # ----------------------------------------
                    # SAVE FRAME
                    # ----------------------------------------

                    self._save_frame(
                        display_frame
                    )

        except Exception as error:
            print(
                "Translator service error:",
                error,
            )

            with self.lock:
                self.state = "ERROR"
                self.reason = str(error)

        finally:
            if camera is not None:
                camera.release()

    # --------------------------------------------------------
    # JPEG ENCODE
    # --------------------------------------------------------

    def _save_frame(
        self,
        frame,
    ):
        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                82,
            ],
        )

        if not success:
            return

        data = encoded.tobytes()

        with self.lock:
            self.latest_frame = data


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)

app.register_blueprint(
    education_bp
)

app.register_blueprint(
    chatbot_bp
)

service = (
    SignTranslationService()
)


# ============================================================
# CREATE DICTIONARY FOLDERS
# ============================================================

DICTIONARY_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DICTIONARY_VIDEOS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DICTIONARY_LETTERS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DICTIONARY HELPERS
# ============================================================

def normalize_dictionary_word(
    value: str,
) -> str:
    value = value.strip().upper()

    return re.sub(
        r"[^A-Z0-9]+",
        "",
        value,
    )


# ============================================================
# DICTIONARY DATABASE INITIALIZATION + MIGRATION
# ============================================================

def init_dictionary_db():
    connection = sqlite3.connect(
        DICTIONARY_DB_PATH
    )

    try:
        # ----------------------------------------------------
        # CREATE TABLE IF IT DOES NOT EXIST
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS dictionary_signs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                word TEXT NOT NULL,

                normalized_word TEXT
                    NOT NULL UNIQUE,

                letter TEXT NOT NULL,

                video_filename TEXT
                    NOT NULL,

                media_type TEXT
                    NOT NULL DEFAULT 'video',

                image_filename TEXT
                    NOT NULL DEFAULT '',

                original_dataset TEXT
                    NOT NULL DEFAULT 'WLASL100',

                original_split TEXT
                    NOT NULL DEFAULT '',

                original_folder TEXT
                    NOT NULL DEFAULT '',

                original_video_name TEXT
                    NOT NULL DEFAULT '',

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # MIGRATE OLD DATABASE IF NEEDED
        # ----------------------------------------------------

        columns = connection.execute(
            """
            PRAGMA table_info(dictionary_signs)
            """
        ).fetchall()

        existing_columns = {
            row[1]
            for row in columns
        }

        migrations = {
            "media_type":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN media_type TEXT
                NOT NULL DEFAULT 'video'
                """,

            "image_filename":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN image_filename TEXT
                NOT NULL DEFAULT ''
                """,

            "original_dataset":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN original_dataset TEXT
                NOT NULL DEFAULT 'WLASL100'
                """,

            "original_split":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN original_split TEXT
                NOT NULL DEFAULT ''
                """,

            "original_folder":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN original_folder TEXT
                NOT NULL DEFAULT ''
                """,

            "original_video_name":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN original_video_name TEXT
                NOT NULL DEFAULT ''
                """,

            "created_at":
                """
                ALTER TABLE dictionary_signs
                ADD COLUMN created_at TIMESTAMP
                """,
        }

        for column_name, sql in migrations.items():
            if column_name not in existing_columns:
                print(
                    f"Migrating dictionary column: "
                    f"{column_name}"
                )

                connection.execute(
                    sql
                )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_dictionary_signs_word
            ON dictionary_signs(normalized_word)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_dictionary_signs_letter
            ON dictionary_signs(letter)
            """
        )

        connection.commit()

    finally:
        connection.close()


init_dictionary_db()


# ============================================================
# VERIFY DICTIONARY DATABASE
# ============================================================

def print_dictionary_database_info():
    try:
        connection = sqlite3.connect(
            DICTIONARY_DB_PATH
        )

        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM dictionary_signs
            """
        ).fetchone()

        total = (
            int(row[0])
            if row
            else 0
        )

        connection.close()

        print()
        print("=" * 72)
        print("DICTIONARY DATABASE READY")
        print("=" * 72)
        print(
            f"Database: {DICTIONARY_DB_PATH}"
        )
        print(
            f"Words   : {total}"
        )
        print("=" * 72)
        print()

    except Exception as error:
        print()
        print(
            "Dictionary database check failed:"
        )
        print(error)
        print()


print_dictionary_database_info()


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_dictionary_db():
    if "dictionary_db" not in g:
        connection = sqlite3.connect(
            DICTIONARY_DB_PATH,
            timeout=30,
        )

        connection.row_factory = (
            sqlite3.Row
        )

        g.dictionary_db = (
            connection
        )

    return g.dictionary_db


@app.teardown_appcontext
def close_dictionary_db(
    error=None,
):
    connection = g.pop(
        "dictionary_db",
        None,
    )

    if connection is not None:
        connection.close()


# ============================================================
# SERIALIZE DICTIONARY SIGN
# ============================================================

def dictionary_sign_to_json(
    row,
):
    if row is None:
        return None

    keys = row.keys()

    source = (
        row["original_dataset"]
        if "original_dataset" in keys
        else "ASL Citizen"
    )

    split = (
        row["original_split"]
        if "original_split" in keys
        else ""
    )

    media_type = (
        row["media_type"]
        if "media_type" in keys
        else "video"
    )

    if media_type not in {"video", "image"}:
        media_type = "video"

    video_filename = (
        row["video_filename"]
        if "video_filename" in keys
        else ""
    )

    image_filename = (
        row["image_filename"]
        if "image_filename" in keys
        else ""
    )

    video_url = ""
    image_url = ""

    if media_type == "video" and video_filename:
        video_url = url_for(
            "dictionary_video",
            filename=video_filename,
            _external=True,
        )

    if media_type == "image" and image_filename:
        image_url = url_for(
            "dictionary_letter_image",
            filename=image_filename,
            _external=True,
        )

    return {
        "id": row["id"],
        "word": row["word"],
        "letter": row["letter"],
        "media_type": media_type,
        "video_filename": video_filename,
        "video_url": video_url,
        "image_filename": image_filename,
        "image_url": image_url,
        "source": source,
        "split": split,
    }

def get_previous_sign(
    current_word: str,
):
    db = get_dictionary_db()

    return db.execute(
        """
        SELECT *
        FROM dictionary_signs

        WHERE word < ?

        ORDER BY word DESC

        LIMIT 1
        """,
        (
            current_word,
        ),
    ).fetchone()


def get_next_sign(
    current_word: str,
):
    db = get_dictionary_db()

    return db.execute(
        """
        SELECT *
        FROM dictionary_signs

        WHERE word > ?

        ORDER BY word ASC

        LIMIT 1
        """,
        (
            current_word,
        ),
    ).fetchone()


# ============================================================
# MAIN BACKEND HEALTH
# ============================================================

@app.get("/api/health")
def health():
    return jsonify(
        {
            "success": True,

            "message":
                "SignBridge AI Backend is running",

            "backend_root":
                str(BACKEND_ROOT),

            "ai_project_found":
                AI_PROJECT_ROOT.exists(),

            "dictionary_db_found":
                DICTIONARY_DB_PATH.exists(),
        }
    )


# ============================================================
# DICTIONARY HEALTH
# ============================================================

@app.get("/api/dictionary/health")
def dictionary_health():
    try:
        db = get_dictionary_db()

        row = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM dictionary_signs
            """
        ).fetchone()

        total = (
            int(row["total"])
            if row
            else 0
        )

        return jsonify(
            {
                "success":
                    True,

                "message":
                    "Dictionary API is running",

                "total_words":
                    total,

                "database":
                    str(
                        DICTIONARY_DB_PATH
                    ),
            }
        )

    except Exception as error:
        print(
            "Dictionary health error:",
            repr(error),
        )

        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(error),

                "database":
                    str(
                        DICTIONARY_DB_PATH
                    ),

                "database_exists":
                    DICTIONARY_DB_PATH.exists(),
            }
        ), 500


# ============================================================
# DICTIONARY LETTERS
# ============================================================

@app.get("/api/dictionary/letters")
def dictionary_letters():
    db = get_dictionary_db()

    rows = db.execute(
        """
        SELECT
            letter,
            COUNT(*) AS count

        FROM dictionary_signs

        GROUP BY letter

        ORDER BY letter
        """
    ).fetchall()

    return jsonify(
        {
            "success": True,

            "letters": [
                {
                    "letter":
                        row["letter"],

                    "count":
                        int(row["count"]),
                }

                for row in rows
            ],
        }
    )


# ============================================================
# DICTIONARY ALL SIGNS
# ============================================================

@app.get("/api/dictionary/signs")
def dictionary_signs():
    db = get_dictionary_db()

    search = request.args.get(
        "search",
        "",
    ).strip()

    letter = request.args.get(
        "letter",
        "",
    ).strip().upper()

    try:
        limit = int(
            request.args.get(
                "limit",
                500,
            )
        )

    except ValueError:
        limit = 500

    limit = max(
        1,
        min(
            limit,
            1000,
        ),
    )

    conditions = []
    values = []

    if search:
        normalized_search = (
            normalize_dictionary_word(
                search
            )
        )

        conditions.append(
            "normalized_word LIKE ?"
        )

        values.append(
            f"%{normalized_search}%"
        )

    if (
        letter
        and letter != "ALL"
    ):
        conditions.append(
            "letter = ?"
        )

        values.append(
            letter
        )

    where_clause = ""

    if conditions:
        where_clause = (
            "WHERE "
            + " AND ".join(
                conditions
            )
        )

    query = f"""
        SELECT *
        FROM dictionary_signs

        {where_clause}

        ORDER BY word

        LIMIT ?
    """

    values.append(
        limit
    )

    rows = db.execute(
        query,
        values,
    ).fetchall()

    return jsonify(
        {
            "success":
                True,

            "count":
                len(rows),

            "items": [
                dictionary_sign_to_json(
                    row
                )

                for row in rows
            ],
        }
    )


# ============================================================
# DICTIONARY SIGN BY ID
# ============================================================

@app.get(
    "/api/dictionary/signs/<int:sign_id>"
)
def dictionary_sign_details(
    sign_id: int,
):
    db = get_dictionary_db()

    row = db.execute(
        """
        SELECT *
        FROM dictionary_signs

        WHERE id = ?

        LIMIT 1
        """,
        (
            sign_id,
        ),
    ).fetchone()

    if row is None:
        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Word not found.",
            }
        ), 404

    previous_row = (
        get_previous_sign(
            row["word"]
        )
    )

    next_row = (
        get_next_sign(
            row["word"]
        )
    )

    return jsonify(
        {
            "success":
                True,

            "sign":
                dictionary_sign_to_json(
                    row
                ),

            "previous":
                dictionary_sign_to_json(
                    previous_row
                ),

            "next":
                dictionary_sign_to_json(
                    next_row
                ),
        }
    )


# ============================================================
# DICTIONARY SIGN BY WORD
# ============================================================

@app.get(
    "/api/dictionary/word/<path:word>"
)
def dictionary_sign_by_word(
    word: str,
):
    db = get_dictionary_db()

    normalized_word = (
        normalize_dictionary_word(
            word
        )
    )

    row = db.execute(
        """
        SELECT *
        FROM dictionary_signs

        WHERE normalized_word = ?

        LIMIT 1
        """,
        (
            normalized_word,
        ),
    ).fetchone()

    if row is None:
        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Word not found.",
            }
        ), 404

    previous_row = (
        get_previous_sign(
            row["word"]
        )
    )

    next_row = (
        get_next_sign(
            row["word"]
        )
    )

    return jsonify(
        {
            "success":
                True,

            "sign":
                dictionary_sign_to_json(
                    row
                ),

            "previous":
                dictionary_sign_to_json(
                    previous_row
                ),

            "next":
                dictionary_sign_to_json(
                    next_row
                ),
        }
    )


# ============================================================
# DICTIONARY VIDEO
# ============================================================

@app.get(
    "/api/dictionary/videos/<path:filename>"
)
def dictionary_video(
    filename: str,
):
    return send_from_directory(
        DICTIONARY_VIDEOS_DIR,
        filename,
        conditional=True,
    )


# ============================================================
# DICTIONARY LETTER IMAGE
# ============================================================

@app.get(
    "/api/dictionary/letters-media/<path:filename>"
)
def dictionary_letter_image(
    filename: str,
):
    return send_from_directory(
        DICTIONARY_LETTERS_DIR,
        filename,
        conditional=True,
    )


# ============================================================
# CAMERA FRAME
# ============================================================

@app.get("/api/sign/frame")
def sign_frame():
    frame = service.get_frame()

    if frame is None:
        return Response(
            status=503
        )

    return Response(
        frame,
        mimetype="image/jpeg",
        headers={
            "Cache-Control":
                "no-store, no-cache, must-revalidate",
        },
    )


# ============================================================
# STATUS
# ============================================================

@app.get("/api/sign/status")
def sign_status():
    return jsonify(
        {
            "success":
                True,

            **service.get_status(),
        }
    )


# ============================================================
# START TRANSLATION
# ============================================================

@app.post("/api/sign/start")
def start_translation():
    service.set_enabled(
        True
    )

    return jsonify(
        {
            "success":
                True,

            "message":
                "Translation started",
        }
    )


# ============================================================
# STOP TRANSLATION
# ============================================================

@app.post("/api/sign/stop")
def stop_translation():
    service.set_enabled(
        False
    )

    return jsonify(
        {
            "success":
                True,

            "message":
                "Translation stopped",
        }
    )


# ============================================================
# CLEAR HISTORY
# ============================================================

@app.post("/api/sign/reset")
def reset_translation():
    service.reset_result()

    return jsonify(
        {
            "success":
                True,

            "message":
                "Translation reset",
        }
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    service.start()

    print()
    print("=" * 72)
    print("SIGNBRIDGE BACKEND READY")
    print("=" * 72)

    print(
        "Local:"
    )

    print(
        "http://127.0.0.1:5000"
    )

    print()
    print("Main:")
    print("GET  /api/health")

    print()
    print("Translation:")
    print("GET  /api/sign/frame")
    print("GET  /api/sign/status")
    print("POST /api/sign/start")
    print("POST /api/sign/stop")
    print("POST /api/sign/reset")

    print()
    print("Dictionary:")
    print("GET  /api/dictionary/health")
    print("GET  /api/dictionary/letters")
    print("GET  /api/dictionary/signs")
    print("GET  /api/dictionary/signs/<id>")
    print("GET  /api/dictionary/word/<word>")
    print("GET  /api/dictionary/videos/<filename>")
    print("GET  /api/dictionary/letters-media/<filename>")

    print()
    print("Education:")
    print("GET  /api/education/health")
    print("GET  /api/education/levels")
    print("GET  /api/education/levels/<id>")
    print(
        "GET  /api/education/levels/<id>/sentences"
    )
    print(
        "GET  /api/education/levels/<id>/quiz"
    )

    print()
    print("Chatbot:")
    print("GET  /api/chatbot/health")
    print("POST /api/chatbot/message")
    print("POST /api/chatbot/smart-replies")
    print("POST /api/chatbot/speak-for-me")

    print("=" * 72)
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False,
    )