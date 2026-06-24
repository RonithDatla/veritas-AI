def extract_text(response):
    if hasattr(response, "text") and response.text:
        return response.text
    try:
        return response.candidates[0].content.parts[0].text
    except:
        return "⚠️ No response text found"


def run_llm(chat, content, clean_output, extract_text):
    response = chat.send_message(content)
    return clean_output(extract_text(response))
