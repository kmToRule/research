import pytesseract
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
from pdf2image import convert_from_bytes
import tempfile
import os


def extract_text_from_pdf(uploaded_file):
    try:
        # Convert PDF → images
        images = convert_from_bytes(uploaded_file.read(), dpi=300)

        if not images:
            print("PDF to image conversion failed")
            return ""

        full_text = ""

        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img, lang="eng")

            if text:
                full_text += text + "\n"

        print("Extracted length:", len(full_text))
        return full_text.strip()

    except Exception as e:
        print("OCR ERROR:", str(e))
        return ""
