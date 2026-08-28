from __future__ import annotations

import json
import os
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from google import genai
from google.genai import types

from rag_service import SignBridgeRAG
from signbridge_memory import SignBridgeMemory


# ============================================================
# CONFIG
# ============================================================

BACKEND_ROOT = Path(__file__).resolve().parent

load_dotenv(
    BACKEND_ROOT / ".env"
)

chatbot_bp = Blueprint(
    "chatbot",
    __name__,
)


# ============================================================
# GEMINI MODELS
# ============================================================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash",
).strip()


# Optional fallback model.
#
# Leave empty unless you have tested another model.
# You can later add in .env:
#
# GEMINI_FALLBACK_MODEL=your-working-model
#
GEMINI_FALLBACK_MODEL = os.getenv(
    "GEMINI_FALLBACK_MODEL",
    "",
).strip()


# ============================================================
# SIGNBRIDGE SERVICES
# ============================================================

APP_MEMORY = SignBridgeMemory()

RAG = SignBridgeRAG()


# ============================================================
# GEMINI CLIENT
# ============================================================

@lru_cache(maxsize=1)
def get_client() -> genai.Client:

    api_key = os.getenv(
        "GEMINI_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing "
            "from backend/.env"
        )

    return genai.Client(
        api_key=api_key,
    )


# ============================================================
# ERROR HELPERS
# ============================================================

def _is_quota_error(
    error: Exception | str,
) -> bool:

    text = str(
        error
    ).lower()

    return (
        "429" in text
        or "resource_exhausted" in text
        or "quota" in text
    )


def _is_temporary_error(
    error: Exception | str,
) -> bool:

    text = str(
        error
    ).lower()

    temporary_markers = (
        "503",
        "service unavailable",
        "temporarily unavailable",
        "high demand",
        "timeout",
        "timed out",
        "connection reset",
    )

    return any(
        marker in text
        for marker in temporary_markers
    )


# ============================================================
# ONE GEMINI REQUEST
# ============================================================

def _generate_once(
    *,
    model: str,
    contents: Any,
    system_instruction: str,
    max_output_tokens: int,
    temperature: float,
) -> str:

    response = (
        get_client()
        .models
        .generate_content(
            model=model,
            contents=contents,
            config=
                types.GenerateContentConfig(
                    system_instruction=
                        system_instruction,
                    max_output_tokens=
                        max_output_tokens,
                    temperature=
                        temperature,
                ),
        )
    )

    text = (
        response.text
        or ""
    ).strip()

    if not text:
        raise RuntimeError(
            f"Gemini model {model} "
            "returned an empty response."
        )

    return text


# ============================================================
# GEMINI WITH OPTIONAL FALLBACK
# ============================================================

def generate_text(
    *,
    contents: Any,
    system_instruction: str,
    max_output_tokens: int = 750,
    temperature: float = 0.35,
    main_attempts: int = 2,
) -> tuple[str, str]:

    models: list[
        tuple[str, int]
    ] = [
        (
            GEMINI_MODEL,
            max(
                1,
                main_attempts,
            ),
        ),
    ]

    if (
        GEMINI_FALLBACK_MODEL
        and
        GEMINI_FALLBACK_MODEL
        != GEMINI_MODEL
    ):
        models.append(
            (
                GEMINI_FALLBACK_MODEL,
                1,
            )
        )

    last_error: Exception | None = None

    for model, attempts in models:

        for attempt in range(
            1,
            attempts + 1,
        ):

            try:

                result = _generate_once(
                    model=model,
                    contents=contents,
                    system_instruction=
                        system_instruction,
                    max_output_tokens=
                        max_output_tokens,
                    temperature=
                        temperature,
                )

                return (
                    result,
                    model,
                )

            except Exception as error:

                last_error = error

                print(
                    f"GEMINI {model} "
                    f"ATTEMPT "
                    f"{attempt}/{attempts} "
                    "ERROR:",
                    repr(error),
                )

                # --------------------------------------------
                # QUOTA ERROR
                #
                # Do not waste more requests on the same
                # exhausted model.
                # --------------------------------------------

                if _is_quota_error(
                    error
                ):
                    break

                # --------------------------------------------
                # TEMPORARY ERROR
                # --------------------------------------------

                if (
                    attempt < attempts
                    and
                    _is_temporary_error(
                        error
                    )
                ):

                    time.sleep(
                        0.45
                        * attempt
                    )

                    continue

                break

    raise RuntimeError(
        "Gemini is currently unavailable "
        "on the configured models. "
        f"Last error: {last_error}"
    )


