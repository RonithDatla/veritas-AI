# Veritas AI

Veritas AI is a Streamlit-based AI assistant using Google Gemini models.  
It includes a chatbot and several tools for working with text, files, and videos.

---

## Features

- Chat assistant with memory
- Report generator from files or prompts
- Academic document polishing
- YouTube video summarizer(currently out of service)

---

## Requirements

Install dependencies:

pip install -r requirements.txt

---

## API Key

Set your API key before running:

Windows:
set GEMINI_API_KEY=your_api_key

macOS/Linux:
export GEMINI_API_KEY=your_api_key

---

## Run the App

streamlit run app.py

---

## Project Structure

app.py
genai_utils.py
yt_utils.py
pdf_utils.py
file_utils.py
formatting.py
config.py
requirements.txt

---

## Notes
- Chat uses persistent memory
- Tools use fresh AI calls (no shared context)
- Supports PDF, DOCX, TXT, and image inputs

- Chat uses persistent memory
- Tools use fresh AI calls (no shared context)
- Supports PDF, DOCX, TXT, and image inputs
