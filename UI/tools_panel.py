import streamlit as st

from Core.chat_engine import create_chat
from Core.prompts import REPORT_PROMPT, POLISH_PROMPT

from Utils.file_utils import extract_file_text
from Utils.genai_utils import extract_text
from Utils.formatting_utils import clean_output
from Utils.pdf_utils import create_pdf


def render_tools():

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

            chat = create_chat(
                st.session_state.client,
                st.session_state.model,
                st.session_state.mode
            )

            if report_image:
                response = chat.send_message([content, report_image])
            else:
                response = chat.send_message(content)

            st.session_state.report_output = clean_output(
                extract_text(response)
            )

        if st.session_state.get("report_output"):
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

            chat = create_chat(
                st.session_state.client,
                st.session_state.model,
                st.session_state.mode
            )

            response = chat.send_message(
                POLISH_PROMPT + "\n\n" + text[:15000]
            )

            st.session_state.polish_output = clean_output(
                extract_text(response)
            )

        if st.session_state.get("polish_output"):
            st.download_button(
                "⬇️ Download Polished",
                create_pdf(st.session_state.polish_output),
                "polished.pdf"
            )