# ============================================================
# CLEAN CONVERSATION HISTORY
# ============================================================

def clean_history(
    raw_history: Any,
) -> list[
    dict[str, str]
]:

    if not isinstance(
        raw_history,
        list,
    ):
        return []

    error_markers = (
        "resource_exhausted",
        "could not answer this request",
        "gemini request failed",
        "could not reach signbridge ai",
        "gemini is currently unavailable",
        "please check the backend",
        "current gemini quota",
    )

    successful_turns: list[
        dict[str, str]
    ] = []

    pending_user: str | None = None

    # ========================================================
    # IMPORTANT
    #
    # Keep only complete:
    #
    # user
    # assistant
    #
    # pairs.
    #
    # If the newest question was already inserted by Flutter
    # into history, but has no assistant answer yet, it is
    # discarded here.
    #
    # This prevents Gemini from answering an older question.
    # ========================================================

    for item in raw_history[
        -20:
    ]:

        if not isinstance(
            item,
            dict,
        ):
            continue

        role = str(
            item.get(
                "role",
                "",
            )
        ).strip().lower()

        content = str(
            item.get(
                "content",
                "",
            )
        ).strip()

        if role not in {
            "user",
            "assistant",
        }:
            continue

        if not content:
            continue

        # ----------------------------------------------------
        # USER
        # ----------------------------------------------------

        if role == "user":

            pending_user = content

            continue

        # ----------------------------------------------------
        # ASSISTANT
        # ----------------------------------------------------

        if pending_user is None:
            continue

        lowered = (
            content.lower()
        )

        # Failed AI responses must not enter history.
        if any(
            marker in lowered
            for marker in error_markers
        ):

            pending_user = None

            continue

        successful_turns.append(
            {
                "role":
                    "user",

                "content":
                    pending_user,
            }
        )

        successful_turns.append(
            {
                "role":
                    "assistant",

                "content":
                    content,
            }
        )

        pending_user = None

    # Last four complete conversations.
    return successful_turns[
        -8:
    ]


# ============================================================
# BUILD GEMINI CONTENTS
# ============================================================

def build_contents(
    history: list[
        dict[str, str]
    ],
    current_message: str,
) -> list[
    types.Content
]:

    contents: list[
        types.Content
    ] = []

    for item in history:

        if (
            item[
                "role"
            ]
            ==
            "assistant"
        ):
            role = "model"
        else:
            role = "user"

        contents.append(
            types.Content(
                role=role,

                parts=[
                    types.Part
                    .from_text(
                        text=
                            item[
                                "content"
                            ]
                    )
                ],
            )
        )

    # ========================================================
    # NEWEST QUESTION ALWAYS HAS PRIORITY
    # ========================================================

    newest_request = (
        "CURRENT USER REQUEST:\n"
        "Answer THIS newest request now. "
        "Conversation history is background context only. "
        "Do not answer an older request unless this newest "
        "request explicitly refers to it.\n\n"
        f"{current_message}"
    )

    contents.append(
        types.Content(
            role=
                "user",

            parts=[
                types.Part
                .from_text(
                    text=
                        newest_request
                )
            ],
        )
    )

    return contents


# ============================================================
# MAIN SIGNBRIDGE SYSTEM INSTRUCTION
# ============================================================

