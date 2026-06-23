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

# ------------------ RAG UTILITIES ------------------

def chunk_text(text, chunk_size=800, overlap=150):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


#   Batched Gemini Embeddings
def embed(text_list):
    response = st.session_state.client.models.embed_content(
        model="models/embedding-001",
        contents=text_list
    )
    return [e.values for e in response.embeddings]


def build_index(embeddings):
    import faiss
    import numpy as np

    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))

    return index


def search_index(index, query_vector, k=3):
    import numpy as np

    query_vector = np.array([query_vector]).astype("float32")
    D, I = index.search(query_vector, k)
    return I[0]

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

if "client" not in st.session_state:
    st.session_state.client = genai.Client()

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
        report_file = st.file_uploader("Upload file", key="report_upload")

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

        polish_file = st.file_uploader("Upload document", key="polish_upload")

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

#   Scroll-to-bottom button
st.markdown("""
<style>
#scroll-btn {
    position: fixed;
    bottom: 90px;
    right: 20px;
    z-index: 1000;
    background-color: #262730;
    color: white;
    border: none;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 18px;
    text-decoration: none;
}
</style>

<a href="#bottom" id="scroll-btn">⬇</a>
""", unsafe_allow_html=True)


with col_main:

    #   Show chat history first
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    #   Bottom container (file + preview near prompt)
    bottom_container = st.container()

    with bottom_container:

        uploaded_file = st.file_uploader(
            "📎 Attach",
            type=["pdf", "txt", "docx", "png", "jpg", "jpeg"],
            key="chat_file"
        )

        MAX_DIRECT_CHARS = 12000
        chat_image, chat_text = None, None

        if uploaded_file:
            file_id = uploaded_file.name

            #   Reset RAG if new file
            if st.session_state.get("current_file") != file_id:
                st.session_state.current_file = file_id
                st.session_state.rag_ready = False

            chat_image, chat_text = extract_file_text(uploaded_file)

            st.caption(f"📄 {uploaded_file.name}")

            if chat_image:
                st.image(chat_image, use_column_width=True)

            #   Build RAG once for large files
            if chat_text and len(chat_text) >= MAX_DIRECT_CHARS:
                if not st.session_state.get("rag_ready", False):

                    chunks = chunk_text(chat_text)
                    embeddings = embed(chunks)
                    index = build_index(embeddings)

                    st.session_state.index = index
                    st.session_state.chunks = chunks
                    st.session_state.rag_ready = True

    #   Chat input pinned at bottom
    st.markdown('<div id="bottom"></div>', unsafe_allow_html=True)

    user_input = st.chat_input("Ask something...")

    if user_input:

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        #   CASE 1: No file
        if not uploaded_file:
            response = st.session_state.chat_main.send_message(user_input)

        #   CASE 2: Small document
        elif chat_text and len(chat_text) < MAX_DIRECT_CHARS:

            prompt = f"""
                Answer based on this document:

                {chat_text[:12000]}

                Question:
                {user_input}
                """

            response = st.session_state.chat_main.send_message(prompt)

        #   CASE 3: Large document (RAG)
        elif "rag_ready" in st.session_state:

            query_vector = embed([user_input])[0]

            top_indices = search_index(
                st.session_state.index,
                query_vector,
                k=3
            )

            retrieved_chunks = [
                st.session_state.chunks[i] for i in top_indices
            ]

            context = "\n\n".join(retrieved_chunks)

            prompt = f"""
                Use the context below to answer the question. If incomplete, reason carefully.

                Context:
                {context}

                Question:
                {user_input}
                """

            response = st.session_state.chat_main.send_message(prompt)

        else:
            response = st.session_state.chat_main.send_message(user_input)

        clean_text = clean_output(extract_text(response))

        st.session_state.messages.append({
            "role": "assistant",
            "content": clean_text
        })

        st.rerun()