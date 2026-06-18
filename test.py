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

        c.drawString(40, y, line[:90])
        y -= 15

    c.save()
    buffer.seek(0)
    return buffer


# ------------------ FILE READERS ------------------
def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])


def read_txt(file):
    return file.read().decode("utf-8", errors="ignore")


def read_csv(file):
    return pd.read_csv(file).to_string()


def read_excel(file):
    return pd.read_excel(file).to_string()


def read_json(file):
    return json.dumps(json.load(file), indent=2)


# ------------------ APP ------------------
st.set_page_config(page_title="🔍 Veritas AI", layout="wide")
st.title("🔍 Veritas AI")

# ------------------ STATES ------------------
MODES = {
    "precise": 0.1,
    "balanced": 0.2,
    "creative": 0.6
}

# ✅ display → actual value
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

if "client" not in st.session_state:
    st.session_state.client = genai.Client()


# ------------------ CONFIG ------------------
def get_config():
    return types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=MODES[st.session_state.mode],
        top_p=0.8,
        system_instruction="""
        You are a research assistant.
        Always include citations.
        Base answers on verifiable data.
        Be truthful.
        """
    )


# ------------------ INIT CHAT ------------------
if "chat" not in st.session_state:
    st.session_state.chat = st.session_state.client.chats.create(
        model=st.session_state.model,
        config=get_config()
    )

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🧹 Clear Chat"):
        st.session_state.chat = st.session_state.client.chats.create(
            model=st.session_state.model,
            config=get_config()
        )
        st.session_state.messages = []
        st.rerun()

    with st.expander("💻 Commands"):
        st.markdown("- /help")
        st.markdown("- /clear")

    # ✅ reverse mapping to get display label
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
        st.session_state.messages = []
        st.rerun()

    selected_model = st.selectbox(
        "Model",
        MODEL_OPTIONS,
        index=MODEL_OPTIONS.index(st.session_state.model)
    )

    if selected_model != st.session_state.model:
        st.session_state.model = selected_model
        st.session_state.chat = st.session_state.client.chats.create(
            model=st.session_state.model,
            config=get_config()
        )
        st.session_state.messages = []
        st.rerun()


# ------------------ ATTACHMENT ------------------
uploaded_file = st.file_uploader(
    "Attach file",
    type=["png", "jpg", "jpeg", "pdf", "txt", "docx", "csv", "json", "xlsx"]
)

image = None
file_text = None

if uploaded_file:
    file_type = uploaded_file.type or ""

    if file_type.startswith("image"):
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)

    elif "pdf" in file_type:
        file_text = read_pdf(uploaded_file)

    elif file_type == "text/plain":
        file_text = read_txt(uploaded_file)

    elif "wordprocessingml" in file_type:
        file_text = read_docx(uploaded_file)

    elif "csv" in file_type:
        file_text = read_csv(uploaded_file)

    elif "json" in file_type:
        file_text = read_json(uploaded_file)

    elif "spreadsheetml" in file_type:
        file_text = read_excel(uploaded_file)


# ------------------ IMAGE REPORT ------------------
if image:
    col1, col2 = st.columns(2)

    generate_btn = col1.button("Generate Report")
    download_btn = col2.button("Download PDF Report")

    if generate_btn:
        with st.chat_message("assistant"):
            response = st.session_state.chat.send_message([
                "Write a detailed research report about this image.",
                image
            ])
            st.markdown(response.text)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.text
            })

    if download_btn:
        response = st.session_state.chat.send_message([
            "Write a detailed research report about this image.",
            image
        ])
        pdf = create_pdf(response.text)

        st.download_button("Download PDF", pdf, "report.pdf", "application/pdf")


# ------------------ DISPLAY CHAT ------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ------------------ CHAT INPUT ------------------
user_input = st.chat_input("Ask something...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            if file_text:
                prompt = f"""
                Use this document:

                {file_text[:15000]}

                Question:
                {user_input}
                """
                response = st.session_state.chat.send_message(prompt)

            elif image:
                response = st.session_state.chat.send_message([user_input, image])

            else:
                response = st.session_state.chat.send_message(user_input)

            st.markdown(response.text)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.text
            })

        except Exception as e:
            st.error(f"Error: {e}")