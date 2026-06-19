import streamlit as st
from google import genai
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import os
from youtube_transcript_api import YouTubeTranscriptApi

from config import get_config, MODE_MAP, MODEL_OPTIONS
from file_utils import *
from formatting import clean_output, make_links_clickable

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

# ------------------ YOUTUBE ------------------
def get_youtube_transcript(url):
    try:
        import re

        match = re.search(r"(v=|youtu\.be/)([^&?/]+)", url)
        if not match:
            print("Invalid URL")
            return None

        video_id = match.group(2)

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        print("Available transcripts:", transcript_list)

        # ✅ Try ALL transcripts one by one
        for transcript in transcript_list:
            try:
                print("Trying:", transcript)
                result = transcript.fetch()

                text = " ".join([t["text"] for t in result])
                if text.strip():
                    return text

            except Exception as e:
                print("Fetch failed:", e)

        # ✅ Try translation fallback
        for transcript in transcript_list:
            try:
                print("Trying translate:", transcript)
                result = transcript.translate("en").fetch()

                text = " ".join([t["text"] for t in result])
                if text.strip():
                    return text

            except Exception as e:
                print("Translate failed:", e)

        print("All transcript attempts failed")
        return None

    except Exception as e:
        print("Transcript error:", e)
        return None
    
# ------------------ PDF ------------------

def create_pdf(text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    height = letter[1]
    y = height - 40

    for line in text.split("\n"):
        if y < 40:
            c.showPage()
            y = height - 40
        c.setFont("Helvetica", 10)
        c.drawString(40, y, line[:100])
        y -= 15

    c.save()
    buffer.seek(0)
    return buffer

# ------------------ APP ------------------

st.set_page_config(page_title="Veritas AI", layout="wide")
st.title("🔍 Veritas AI")

# ------------------ API ------------------

if "client" not in st.session_state:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Missing API key.")
        st.stop()
    st.session_state.client = genai.Client(api_key=api_key)

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

# ------------------ CHAT ------------------

def create_chat():
    return st.session_state.client.chats.create(
        model=st.session_state.model,
        config=get_config(st.session_state.mode)
    )

if "chat" not in st.session_state:
    st.session_state.chat = create_chat()

# ------------------ SIDEBAR ------------------

with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat = create_chat()
        st.rerun()

    reverse_map = {v: k for k, v in MODE_MAP.items()}
    current_display = reverse_map.get(st.session_state.mode, list(MODE_MAP.keys())[0])

    selected_display = st.selectbox(
        "Mode",
        list(MODE_MAP.keys()),
        index=list(MODE_MAP.keys()).index(current_display)
    )

    selected_mode = MODE_MAP[selected_display]

    if selected_mode != st.session_state.mode:
        st.session_state.mode = selected_mode
        st.session_state.chat = create_chat()
        st.rerun()

    selected_model = st.selectbox(
        "Model",
        MODEL_OPTIONS,
        index=MODEL_OPTIONS.index(st.session_state.model)
    )

    if selected_model != st.session_state.model:
        st.session_state.model = selected_model
        st.session_state.chat = create_chat()
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

        report_text = None
        report_image = None

        if report_file:
            file_bytes = report_file.getvalue()
            file_type = report_file.type or ""

            if file_type.startswith("image"):
                report_image = Image.open(BytesIO(file_bytes))
                st.image(report_image)
            else:
                if "pdf" in file_type:
                    report_text = read_pdf_cached(file_bytes)
                elif "word" in file_type:
                    report_text = read_docx_cached(file_bytes)
                else:
                    report_text = read_txt_cached(file_bytes)

        if st.button("Generate Report", key="report_btn"):
            if not report_instruction and not report_file:
                st.warning("Provide input.")
                st.stop()

            content = REPORT_PROMPT + "\n\n"

            if report_instruction:
                content += report_instruction + "\n\n"
            if report_text:
                content += report_text[:15000]

            if report_image:
                response = st.session_state.chat.send_message([content, report_image])
            else:
                response = st.session_state.chat.send_message(content)

            st.session_state.report_output = clean_output(
                getattr(response, "text", response.candidates[0].content.parts[0].text)
            )

        if st.session_state.report_output:
            st.download_button(
                "⬇️ Download Report",
                create_pdf(st.session_state.report_output),
                "report.pdf"
            )

    # ---------- POLISH ----------
    with st.expander("✍️ Polish Academic Document"):

        polish_file = st.file_uploader("Upload document", key="polish_upload")

        if st.button("Polish", key="polish_btn"):

            if not polish_file:
                st.warning("Upload a document.")
                st.stop()

            text = read_txt_cached(polish_file.getvalue())

            response = st.session_state.chat.send_message(
                POLISH_PROMPT + "\n\n" + text[:15000]
            )

            st.session_state.polish_output = clean_output(
                getattr(response, "text", response.candidates[0].content.parts[0].text)
            )

        if st.session_state.polish_output:
            st.download_button(
                "⬇️ Download Polished",
                create_pdf(st.session_state.polish_output),
                "polished.pdf"
            )

    # ---------- YOUTUBE ----------
    with st.expander("🎥 Summarize YouTube Video"):

        yt_url = st.text_input("YouTube URL")

        if st.button("Summarize Video", key="yt_btn"):

            if not yt_url:
                st.warning("Provide a link.")
                st.stop()

            transcript = get_youtube_transcript(yt_url)

            if not transcript:
                st.error("No transcript available.")
            else:
                response = st.session_state.chat.send_message(
                    REPORT_PROMPT + "\n\n" + transcript[:15000]
                )

                try:
                    output_text = response.text
                except:
                    output_text = response.candidates[0].content.parts[0].text

                st.session_state.yt_output = clean_output(output_text)

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
        response = st.session_state.chat.send_message(user_input)

        output_text = getattr(
            response,
            "text",
            response.candidates[0].content.parts[0].text
        )

        clean_text = clean_output(output_text)

        st.session_state.messages.append({
            "role": "assistant",
            "content": clean_text
        })

        st.rerun()