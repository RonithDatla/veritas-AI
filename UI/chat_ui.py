import streamlit as st

from Core.chat_engine import send_message
from Core.rag_pipeline import build_rag, query_rag

from Utils.file_utils import extract_file_text
from Utils.genai_utils import extract_text
from Utils.formatting_utils import clean_output


def render_chat():

    # ------------------ FILE UPLOAD ------------------

    uploaded_file = st.file_uploader(
        "📎 Attach document",
        type=["pdf", "txt", "docx", "png", "jpg", "jpeg"],
        key="chat_file"
    )

    chat_image, chat_text = None, None

    if uploaded_file:
        file_id = uploaded_file.name

        # ✅ Reset RAG if new file
        if st.session_state.get("current_file") != file_id:
            st.session_state.current_file = file_id
            st.session_state.rag = None

        chat_image, chat_text = extract_file_text(uploaded_file)

        st.caption(f"📄 {uploaded_file.name}")

        if chat_image:
            st.image(chat_image, use_column_width=True)

        # ✅ Build RAG ONCE
        if chat_text and st.session_state.get("rag") is None:
            with st.spinner("Indexing document..."):
                chunks, index = build_rag(chat_text)
                st.session_state.rag = (chunks, index)

    # ------------------ CHAT HISTORY ------------------

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ------------------ INPUT ------------------

    user_input = st.chat_input("Ask something...")

    if user_input:

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.spinner("Thinking..."):

            # ✅ CASE 1: RAG
            if st.session_state.get("rag"):

                chunks, index = st.session_state.rag

                context, sources = query_rag(
                    index,
                    chunks,
                    user_input
                )

                prompt = f"""
You are a precise AI assistant.

Use ONLY the context below.
If the answer is not found, say "Not found in document".

Context:
{context}

Question:
{user_input}
"""

                response = send_message(
                    st.session_state.chat,
                    prompt
                )

                clean_text = clean_output(
                    extract_text(response)
                )

                sources_text = "\n".join(
                    f"- Chunk {idx}: {chunk[:120].rsplit(' ', 1)[0]}..."
                    for idx, chunk in sources
                )

                final_output = f"{clean_text}\n\n**Sources:**\n{sources_text}"

                # Preview
                with st.expander("🔍 Source Preview"):
                    for idx, chunk in sources:
                        st.markdown(f"**Chunk {idx}**")
                        st.write(chunk[:250])

            # ✅ CASE 2: Normal chat
            else:
                response = send_message(
                    st.session_state.chat,
                    user_input
                )

                final_output = clean_output(
                    extract_text(response)
                )

        st.session_state.messages.append({
            "role": "assistant",
            "content": final_output
        })

        st.rerun()