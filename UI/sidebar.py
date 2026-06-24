import streamlit as st
from Core.chat_engine import create_chat
from config import MODEL_OPTIONS, MODE_MAP


def render_sidebar():

    with st.sidebar:
        st.header("⚙️ Controls")

        # Clear chat
        if st.button("🧹 Clear Chat"):
            st.session_state.messages = []
            st.session_state.chat = create_chat(
                st.session_state.client,
                st.session_state.model,
                st.session_state.mode
            )
            st.rerun()

        # Mode selection
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
            st.session_state.chat = create_chat(
                st.session_state.client,
                st.session_state.model,
                st.session_state.mode
            )
            st.rerun()

        # Model selection
        selected_model = st.selectbox(
            "Model",
            MODEL_OPTIONS,
            index=MODEL_OPTIONS.index(st.session_state.model)
        )

        if selected_model != st.session_state.model:
            st.session_state.model = selected_model
            st.session_state.chat = create_chat(
                st.session_state.client,
                st.session_state.model,
                st.session_state.mode
            )
            st.rerun()