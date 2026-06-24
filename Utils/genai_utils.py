def extract_text(response):
    """
    Extracts text safely from Gemini response.
    Handles multiple response formats.
    """

    # ✅ Direct text (fast path)
    if hasattr(response, "text") and response.text:
        return response.text

    # ✅ Candidates-based structure
    try:
        candidates = getattr(response, "candidates", [])
        if not candidates:
            return "⚠️ No response text found"

        parts = candidates[0].content.parts

        texts = []
        for part in parts:
            if hasattr(part, "text") and part.text:
                texts.append(part.text)

        if texts:
            return "\n".join(texts)

    except Exception:
        pass

    return "⚠️ No response text found"


def run_llm(chat, content, clean_output, extract_text):
    """
    Simple wrapper for sending message and returning clean text.
    (kept compatible with rest of your system)
    """
    response = chat.send_message(content)

    return clean_output(
        extract_text(response)
    )
def extract_grounding_sources(response):
    sources = []
    queries = []

    try:
        metadata = response.candidates[0].grounding_metadata

        if not metadata:
            return [], []

        # ✅ queries
        if metadata.web_search_queries:
            queries = list(metadata.web_search_queries)

        # ✅ sources (IMPORTANT FIX)
        if metadata.grounding_chunks:
            for chunk in metadata.grounding_chunks:
                web = getattr(chunk, "web", None)

                if web and web.uri:
                    sources.append({
                        "title": web.title or web.uri,  # ✅ FIX
                        "url": web.uri
                    })

    except Exception as e:
        print("Extraction error:", e)

    # ✅ Deduplicate
    seen = set()
    unique = []

    for s in sources:
        if s["url"] not in seen:
            unique.append(s)
            seen.add(s["url"])

    return unique, queries