import fitz  # PyMuPDF
import easyocr
import numpy as np
from PIL import Image
import io

# Initialize OCR reader once (fast reuse)
reader = easyocr.Reader(['en'], gpu=False)


def extract_text_from_pdf(file):
    text = ""

    # ---------- Convert PDF pages to images ----------
    try:
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")

        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            img_np = np.array(img)

            # OCR
            result = reader.readtext(img_np, detail=0, paragraph=True)
            text += " ".join(result) + "\n"

    except Exception as e:
        print("OCR FAILED:", e)

    return text.strip()
