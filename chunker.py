def chunk_text(text, chunk_size=6000, overlap=500):
    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap

    return chunks
