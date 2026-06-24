import streamlit as st

from Services.genai_client import get_client
from Core.chat_engine import create_chat

from UI.sidebar import render_sidebar
from UI.tools_panel import render_tools
from UI.chat_ui import render_chat

from config import MODEL_OPTIONS


# ---------- CONFIG ----------
st.set_page_config(page_title="Veritas AI", layout="wide")
def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()
st.title("🔍 Veritas AI")


# ---------- INIT ----------
if "client" not in st.session_state:
    st.session_state.client = get_client()

defaults = {
    "mode": "balanced",
    "model": MODEL_OPTIONS[0],
    "messages": [],
    "rag": None
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


if "chat" not in st.session_state:
    st.session_state.chat = create_chat(
        st.session_state.client,
        st.session_state.model,
        st.session_state.mode
    )


# ---------- LAYOUT ----------
col_main, col_right = st.columns([4, 1.2])


# ---------- UI ----------

render_sidebar()

with col_right:
    render_tools()

with col_main:
    render_chat()