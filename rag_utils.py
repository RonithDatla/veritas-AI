import numpy as np
import faiss
import streamlit as st

import re

def chunk_text(text, chunk_size=500, overlap=50):
    # --- Step 1: split into paragraphs ---
    paragraphs = text.split("\n\n")

    final_chunks = []

    for para in paragraphs:

        words = para.split()

        if len(words) <= chunk_size:
            final_chunks.append(para.strip())
            continue

        sentences = re.split(r'(?<=[.!?]) +', para)

        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sent_words = sentence.split()

            if current_length + len(sent_words) <= chunk_size:
                current_chunk.append(sentence)
                current_length += len(sent_words)

            else:

                if current_chunk:
                    final_chunks.append(" ".join(current_chunk))

                
                current_chunk = [sentence]
                current_length = len(sent_words)

        
        if current_chunk:
            final_chunks.append(" ".join(current_chunk))

    # --- Step 3: add overlap ---
    if overlap > 0:
        overlapped_chunks = []

        for i, chunk in enumerate(final_chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
                continue

            prev_words = final_chunks[i - 1].split()
            overlap_text = " ".join(prev_words[max(0, len(prev_words) - overlap):])

            new_chunk = overlap_text + " " + chunk
            overlapped_chunks.append(new_chunk)

        return overlapped_chunks
    final_chunks = [c for c in final_chunks if c.strip()]
    return final_chunks

def embed(text_list):
    response = st.session_state.client.models.embed_content(
        model="models/embedding-001",
        contents=text_list
    )

    vectors = [e.values for e in response.embeddings]

    vectors = [v / np.linalg.norm(v) for v in vectors]

    return vectors


def build_index(embeddings):
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))
    return index


def search_index(index, query_vector, k=5):
    query_vector = np.array([query_vector]).astype("float32")
    D, I = index.search(query_vector, k)
    return I[0]