import streamlit as st

from Core.chat_engine import send_message, send_rag_message, extract_used_citations
from Core.rag_pipeline import build_rag, query_rag

from Utils.file_utils import extract_file_text
from Utils.genai_utils import extract_text, extract_grounding_sources
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

            # ✅ CASE 1: RAG (document citations)
            if st.session_state.get("rag"):

                chunks, index = st.session_state.rag

                context, retrieved_chunks = query_rag(
                    index,
                    chunks,
                    user_input
                )

                response = send_rag_message(
                    st.session_state.chat,
                    retrieved_chunks,
                    user_input
                )

                clean_text = clean_output(
                    extract_text(response)
                )

                final_output = clean_text

                # ✅ Highlight used citations
                used_citations = extract_used_citations(clean_text)

                with st.expander("📚 Document Sources"):
                    for i, chunk in enumerate(retrieved_chunks, start=1):
                        if i in used_citations:
                            st.markdown(f"**[{i}] ✅ Used in answer**")
                        else:
                            st.markdown(f"[{i}]")

                        st.write(chunk["text"][:250])

            # ✅ CASE 2: Normal chat (Google citations)
            else:
                response, web_sources = send_message(
                    st.session_state.chat,
                    user_input
                )

                final_output = clean_output(
                    extract_text(response)
                )

                if web_sources:
                    with st.expander("🌐 Sources (Google Search)"):
                        for i, src in enumerate(web_sources, 1):

                            # ✅ Handle multiple possible formats safely
                            if isinstance(src, dict):
                                title = src.get("title", "Unknown Source")
                                url = src.get("url", "")
                            elif isinstance(src, (list, tuple)) and len(src) == 2:
                                title, url = src
                            else:
                                title = str(src)
                                url = str(src)

                            st.markdown(f"**[{i}] {title}**")
                            st.markdown(url)
        st.session_state.messages.append({
            "role": "assistant",
            "content": final_output
        })

        st.rerun()