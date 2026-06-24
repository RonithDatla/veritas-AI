import numpy as np
import faiss
import streamlit as st
import re


# ------------------ CLEAN TEXT ------------------

def clean_pdf_text(text):
    text = text.replace("\u00b7", " ")   # weird dots
    text = text.replace("\uf0b7", "-")   # bullet points
    text = text.replace("\n", " ")

    text = re.sub(r'\s+', ' ', text)  # remove extra spaces

    return text.strip()


# ------------------ BUILD RAG ------------------
@st.cache_data
def build_rag(pages):
    """
    pages = list of page texts
    """

    all_chunks = []
    current_id = 0

    for page_num, page_text in enumerate(pages, start=1):

        page_chunks = chunk_text(page_text)

        for chunk in page_chunks:
            all_chunks.append({
                "id": current_id,
                "text": chunk["text"],
                "page": page_num  # ✅ ADDED HERE
            })
            current_id += 1

    embeddings = embed(all_chunks)
    index = build_index(embeddings)

    return all_chunks, index


# ------------------ SMART CHUNKING ------------------

def chunk_text(text, chunk_size=300, overlap=40):
    """
    ✅ Hybrid chunking:
    - Sentence-aware (keeps meaning)
    - Balanced chunk size (better embeddings)
    - Light overlap (context continuity)
    """

    # ✅ Split into sentences
    sentences = re.split(r'(?<=[.!?]) +', text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sent in sentences:
        words = sent.split()

        # ✅ Skip useless tiny/noisy sentences
        if len(words) < 5:
            continue

        # ✅ Add sentence to current chunk
        current_chunk.append(sent)
        current_length += len(words)

        # ✅ If chunk size reached → save chunk
        if current_length >= chunk_size:
            chunk_text = " ".join(current_chunk).strip()

            # ✅ remove noisy small chunks
            if len(chunk_text.split()) > 30:
                chunks.append(chunk_text)

            # ✅ Overlap: keep last few sentences (NOT words)
            overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
            current_chunk = overlap_sentences
            current_length = sum(len(s.split()) for s in current_chunk)

    # ✅ Add last chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk).strip()
        if len(chunk_text.split()) > 30:
            chunks.append(chunk_text)

    # ✅ Return with metadata (same structure as before)
    return [{"id": i, "text": c} for i, c in enumerate(chunks)]

# ------------------ EMBEDDING ------------------
def embed(text_list):
    if not text_list:
        return []

    if isinstance(text_list[0], dict):
        text_list = [t["text"] for t in text_list]

    response = st.session_state.client.models.embed_content(
        model="gemini-embedding-001",
        contents=text_list
    )

    vectors = [e.values for e in response.embeddings]

    vectors = [v / np.linalg.norm(v) for v in vectors]

    return vectors


# ------------------ INDEX ------------------

def build_index(embeddings):
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))
    return index


# ------------------ SEARCH ------------------

def search_index(index, query_vector, k=7):  # ✅ increased recall
    query_vector = np.array([query_vector]).astype("float32")
    D, I = index.search(query_vector, k)
    return I[0]


# ------------------ QUERY ------------------

def query_rag(index, chunks, user_input):

    # ✅ Query enhancement (VERY IMPORTANT)
    query = f"Find relevant instructions, requirements, or details: {user_input}"

    q_vec = embed([query])[0]

    top_idx = search_index(index, q_vec)

    results = [chunks[i] for i in top_idx]

    # ✅ DEBUG: check retrieval quality
    print("\n--- RETRIEVED CHUNKS ---")
    for i, r in enumerate(results):
        print(f"\nChunk {i+1}:\n{r['text'][:300]}")

    context = "\n\n".join(
    f"(Page {r['page']}) {r['text']}"
    for r in results
    )
    return context, results
