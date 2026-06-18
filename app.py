import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

def create_pdf(text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter
    y = height - 40

    lines = text.split("\n")

    for line in lines:
        if y < 40:
            c.showPage()
            y = height - 40

        c.drawString(40, y, line[:90])
        y -= 15

    c.save()
    buffer.seek(0)
    return buffer


st.set_page_config(page_title="🔍Veritas AI", layout="wide")
st.title("🔍Veritas AI")

MODES = {
    "precise": 0.1,
    "balanced": 0.2,
    "creative": 0.6
}

MODE_OPTIONS = ["Precise", "Balanced", "Creative"]
MODEL_OPTIONS = ["gemini-2.5-flash", "gemini-3.5-flash"]

if "mode" not in st.session_state:
    st.session_state.mode = "Balanced"

if "model" not in st.session_state:
    st.session_state.model = "gemini-3.5-flash"

if "client" not in st.session_state:
    st.session_state.client = genai.Client()

config = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=MODES[st.session_state.mode.lower()],
    top_p=0.8,
    system_instruction="""
        You are a research assistant.
        Always include citations in your answer.
        Use numbered references like [1], [2].
        Base answers on verifiable data.

        you must be truthful about the data even if you contradict the user.
        you are not to provide or create any unsafe unethical content.
    """
)

if "chat" not in st.session_state:
    st.session_state.chat = st.session_state.client.chats.create(
        model=st.session_state.model,
        config=config
    )

if "messages" not in st.session_state:
    st.session_state.messages = []


with st.sidebar:
    st.header("Controls")

    if st.button("Clear Chat"):
        st.session_state.chat = st.session_state.client.chats.create(
            model=st.session_state.model,
            config=config
        )
        st.session_state.messages = []
        st.rerun()

    # Commands dropdown
    with st.expander("Commands"):
        st.markdown("- `/help` → show commands")
        st.markdown("- `/clear` → reset chat")
        st.markdown("- `/mode precise|balanced|creative`")

    # Mode dropdown
    selected_mode = st.selectbox("Mode", MODE_OPTIONS, index=MODE_OPTIONS.index(st.session_state.mode))

    if selected_mode != st.session_state.mode:
        st.session_state.mode = selected_mode
        st.session_state.chat = st.session_state.client.chats.create(
            model=st.session_state.model,
            config=config
        )
        st.session_state.messages = []
        st.rerun()

    # Model dropdown
    selected_model = st.selectbox("Model", MODEL_OPTIONS, index=MODEL_OPTIONS.index(st.session_state.model))

    if selected_model != st.session_state.model:
        st.session_state.model = selected_model
        st.session_state.chat = st.session_state.client.chats.create(
            model=st.session_state.model,
            config=config
        )
        st.session_state.messages = []
        st.rerun()

    st.markdown("### Upload Image")

    uploaded_file = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg"]
    )


if uploaded_file:
    image = Image.open(uploaded_file)

    st.image(image, caption="Uploaded Image", use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        generate_chat = st.button("Generate Report")

    with col2:
        download_pdf = st.button("Download PDF Report")

    if generate_chat:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing image..."):
                try:
                    response = st.session_state.chat.send_message([
                        """Write a detailed 2-page research-style report about this image.
                        Include:
                        1. Identification of subject
                        2. Historical background
                        3. Key observations
                        4. Cultural or scientific significance
                        5. Conclusion
                        Use citations where possible.""",
                        image
                    ])

                    st.markdown(response.text)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.text
                    })

                except Exception as e:
                    st.error(f"Error: {e}")

    if download_pdf:
        with st.spinner("Generating PDF..."):
            try:
                response = st.session_state.chat.send_message([
                    """Write a detailed 2-page research-style report about this image.
                    Include:
                    1. Identification of subject
                    2. Historical background
                    3. Key observations
                    4. Cultural or scientific significance
                    5. Conclusion
                    Use citations where possible.""",
                    image
                ])

                pdf_file = create_pdf(response.text)

                st.download_button(
                    label="Download PDF",
                    data=pdf_file,
                    file_name="image_report.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Error: {e}")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


user_input = st.chat_input("Ask something...")

if user_input:
    if user_input.lower() == "/clear":
        st.session_state.chat = st.session_state.client.chats.create(
            model=st.session_state.model,
            config=config
        )
        st.session_state.messages = []
        st.rerun()

    elif user_input.lower() == "/help":
        help_text = """
        **Commands:**
        - `/help` → Show commands  
        - `/clear` → Reset chat  
        - `/mode precise|balanced|creative` → Change AI mode
        """
        st.session_state.messages.append({"role": "assistant", "content": help_text})
        st.rerun()

    else:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.chat.send_message(user_input)

                    st.markdown(response.text)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.text
                    })

                except Exception as e:
                    st.error(f"Error: {e}")