import streamlit as st
from google import genai
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import os

from config import get_config, MODE_MAP, MODEL_OPTIONS
from file_utils import *
from formatting import clean_output, make_links_clickable

# ------------------ CONSTANTS ------------------
REPORT_PROMPT = """
You are an expert research analyst.

Generate a high-quality structured report using the following format:

1. Title
2. Abstract
3. Key Insights (bullet points)
4. Detailed Analysis (clear sections)
5. Key Takeaways
6. Conclusion

Instructions:
- Use any provided files as primary reference
- Carefully analyze ALL provided content before writing
- Combine user instructions with file content
- Be precise, analytical, and avoid fluff
"""

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

if "report_output" not in st.session_state:
    st.session_state.report_output = None

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
    st.header("Controls")

    if st.button("Clear Chat"):
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

# ------------------ MAIN LAYOUT ------------------
col_main, col_right = st.columns([3, 1])

# ------------------ RIGHT PANEL (REPORT) ------------------
with col_right:
    with st.expander("Generate Report", expanded=False):

        report_instruction = st.text_area(
            "Instructions",
            placeholder="e.g. focus on trends, summarize insights...",
            key="report_text_input"
        )

        report_file = st.file_uploader(
            "Upload file",
            key="report_file_upload"
        )

        report_image = None
        report_text = None

        if report_file:
            file_bytes = report_file.read()
            file_type = report_file.type or ""

            if file_type.startswith("image"):
                report_image = Image.open(BytesIO(file_bytes))
                st.image(report_image, use_column_width=True)
            else:
                if "pdf" in file_type:
                    report_text = read_pdf_cached(file_bytes)
                elif "word" in file_type:
                    report_text = read_docx_cached(file_bytes)
                elif file_type == "text/plain":
                    report_text = read_txt_cached(file_bytes)
                elif "csv" in file_type:
                    report_text = read_csv_cached(file_bytes)
                elif "json" in file_type:
                    report_text = read_json_cached(file_bytes)
                elif "spreadsheet" in file_type:
                    report_text = read_excel_cached(file_bytes)
                elif report_file.name.endswith(".md"):
                    report_text = read_md_cached(file_bytes)
                elif report_file.name.endswith(".html"):
                    report_text = read_html_cached(file_bytes)

        if st.button("Generate Report", key="generate_report_btn"):

            if not report_file and not report_instruction:
                st.warning("Provide a file or instructions.")
                st.stop()

            with st.spinner("Generating report..."):

                content_input = REPORT_PROMPT + "\n\n"

                if report_instruction:
                    content_input += f"User Instruction:\n{report_instruction}\n\n"

                if report_text:
                    content_input += f"Content:\n{report_text[:15000]}"

                if report_image:
                    response = st.session_state.chat.send_message(
                        [content_input, report_image]
                    )
                else:
                    response = st.session_state.chat.send_message(content_input)

                if hasattr(response, "text") and response.text:
                    output_text = response.text
                else:
                    try:
                        output_text = response.candidates[0].content.parts[0].text
                    except:
                        output_text = "Report generation failed."

                clean_text = clean_output(output_text)
                formatted_text = make_links_clickable(clean_text)

                st.session_state.report_output = formatted_text

        if st.session_state.report_output:
            st.markdown("### Preview")

            preview = st.session_state.report_output[:1000]
            st.markdown(preview + "...")

            st.info("Download full report below")

            pdf = create_pdf(st.session_state.report_output)

            st.download_button(
                "Download",
                pdf,
                "report.pdf",
                "application/pdf",
                key="download_report_btn"
            )

# ------------------ LEFT PANEL (CHAT) ------------------
with col_main:

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask something...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                response = st.session_state.chat.send_message(user_input)

                if hasattr(response, "text") and response.text:
                    output_text = response.text
                else:
                    try:
                        output_text = response.candidates[0].content.parts[0].text
                    except:
                        output_text = "No response from model."

                clean_text = clean_output(output_text)
                formatted_text = make_links_clickable(clean_text)

                st.markdown(formatted_text)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": formatted_text
                })