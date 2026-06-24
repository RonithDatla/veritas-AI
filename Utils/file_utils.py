import streamlit as st
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import json
from PIL import Image

@st.cache_data
def read_pdf_cached(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))

    pages = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    return pages
# ------------------ MAIN FILE ROUTER ------------------

def extract_file_text(file):
    file_bytes = file.getvalue()
    file_type = file.type or ""

    if file_type.startswith("image"):
        return Image.open(BytesIO(file_bytes)), None

    if "pdf" in file_type:
        return None, read_pdf_cached(file_bytes)  # ✅ now returns pages

    elif "word" in file_type:
        return None, read_docx_cached(file_bytes)

    else:
        return None, read_txt_cached(file_bytes)


# ------------------ RESPONSE TEXT ------------------

def extract_text(response):
    if hasattr(response, "text") and response.text:
        return response.text
    try:
        return response.candidates[0].content.parts[0].text
    except:
        return "⚠️ No response text found"



# ------------------ OTHER FILE TYPES ------------------

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


@st.cache_data
def read_md_cached(file_bytes):
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except:
        return None


@st.cache_data
def read_html_cached(file_bytes):
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except:
        return None
