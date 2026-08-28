import os

from dotenv import load_dotenv
from google import genai


# ============================================================
# LOAD .ENV
# ============================================================

load_dotenv()


# ============================================================
# API KEY
# ============================================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY was not found in backend/.env"
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=api_key
)


# ============================================================
# TEST
# ============================================================

print()
print("=" * 60)
print("SIGNBRIDGE - GEMINI API TEST")
print("=" * 60)
print()

try:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=(
            "You are SignBridge AI. "
            "Introduce yourself in one short sentence."
        ),
    )

    print("GEMINI RESPONSE:")
    print()
    print(response.text)

    print()
    print("=" * 60)
    print("TEST SUCCESSFUL")
    print("=" * 60)

except Exception as error:
    print()
    print("=" * 60)
    print("TEST FAILED")
    print("=" * 60)
    print()
    print(error)