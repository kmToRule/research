import re

def split_sentences(text):
    text = re.sub(r"\s+", " ", text)
    return re.split(r'(?<=[.!?]) +', text)

def find_sentences_with_keywords(text, keywords, limit=5):
    sentences = split_sentences(text)
    results = []

    for s in sentences:
        for kw in keywords:
            if kw.lower() in s.lower():
                results.append(s.strip())
                break
        if len(results) >= limit:
            break

    return results

def clean_sentence(s, max_len=180):
    s = s.strip()

    junk = [
        "thank you", "thanks", "good morning", "good afternoon",
        "operator", "listen-only", "question", "please go ahead",
        "page", "moderator", "sameet", "jairam", "kaynes technology",
        "conference call", "transcript", "participant", "welcome"
    ]

    low = s.lower()
    for j in junk:
        if j in low:
            return None

    # Remove very long noisy OCR sentences
    if len(s.split()) > 35:
        return None

    return s

