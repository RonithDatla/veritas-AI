from config import get_config
from Utils.genai_utils import extract_grounding_sources


def create_chat(client, model, mode):
    return client.chats.create(
        model=model,
        config=get_config(mode)
    )


# ✅ NORMAL CHAT (Google grounding sources)
def send_message(chat, message):
    response = chat.send_message(message)

    # ✅ Extract real Google sources (may be empty)
    sources = extract_grounding_sources(response)

    return response, sources


# ✅ RAG CHAT (document-based, NO AI citation forcing)
def send_rag_message(chat, retrieved_chunks, user_input):

    # ✅ Simple grounded prompt (no fake [1][2])
    context = "\n\n".join(
        chunk["text"] for chunk in retrieved_chunks
    )

    prompt = f"""
You are a precise AI assistant.

Use ONLY the context below.
If the answer is not found, say "Not found in document".

Context:
{context}

Question:
{user_input}

Also provide the page number of the source for each answer, in the format: (Page X)
"""

    response = chat.send_message(prompt)

    return response


# ✅ OPTIONAL: simple helper (if you still want highlighting later)
def extract_used_citations(text):
    import re
    return list(set(map(int, re.findall(r'\[(\d+)\]', text))))
