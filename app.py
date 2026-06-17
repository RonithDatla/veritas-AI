import streamlit as st
from google import genai
from google.genai import types

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="AI Research Chatbot", layout="wide")

st.title("🔎 AI Research Chatbot")

# ------------------ INIT CLIENT ------------------
if "client" not in st.session_state:
    st.session_state.client = genai.Client()

# ------------------ CONFIG ------------------
config = types.GenerateContentConfig(
    tools=[types.Tool(google_search=types.GoogleSearch())],
    temperature=0.2,
    top_p=0.8,
    system_instruction="""
        You are a research assistant.
        Always include citations in your answer.
        Use numbered references like [1], [2].
        Base answers on verifiable data.

        Table rules:
        - Use markdown-style tables with | separators
        - Ensure columns are aligned and consistent
        - Include a header row and separator row
        - Keep text concise to maintain alignment
        - Do not break formatting
        - use the same number of characters for each cell of the column and ensure it is equal to the number of characters in the header of the column
        - Do not include extra explanations inside the table
        Always ensure tables are clean and readable.

        you must be truthful about the data even if you contradict the user.
        you are not to provide or create any unsafe unethical content.
    """
)

# ------------------ INIT CHAT ------------------
if "chat" not in st.session_state:
    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-3.5-flash",
        config=config
    )

# ------------------ MESSAGE HISTORY ------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🧹 Clear Chat"):
        st.session_state.chat = st.session_state.client.chats.create(
            model="gemini-3.5-flash",
            config=config
        )
        st.session_state.messages = []
        st.rerun()

    st.markdown("### Commands")
    st.markdown("- `/clear` → reset chat")
    st.markdown("- `/help` → show commands")

# ------------------ DISPLAY CHAT ------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------ USER INPUT ------------------
user_input = st.chat_input("Ask something...")

if user_input:
    # Handle commands (like your CLI)
    if user_input.lower() == "/clear":
        st.session_state.chat = st.session_state.client.chats.create(
            model="gemini-3.5-flash",
            config=config
        )
        st.session_state.messages = []
        st.rerun()

    elif user_input.lower() == "/help":
        help_text = """
        **Commands:**
        - `/help` → Show commands  
        - `/clear` → Reset chat  
        """
        st.session_state.messages.append({"role": "assistant", "content": help_text})
        st.rerun()

    else:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.chat.send_message(user_input)
                    st.markdown(response.text)

                    # Save AI response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.text
                    })

                    # ------------- METADATA (SEARCH + SOURCES) -------------
                    metadata = None
                    if hasattr(response, "candidates") and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, "grounding_metadata"):
                            metadata = candidate.grounding_metadata

                    if metadata:

                        # Show search queries
                        if metadata.web_search_queries:
                            st.markdown("### 🔍 Search Queries")
                            for q in metadata.web_search_queries:
                                st.markdown(f"- {q}")

                        # Show sources
                        if metadata.grounding_chunks:
                            st.markdown("### 🔗 Sources")
                            seen = set()

                            for chunk in metadata.grounding_chunks:
                                if hasattr(chunk, "web") and hasattr(chunk.web, "uri"):
                                    url = chunk.web.uri
                                    title = getattr(chunk.web, "title", url)

                                    if url not in seen:
                                        st.markdown(f"- [{title}]({url})")
                                        seen.add(url)

                except Exception as e:
                    st.error(f"Error: {e}")