def build_assistant_instruction(
    *,
    rag_context: str,
    app_state: dict[
        str,
        Any,
    ],
    mode: str,
) -> str:

    state_text = json.dumps(
        app_state,
        ensure_ascii=False,
        indent=2,
    )

    knowledge_text = (
        rag_context.strip()
        or
        "No relevant SignBridge "
        "RAG document was retrieved."
    )

    return f"""
You are SignBridge AI, a highly capable general-purpose AI assistant inside the SignBridge application.

CORE RULES:

- The user may ask ANY normal question.
- You are NOT restricted to SignBridge questions.
- Never require preset questions.
- Never require fixed keywords.
- Never require exact phrases.
- Understand natural English.
- Understand Arabic.
- Understand Lebanese Arabic.
- Understand follow-up questions.
- Understand typos and incomplete wording.

CURRENT QUESTION PRIORITY:

- The NEWEST/CURRENT user request has absolute priority.
- Conversation history is background context only.
- Never answer an older question when the newest question changes topic.
- If the newest request clearly refers to an earlier answer, use history naturally.
- If the newest request changes topic, change topic immediately.

LANGUAGE:

- Answer in the same language as the user unless they request another language.

YOUR INFORMATION SOURCES:

1. Your general Gemini knowledge.
2. SignBridge project knowledge retrieved through RAG.
3. Current and persistent SignBridge app state.
4. Recent successful conversation history.

APP STATE:

Use CURRENT APP STATE for real user-specific SignBridge information such as:

- learning progress
- current education level
- current education stage
- completed levels
- scores
- latest reliable detected sound
- sound confidence
- sound severity
- recent Live Speech
- latest translated sign
- recent app activity

The app-state values are authoritative when present.

Never invent a missing app-state value.

If app state is missing, this must NOT stop you from answering unrelated general questions.

RAG:

Use RAG when the question is about:

- SignBridge
- SignBridge features
- project architecture
- sign translation
- Voice Assist
- Live Speech
- Smart Replies
- Speak for Me
- Education
- Dictionary
- Games
- SOS
- Avatar
- implementation details

Do NOT force RAG information into unrelated questions.

GENERAL QUESTIONS:

For general questions, answer normally using your general knowledge.

This includes:

- science
- programming
- mathematics
- writing
- translation
- ideas
- explanations
- technology
- everyday questions
- academic questions

Do NOT tell the user that you can only answer SignBridge questions.

CURRENT UI MODE:

{mode}

CURRENT SIGNBRIDGE APP STATE:

{state_text}

RELEVANT SIGNBRIDGE RAG KNOWLEDGE:

{knowledge_text}
""".strip()


# ============================================================
# CLEAN ONE SMART REPLY
# ============================================================

def _clean_reply(
    value: Any,
) -> str:

    text = str(
        value
        or ""
    ).strip()

    text = text.replace(
        "**",
        "",
    )

    text = re.sub(
        r"^\s*(?:R\s*)?"
        r"\d+\s*[.):-]\s*",
        "",
        text,
        flags=
            re.IGNORECASE,
    )

    text = re.sub(
        r"^\s*[-*•]\s*",
        "",
        text,
    )

    return (
        text
        .strip()
        .strip('"')
        .strip("'")
        .strip()
    )


# ============================================================
# UNIQUE SMART REPLIES
# ============================================================

def _unique_replies(
    values: list[
        Any
    ],
    limit: int = 6,
) -> list[str]:

    replies: list[str] = []

    seen: set[str] = set()

    for item in values:

        value = _clean_reply(
            item
        )

        if not value:
            continue

        key = re.sub(
            r"\s+",
            " ",
            value,
        ).casefold()

        if key in seen:
            continue

        seen.add(
            key
        )

        replies.append(
            value
        )

        if len(
            replies
        ) >= limit:
            break

    return replies


# ============================================================
# PARSE SMART REPLIES
# ============================================================

