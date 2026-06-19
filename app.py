import streamlit as st
from google import genai
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import json
import os
import re
from config import get_config, MODE_MAP, MODEL_OPTIONS

# ------------------ CONSTANTS ------------------
IMAGE_PROMPT = "Write a detailed research report 2 pages long about this image."

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

# ------------------ FILE READERS ------------------
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

# ------------------ OUTPUT CLEANING ------------------
def clean_output(text):
    patterns = [
        "Search Queries:",
        "Metadata Search Queries:",
        "Search queries:",
        "Metadata:"
    ]
    for p in patterns:
        if p in text:
            text = text.split(p)[0]
    return text.strip()

def make_links_clickable(text):
    url_pattern = r'(https?://[^\s]+)'
    return re.sub(url_pattern, r'\1', text)

# ------------------ APP ------------------
st.set_page_config(page_title="Veritas AI", layout="wide")
st.title("Veritas AI")

# ------------------ API ------------------
if "client" not in st.session_state:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Missing API key.")
        st.stop()

    st.session_state.client = genai.Client(api_key=api_key)

# ------------------ STATE ------------------
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

#DRY CHAT CREATION
def create_chat():
    return st.session_state.client.chats.create(
        model=st.session_state.model,
        config=get_config(st.session_state.mode)
    )

# ------------------ INIT CHAT ------------------
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
    current_display = reverse_map[st.session_state.mode]

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

# ------------------ CHAT DISPLAY ------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------ CHAT ------------------
user_input = st.chat_input("Ask something...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

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

            # ✅ SAFE RESPONSE EXTRACTION (CRITICAL FIX)
            output_text = ""

            if hasattr(response, "text") and response.text:
                output_text = response.text
            elif hasattr(response, "candidates"):
                try:
                    output_text = response.candidates[0].content.parts[0].text
                except:
                    output_text = "⚠️ Model returned no readable output."
            else:
                output_text = "⚠️ No response from model."

            # ✅ CLEAN + FORMAT
            clean_text = clean_output(output_text)
            formatted_text = make_links_clickable(clean_text)

            st.markdown(formatted_text)

            st.session_state.messages.append({
                "role": "assistant",
                "content": formatted_text
            })
