import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import json
import os

# ------------------ CONSTANTS ------------------
IMAGE_PROMPT = "Write a detailed research report about this image."

# ------------------ PDF CREATION ------------------
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

# ------------------ FILE READERS (CACHED) ------------------

@st.cache_data
def read_pdf_cached(file_bytes):
    try:
        reader = PdfReader(BytesIO(file_bytes))
        return "".join([p.extract_text() or "" for p in reader.pages])
    except:
        return None

@st.cache_data
def read_docx_cached(file_bytes):
    try:
        return "\n".join([p.text for p in Document(BytesIO(file_bytes)).paragraphs])
    except:
        return None

@st.cache_data
def read_txt_cached(file_bytes):
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except:
        return None

@st.cache_data
def read_csv_cached(file_bytes):
    try:
        return pd.read_csv(BytesIO(file_bytes)).to_string()
    except:
        return None

@st.cache_data
def read_excel_cached(file_bytes):
    try:
        return pd.read_excel(BytesIO(file_bytes)).to_string()
    except:
        return None

@st.cache_data
def read_json_cached(file_bytes):
    try:
        return json.dumps(json.loads(file_bytes.decode("utf-8")), indent=2)
    except:
        return None

# ------------------ APP ------------------
st.set_page_config(page_title="Veritas AI", layout="wide")
st.title("Veritas AI")

# ------------------ API KEY ------------------
if "client" not in st.session_state:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            st.error("Missing API key try renaming it to GEMINI_API_KEY")
            st.stop()
    st.session_state.client = genai.Client(api_key=api_key)

# ------------------ STATES ------------------
MODES = {
    "precise": 0.1,
    "balanced": 0.2,
    "creative": 0.6
}

MODE_MAP = {
    "🎯 Precise": "precise",
    "⚖️ Balanced": "balanced",
    "🎨 Creative": "creative"
}

MODEL_OPTIONS = ["gemini-2.5-flash", "gemini-3.5-flash"]

if "mode" not in st.session_state:
    st.session_state.mode = "balanced"

if "model" not in st.session_state:
    st.session_state.model = "gemini-3.5-flash"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "file_text" not in st.session_state:
    st.session_state.file_text = None

if "image" not in st.session_state:
    st.session_state.image = None

if "last_report" not in st.session_state:
    st.session_state.last_report = None

# ------------------ CONFIG ------------------
google_tool = types.Tool(google_search=types.GoogleSearch())

def get_config():
    return types.GenerateContentConfig(
        tools=[google_tool],
        temperature=MODES[st.session_state.mode],
        top_p=0.8,
        system_instruction="You are a research assistant. Always include citations."
    )

# ------------------ INIT CHAT ------------------
if "chat" not in st.session_state:
    st.session_state.chat = st.session_state.client.chats.create(
        model=st.session_state.model,
        config=get_config()
    )

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.session_state.chat = st.session_state.client.chats.create(
            model=st.session_state.model,
            config=get_config()
        )
        st.rerun()

    with st.expander("💻 Commands"):
        st.markdown("- /help")
        st.markdown("- /clear")

    reverse_map = {v: k for k, v in MODE_MAP.items()}
    current_display = reverse_map[st.session_state.mode]

    selected_display = st.selectbox(
        "Mode",
        list(MODE_MAP.keys()),
        index=list(MODE_MAP.keys()).index(current_display)
    )

    selected_mode = MODE_MAP[selected_display]

    if selected_mode != st.session_state.mode:
        st.session_state.mode = selected_mode
        st.session_state.chat = st.session_state.client.chats.create(
            model=st.session_state.model,
            config=get_config()
        )
        st.rerun()

    selected_model = st.selectbox(
        "Model",
        MODEL_OPTIONS,
        index=MODEL_OPTIONS.index(st.session_state.model)
    )

    if selected_model != st.session_state.model:
        st.session_state.model = selected_model
        st.session_state.chat = st.session_state.client.chats.create(
            model=selected_model,
            config=get_config()
        )
        st.rerun()

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader("Attach file")

if uploaded_file:
    file_type = uploaded_file.type or ""
    file_bytes = uploaded_file.read()

    if file_type.startswith("image"):
        st.session_state.image = Image.open(BytesIO(file_bytes))
        st.session_state.file_text = None
        st.image(st.session_state.image)

    else:
        st.session_state.image = None

        if "pdf" in file_type:
            text = read_pdf_cached(file_bytes)
        elif "word" in file_type:
            text = read_docx_cached(file_bytes)
        elif file_type == "text/plain":
            text = read_txt_cached(file_bytes)
        elif "csv" in file_type:
            text = read_csv_cached(file_bytes)
        elif "json" in file_type:
            text = read_json_cached(file_bytes)
        elif "spreadsheet" in file_type:
            text = read_excel_cached(file_bytes)
        else:
            text = None

        st.session_state.file_text = text

        if text and len(text) > 15000:
            st.warning("Document is large. Only part of it will be used.")

# ------------------ IMAGE REPORT ------------------
if st.session_state.image:
    col1, col2 = st.columns(2)

    if col1.button("Generate Report"):
        st.session_state.messages.append({
            "role": "user",
            "content": "Generate report from image"
        })

        with st.chat_message("assistant"):
            with st.spinner("Analyzing image..."):
                response = st.session_state.chat.send_message(
                    [IMAGE_PROMPT, st.session_state.image]
                )
                st.markdown(response.text)
                st.session_state.last_report = response.text
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.text
                })

    if col2.button("Download PDF Report"):
        if not st.session_state.last_report:
            st.warning("Generate a report first")
        else:
            pdf = create_pdf(st.session_state.last_report)
            st.download_button("Download PDF", pdf, "report.pdf", "application/pdf")

# ------------------ DISPLAY CHAT ------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------ CHAT ------------------
user_input = st.chat_input("Ask something...")

if user_input:

    if user_input.lower() == "/clear":
        st.session_state.messages = []
        st.rerun()

    elif user_input.lower() == "/help":
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Commands: /help, /clear"
        })
        st.rerun()

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            if st.session_state.file_text:
                prompt = f"{st.session_state.file_text[:15000]}\n\n{user_input}"
                response = st.session_state.chat.send_message(prompt)

            elif st.session_state.image:
                response = st.session_state.chat.send_message(
                    [user_input, st.session_state.image]
                )

            else:
                response = st.session_state.chat.send_message(user_input)

            st.markdown(response.text)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.text
            })