def parse_replies(
    raw: str,
    limit: int = 6,
) -> list[str]:

    text = (
        raw
        or ""
    ).strip()

    if not text:
        return []

    # Remove markdown code block.
    text = re.sub(
        r"^```(?:json)?\s*"
        r"|\s*```$",
        "",
        text,
        flags=
            re.IGNORECASE
            |
            re.DOTALL,
    ).strip()

    # ========================================================
    # JSON
    # ========================================================

    try:

        parsed = json.loads(
            text
        )

        if isinstance(
            parsed,
            list,
        ):

            return _unique_replies(
                parsed,
                limit,
            )

        if isinstance(
            parsed,
            dict,
        ):

            values = parsed.get(
                "replies"
            )

            if isinstance(
                values,
                list,
            ):

                return _unique_replies(
                    values,
                    limit,
                )

    except Exception:
        pass

    # ========================================================
    # NORMAL LINES
    # ========================================================

    replies = _unique_replies(
        text.splitlines(),
        limit,
    )

    if len(
        replies
    ) >= limit:

        return replies[
            :limit
        ]

    # ========================================================
    # SINGLE LINE OUTPUT
    # ========================================================

    for separator in (
        " || ",
        " | ",
        "; ",
    ):

        if separator in text:

            replies = _unique_replies(
                replies
                +
                text.split(
                    separator
                ),
                limit,
            )

        if len(
            replies
        ) >= limit:
            break

    return replies[
        :limit
    ]


# ============================================================
# SMART REPLY PROMPT
# ============================================================

def _smart_reply_prompt(
    heard_text: str,
) -> str:

    return f"""
A nearby person said exactly:

"{heard_text}"

Generate EXACTLY SIX short, natural replies the SignBridge user could say back.

Requirements:

- Every reply must directly fit the exact sentence that was heard.
- Make all six meaningfully different but relevant.
- Include positive, negative, uncertain, clarification, and useful follow-up options when appropriate.
- If it is a statement rather than a question, react naturally instead of forcing yes/no.
- Use the SAME LANGUAGE as the heard sentence.
- Keep each reply short and easy to speak.
- No explanation.
- No title.

Return exactly:

R1: ...
R2: ...
R3: ...
R4: ...
R5: ...
R6: ...
""".strip()


# ============================================================
# LOCAL SMART REPLY FALLBACK
# ============================================================

def _fallback_reply_set(
    heard_text: str,
) -> list[str]:

    text = (
        heard_text
        .strip()
    )

    lowered = (
        text.casefold()
    )

    has_arabic = bool(
        re.search(
            r"[\u0600-\u06FF]",
            text,
        )
    )

    question_starters = (
        "are ",
        "is ",
        "am ",
        "do ",
        "does ",
        "did ",
        "can ",
        "could ",
        "will ",
        "would ",
        "have ",
        "has ",
        "should ",
        "what ",
        "where ",
        "when ",
        "why ",
        "how ",
        "هل ",
        "وين ",
        "شو ",
        "متى ",
        "كيف ",
        "ليش ",
        "ممكن ",
    )

    contains_question_auxiliary = bool(
        re.search(
            r"\b("
            r"are|is|am|"
            r"do|does|did|"
            r"can|could|"
            r"will|would|"
            r"have|has|should"
            r")\b",
            lowered,
        )
    )

    is_question = (
        text.endswith("?")
        or
        lowered.startswith(
            question_starters
        )
        or
        contains_question_auxiliary
    )

    # ========================================================
    # ARABIC
    # ========================================================

    if has_arabic:

        if is_question:

            return [
                "نعم، أكيد.",
                "لا، مش هالمرة.",
                "مش متأكد بعد.",
                "ممكن توضّح أكتر؟",
                "شو التفاصيل؟",
                "خليني فكّر شوي وبخبرك.",
            ]

        return [
            "فهمت عليك.",
            "شكرًا لأنك خبرتني.",
            "ممكن توضّح أكتر؟",
            "شو بتحب أعمل؟",
            "ممكن تعيدها لو سمحت؟",
            "تمام، وصلت الفكرة.",
        ]

    # ========================================================
    # ENGLISH
    # ========================================================

    if is_question:

        return [
            "Yes, that works for me.",
            "No, not this time.",
            "I'm not sure yet.",
            "Could you explain a little more?",
            "What are the details?",
            "Give me a moment to think about it.",
        ]

    return [
        "I understand.",
        "Thanks for telling me.",
        "Could you explain a little more?",
        "What would you like me to do?",
        "Could you repeat that, please?",
        "Okay, I got it.",
    ]


