import streamlit as st
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd
import json

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