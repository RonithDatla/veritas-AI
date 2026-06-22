import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO

from config import get_config, MODE_MAP, MODEL_OPTIONS
from file_utils import *
from formatting import clean_output
from genai_utils import extract_text
from yt_utils import get_youtube_transcript
from pdf_utils import create_pdf

def create_chat():
    return st.session_state.client.chats.create(
        model=st.session_state.model,
        config=get_config(st.session_state.mode)
    )

# ------------------ CONSTANTS ------------------

REPORT_PROMPT = """
You are an expert research analyst.

Generate a high-quality structured report using:
1. Title
2. Abstract
3. Key Insights
4. Detailed Analysis
5. Key Takeaways
6. Conclusion
Be precise, structured, and analytical.
"""

POLISH_PROMPT = """
You are an academic editor.

Rewrite using:
- British English
- formal academic tone
- improved grammar & punctuation
- preserve meaning
"""

# ------------------ FILE HANDLING ------------------

def extract_file_text(file):
    file_bytes = file.getvalue()
    file_type = file.type or ""

    if file_type.startswith("image"):
        return Image.open(BytesIO(file_bytes)), None

    if "pdf" in file_type:
        return None, read_pdf_cached(file_bytes)
    elif "word" in file_type:
        return None, read_docx_cached(file_bytes)
    else:
        return None, read_txt_cached(file_bytes)

# ------------------ APP ------------------

st.set_page_config(page_title="Veritas AI", layout="wide")
st.title("🔍 Veritas AI")

# ------------------ API ------------------

if "client" not in st.session_state:
    st.session_state.client = genai.Client()

# ------------------ STATE ------------------

for key, default in {
    "mode": "balanced",
    "model": MODEL_OPTIONS[0],
    "messages": [],
    "report_output": None,
    "polish_output": None,
    "yt_output": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ------------------ MAIN CHAT ------------------

if "chat_main" not in st.session_state:
    st.session_state.chat_main = create_chat()

# ------------------ SIDEBAR ------------------

with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat_main = create_chat()
        st.rerun()

    reverse_map = {v: k for k, v in MODE_MAP.items()}
    current_display = reverse_map.get(st.session_state.mode)

    selected_display = st.selectbox(
        "Mode",
        list(MODE_MAP.keys()),
        index=list(MODE_MAP.keys()).index(current_display)
    )

    selected_mode = MODE_MAP[selected_display]

    if selected_mode != st.session_state.mode:
        st.session_state.mode = selected_mode
        st.session_state.chat_main = create_chat()
        st.rerun()

    selected_model = st.selectbox(
        "Model",
        MODEL_OPTIONS,
        index=MODEL_OPTIONS.index(st.session_state.model)
    )

    if selected_model != st.session_state.model:
        st.session_state.model = selected_model
        st.session_state.chat_main = create_chat()
        st.rerun()

# ------------------ LAYOUT ------------------

col_main, col_right = st.columns([4, 1.2])

# ------------------ RIGHT PANEL ------------------

with col_right:
    st.markdown("## 🧰 Tools")

    # ---------- REPORT ----------
    with st.expander("📄 Generate Report"):

        report_instruction = st.text_area("Instructions")
        report_file = st.file_uploader("Upload file")

        report_text, report_image = None, None

        if report_file:
            report_image, report_text = extract_file_text(report_file)
            if report_image:
                st.image(report_image)

        if st.button("Generate Report"):

            if not report_instruction and not report_file:
                st.warning("Provide input.")
                st.stop()

            content = REPORT_PROMPT + "\n\n"

            if report_instruction:
                content += report_instruction + "\n\n"

            if report_text:
                content += report_text[:15000]

            #stateless tool chat
            chat = create_chat()

            if report_image:
                response = chat.send_message([content, report_image])
            else:
                response = chat.send_message(content)

            st.session_state.report_output = clean_output(extract_text(response))

        if st.session_state.report_output:
            st.download_button(
                "⬇️ Download Report",
                create_pdf(st.session_state.report_output),
                "report.pdf"
            )

    # ---------- POLISH ----------
    with st.expander("✍️ Polish Academic Document"):

        polish_file = st.file_uploader("Upload document")

        if st.button("Polish"):

            if not polish_file:
                st.warning("Upload a document.")
                st.stop()

            _, text = extract_file_text(polish_file)

            if not text:
                st.error("Could not extract text.")
                st.stop()

            chat = create_chat()

            response = chat.send_message(
                POLISH_PROMPT + "\n\n" + text[:15000]
            )

            st.session_state.polish_output = clean_output(extract_text(response))

        if st.session_state.polish_output:
            st.download_button(
                "⬇️ Download Polished",
                create_pdf(st.session_state.polish_output),
                "polished.pdf"
            )

    # ---------- YOUTUBE ----------
    with st.expander("🎥 Summarize YouTube"):

        yt_url = st.text_input("YouTube URL")

        if st.button("Summarize"):

            if not yt_url:
                st.warning("Provide URL.")
                st.stop()

            transcript = get_youtube_transcript(yt_url)

            if not transcript:
                st.error("No transcript available.")
            else:
                chat = create_chat()

                response = chat.send_message(
                    REPORT_PROMPT + "\n\n" + transcript[:15000]
                )

                st.session_state.yt_output = clean_output(extract_text(response))

        if st.session_state.yt_output:
            st.download_button(
                "⬇️ Download Summary",
                create_pdf(st.session_state.yt_output),
                "youtube_summary.pdf"
            )

# ------------------ CHAT ------------------

with col_main:

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask something...")

    if user_input:

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        response = st.session_state.chat_main.send_message(user_input)
        clean_text = clean_output(extract_text(response))

        st.session_state.messages.append({
            "role": "assistant",
            "content": clean_text
        })

        st.rerun()