from google.genai import types

MAX_DIRECT_CHARS = 12000
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 3

# ------------------ MODES ------------------
MODES = {
    "precise": 0.1,
    "balanced": 0.2,
    "creative": 0.6
}

# ------------------ UI MAPPING ------------------
MODE_MAP = {
    "🎯 Precise": "precise",
    "⚖️ Balanced": "balanced",
    "🎨 Creative": "creative"
}

# ------------------ MODELS ------------------
MODEL_OPTIONS = ["gemini-2.5-flash", "gemini-3.5-flash"]

# ------------------ GOOGLE TOOL ------------------
google_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# ------------------ CONFIG ------------------
def get_config(mode: str):
    return types.GenerateContentConfig(
        tools=[google_tool],  # ✅ FIXED
        temperature=MODES.get(mode, 0.2),
        top_p=0.8,
        system_instruction="""
You are an expert research assistant.

Always:
- Use Google Search when answering factual or up-to-date questions
- Provide accurate and verifiable information

When using external information:
- Base your answer ONLY on retrieved data
- Ensure correctness and reliability

Structure:
- Use clear headings
- Be concise but informative

Avoid speculation. Prefer verified information.
"""
    )