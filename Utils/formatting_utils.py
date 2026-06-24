import re

def clean_output(text):
    patterns = [
        "Search Queries:",
        "Metadata Search Queries:",
        "Search queries:",
        "Metadata:"
    ]
    for p in patterns:
        if p in text:
            text = text.split(p)[0]
    return text.strip()

def make_links_clickable(text):
    url_pattern = r'(https?://[^\s]+)'
    return re.sub(url_pattern, r'\1', text)