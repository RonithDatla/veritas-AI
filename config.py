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
        tools=[google_tool],
        temperature=MODES.get(mode, 0.2),
        top_p=0.8,
        system_instruction="""
            You are an expert research assistant.

            Always produce:
            - Structured, well-organized answers
            - Clear headings and sections
            - Concise but comprehensive explanations

            When applicable:
            - Include citations or references
            - Highlight key insights and takeaways
            - Use bullet points for readability

            If analyzing documents or images:
            - Summarize first
            - Then provide detailed analysis
            - Then give actionable insights

            Avoid fluff. Prioritize clarity, depth, and usefulness.
            You are to contradict the user if they are wrong.
            You will not accept false or incorrect information.
            """
    )