# ============================================================
# GENERATE SIX SMART REPLIES
# ============================================================

def generate_smart_replies(
    heard_text: str,
) -> tuple[
    list[str],
    str,
]:

    replies: list[str] = []

    model_used = (
        "local-fallback"
    )

    try:

        raw, model_used = generate_text(
            contents=
                _smart_reply_prompt(
                    heard_text
                ),

            system_instruction=(
                "You are the Smart Reply engine "
                "inside SignBridge. "
                "Understand the exact nearby sentence "
                "and return exactly six short, distinct, "
                "context-appropriate reply options."
            ),

            max_output_tokens=
                260,

            temperature=
                0.55,

            main_attempts=
                1,
        )

        replies = parse_replies(
            raw,
            6,
        )

    except Exception as error:

        print(
            "SMART REPLIES AI WARNING:",
            repr(error),
        )

    # ========================================================
    # ALWAYS RETURN SIX
    # ========================================================

    if len(
        replies
    ) < 6:

        replies = _unique_replies(
            replies
            +
            _fallback_reply_set(
                heard_text
            ),
            6,
        )

    return (
        replies[
            :6
        ],
        model_used,
    )


# ============================================================
# HEALTH
# ============================================================

@chatbot_bp.get(
    "/api/chatbot/health"
)
def chatbot_health():

    return jsonify(
        {
            "success":
                True,

            "service":
                "SignBridge AI",

            "provider":
                "Google Gemini",

            "model":
                GEMINI_MODEL,

            "fallback_model":
                (
                    GEMINI_FALLBACK_MODEL
                    or
                    None
                ),

            "api_key_ready":
                bool(
                    os.getenv(
                        "GEMINI_API_KEY",
                        "",
                    ).strip()
                ),

            "rag_ready":
                len(
                    RAG.chunks
                ) > 0,

            "rag_chunks":
                len(
                    RAG.chunks
                ),

            "memory_ready":
                True,

            "free_question_mode":
                True,

            "smart_replies_count":
                6,

            "history_fix":
                True,

            "sound_context_endpoint":
                True,
        }
    )


# ============================================================
# CURRENT APP CONTEXT
# ============================================================

@chatbot_bp.get(
    "/api/chatbot/context"
)
def chatbot_context():

    return jsonify(
        {
            "success":
                True,

            "context":
                APP_MEMORY
                .build_context(),
        }
    )


# ============================================================
# SAVE APP EVENT
# ============================================================

@chatbot_bp.post(
    "/api/chatbot/context/event"
)
def chatbot_context_event():

    try:

        data = (
            request
            .get_json(
                silent=True
            )
            or {}
        )

        event_type = str(
            data.get(
                "type",
                "",
            )
        ).strip().lower()

        payload = data.get(
            "payload"
        )

        if not event_type:

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        "Context event type is required.",
                }
            ), 400

        if payload in (
            None,
            "",
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        "Context event payload is required.",
                }
            ), 400

        APP_MEMORY.record_context_event(
            event_type,
            payload,
        )

        print(
            "SIGNBRIDGE CONTEXT EVENT:",
            event_type,
            payload,
        )

        return jsonify(
            {
                "success":
                    True,

                "type":
                    event_type,
            }
        )

    except Exception as error:

        print(
            "CONTEXT EVENT ERROR:",
            repr(error),
        )

        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(error),
            }
        ), 500


# ============================================================
# RAG STATUS
# ============================================================

@chatbot_bp.get(
    "/api/chatbot/rag/status"
)
def chatbot_rag_status():

    return jsonify(
        {
            "success":
                True,

            "chunks":
                len(
                    RAG.chunks
                ),

            "knowledge_dir":
                str(
                    RAG
                    .knowledge_dir
                ),
        }
    )


