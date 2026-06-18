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

# ------------------ PDF CREATION ------------------
def create_pdf(text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter
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
    return file.read().decode("utf-8")


def read_csv(file):
    return pd.read_csv(file).to_string()


def read_excel(file):
    return pd.read_excel(file).to_string()


def read_json(file):
    return json.dumps(json.load(file), indent=2)


# ------------------ APP ------------------
st.set_page_config(page_title="Veritas", layout="wide")
st.title("Veritas")

# ------------------ INIT CLIENT ------------------
if "client" not in st.session_state:
    st.session_state.client = genai.Client()

if "chat" not in st.session_state:
    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-3.5-flash"
    )

if "messages" not in st.session_state:
    st.session_state.messages = []


# ------------------ ATTACHMENT INPUT ------------------
uploaded_file = st.file_uploader(
    "Attach a file",
    type=["png", "jpg", "jpeg", "pdf", "txt", "docx", "csv", "json", "xlsx"]
)

image = None
file_text = None

if uploaded_file:
    file_type = uploaded_file.type

    if file_type.startswith("image"):
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)

    elif file_type == "application/pdf":
        file_text = read_pdf(uploaded_file)

    elif file_type == "text/plain":
        file_text = read_txt(uploaded_file)

    elif "wordprocessingml" in file_type:
        file_text = read_docx(uploaded_file)

    elif file_type == "text/csv":
        file_text = read_csv(uploaded_file)

    elif file_type == "application/json":
        file_text = read_json(uploaded_file)

    elif "spreadsheetml" in file_type:
        file_text = read_excel(uploaded_file)


# ------------------ IMAGE REPORT OPTIONS ------------------
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

        pdf_file = create_pdf(response.text)

        st.download_button(
            label="Download PDF",
            data=pdf_file,
            file_name="report.pdf",
            mime="application/pdf"
        )


# ------------------ DISPLAY CHAT ------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ------------------ USER INPUT ------------------
user_input = st.chat_input("Ask something...")

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            if file_text:
                prompt = f"""
                Use this document as reference:

                {file_text[:15000]}

                Answer the question:
                {user_input}
                """
                response = st.session_state.chat.send_message(prompt)

            elif image:
                response = st.session_state.chat.send_message([
                    user_input,
                    image
                ])

            else:
                response = st.session_state.chat.send_message(user_input)

            st.markdown(response.text)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response.text
            })

        except Exception as e:
            st.error(f"Error: {e}")