from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import os
import tempfile


def extract_text_from_pdf(pdf_file):
    """
    Extract text from scanned/image-based PDF using Tesseract OCR.
    Best quality when running locally with Tesseract installed.
    """

    text = ""

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            tmp_path = tmp.name

        # Convert PDF pages to images
        images = convert_from_path(tmp_path, dpi=300)

        # OCR each page
        for img in images:
            page_text = pytesseract.image_to_string(img, lang="eng")
            text += page_text + "\n"

        # Cleanup temp file
        os.remove(tmp_path)

    except Exception as e:
        print("OCR ERROR:", e)
        return ""

    return text.strip()