# ============================================================
# RELOAD RAG
# ============================================================

@chatbot_bp.post(
    "/api/chatbot/rag/reload"
)
def chatbot_rag_reload():

    try:

        chunks = RAG.reload()

        return jsonify(
            {
                "success":
                    True,

                "chunks":
                    chunks,
            }
        )

    except Exception as error:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(error),
            }
        ), 500


# ============================================================
# MAIN CHAT
# ============================================================

@chatbot_bp.post(
    "/api/chatbot/message"
)
def chatbot_message():

    started = (
        time.perf_counter()
    )

    try:

        data = (
            request
            .get_json(
                silent=True
            )
            or {}
        )

        message = str(
            data.get(
                "message",
                "",
            )
        ).strip()

        mode = str(
            data.get(
                "mode",
                "chat",
            )
        ).strip().lower()

        if not mode:
            mode = "chat"

        if not message:

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        "Message cannot be empty.",
                }
            ), 400

        # ====================================================
        # SAVE CURRENT FLUTTER CONTEXT
        # ====================================================

        try:

            APP_MEMORY.ingest_app_context(
                data.get(
                    "app_context",
                    {},
                )
            )

        except Exception as error:

            print(
                "APP CONTEXT INGEST WARNING:",
                repr(error),
            )

        # ====================================================
        # OLD SMART REPLY COMPATIBILITY
        # ====================================================

        if mode == "smart_reply":

            replies, model_used = (
                generate_smart_replies(
                    message
                )
            )

            return jsonify(
                {
                    "success":
                        True,

                    "mode":
                        "smart_reply",

                    "replies":
                        replies,

                    "reply":
                        "\n".join(
                            replies
                        ),

                    "count":
                        len(
                            replies
                        ),

                    "model":
                        model_used,

                    "latency_ms":
                        int(
                            (
                                time
                                .perf_counter()
                                -
                                started
                            )
                            *
                            1000
                        ),
                }
            )

        # ====================================================
        # RAG
        # ====================================================

        rag_context = ""

        rag_hits: list[
            dict[
                str,
                Any,
            ]
        ] = []

        try:

            (
                rag_context,
                rag_hits,
            ) = RAG.build_context(
                message,
                k=4,
                max_chars=3600,
            )

        except Exception as error:

            print(
                "RAG RETRIEVAL WARNING:",
                repr(error),
            )

        # ====================================================
        # CURRENT APP STATE
        # ====================================================

        try:

            app_state = (
                APP_MEMORY
                .build_context()
            )

        except Exception as error:

            print(
                "APP MEMORY READ WARNING:",
                repr(error),
            )

            app_state = {}

        # ====================================================
        # HISTORY
        # ====================================================

        history = clean_history(
            data.get(
                "history",
                [],
            )
        )

        # ====================================================
        # GEMINI CONTENTS
        # ====================================================

        contents = build_contents(
            history,
            message,
        )

        instruction = (
            build_assistant_instruction(
                rag_context=
                    rag_context,

                app_state=
                    app_state,

                mode=
                    mode,
            )
        )

        # ====================================================
        # MAIN AI
        # ====================================================

        try:

            reply, model_used = (
                generate_text(
                    contents=
                        contents,

                    system_instruction=
                        instruction,

                    max_output_tokens=
                        780,

                    temperature=
                        0.35,

                    main_attempts=
                        2,
                )
            )

        except Exception as full_error:

            if _is_quota_error(
                full_error
            ):

                return jsonify(
                    {
                        "success":
                            False,

                        "error_type":
                            "quota",

                        "message":
                            (
                                "SignBridge AI reached "
                                "the current Gemini quota. "
                                "Please try again shortly."
                            ),
                    }
                ), 429

            print(
                "FULL CONTEXT CHAT WARNING:",
                repr(
                    full_error
                ),
            )

            # =================================================
            # ONE LIGHT RETRY
            # =================================================

            reply, model_used = (
                generate_text(
                    contents=
                        contents,

                    system_instruction=
                        (
                            "You are SignBridge AI, "
                            "a general-purpose AI assistant. "
                            "The newest user request has "
                            "absolute priority. "
                            "Answer any normal question in "
                            "the user's language. "
                            "Do not restrict the user to "
                            "SignBridge topics or preset questions."
                        ),

                    max_output_tokens=
                        650,

                    temperature=
                        0.35,

                    main_attempts=
                        1,
                )
            )

        # ====================================================
        # RETURN ANSWER
        # ====================================================

        return jsonify(
            {
                "success":
                    True,

                "reply":
                    reply,

                "mode":
                    mode,

                "provider":
                    (
                        "Google Gemini + "
                        "SignBridge RAG + "
                        "App Context"
                    ),

                "model":
                    model_used,

                "rag_used":
                    bool(
                        rag_hits
                    ),

                "rag_sources":
                    [
                        {
                            "source":
                                item.get(
                                    "source"
                                ),

                            "title":
                                item.get(
                                    "title"
                                ),

                            "score":
                                item.get(
                                    "score"
                                ),
                        }

                        for item
                        in rag_hits[
                            :4
                        ]
                    ],

                "latency_ms":
                    int(
                        (
                            time
                            .perf_counter()
                            -
                            started
                        )
                        *
                        1000
                    ),
            }
        )

    except Exception as error:

        print(
            "SIGNBRIDGE CHAT ERROR:",
            repr(error),
        )

        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(error),
            }
        ), 500


