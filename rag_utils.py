import numpy as np
import faiss
import streamlit as st

def chunk_text(text, chunk_size=800, overlap=150):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def embed(text_list):
    response = st.session_state.client.models.embed_content(
        model="models/embedding-001",
        contents=text_list
    )
    return [e.values for e in response.embeddings]


def build_index(embeddings):
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype("float32"))
    return index


def search_index(index, query_vector, k=3):
    query_vector = np.array([query_vector]).astype("float32")
    D, I = index.search(query_vector, k)
    return I[0]