# ============================================================
# SMART REPLIES ROUTE
# ============================================================

@chatbot_bp.post(
    "/api/chatbot/smart-replies"
)
def chatbot_smart_replies():

    started = (
        time.perf_counter()
    )

    try:

        data = (
            request
            .get_json(
                silent=True
            )
            or {}
        )

        heard_text = str(
            data.get(
                "heard_text"
            )
            or
            data.get(
                "message"
            )
            or
            ""
        ).strip()

        if not heard_text:

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        "No recent speech was provided.",
                }
            ), 400

        # ====================================================
        # SAVE SPEECH TO MEMORY
        # ====================================================

        try:

            APP_MEMORY.record_context_event(
                "speech",

                {
                    "text":
                        heard_text,
                },
            )

        except Exception as error:

            print(
                "SMART REPLY MEMORY WARNING:",
                repr(error),
            )

        # ====================================================
        # GENERATE SIX
        # ====================================================

        replies, model_used = (
            generate_smart_replies(
                heard_text
            )
        )

        return jsonify(
            {
                "success":
                    True,

                "replies":
                    replies,

                "reply":
                    "\n".join(
                        replies
                    ),

                "count":
                    len(
                        replies
                    ),

                "model":
                    model_used,

                "latency_ms":
                    int(
                        (
                            time
                            .perf_counter()
                            -
                            started
                        )
                        *
                        1000
                    ),
            }
        )

    except Exception as error:

        print(
            "SMART REPLIES ERROR:",
            repr(error),
        )

        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(error),
            }
        ), 500


# ============================================================
# SPEAK FOR ME
# ============================================================

@chatbot_bp.post(
    "/api/chatbot/speak-for-me"
)
def chatbot_speak_for_me():

    started = (
        time.perf_counter()
    )

    try:

        data = (
            request
            .get_json(
                silent=True
            )
            or {}
        )

        text = str(
            data.get(
                "text"
            )
            or
            data.get(
                "message"
            )
            or
            ""
        ).strip()

        if not text:

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        "Text cannot be empty.",
                }
            ), 400

        # ====================================================
        # EXACT TEXT
        #
        # No Gemini rewriting.
        # ====================================================

        return jsonify(
            {
                "success":
                    True,

                "reply":
                    text,

                "model":
                    "local-exact-text",

                "latency_ms":
                    int(
                        (
                            time
                            .perf_counter()
                            -
                            started
                        )
                        *
                        1000
                    ),
            }
        )

    except Exception as error:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(error),
            }
        ), 500