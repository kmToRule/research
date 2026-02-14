import pytesseract
from pdf2image import convert_from_bytes
import tempfile
import os

# Set path to tesseract executable (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(file):
    text = ""

    images = convert_from_bytes(file.read())

    for img in images:
        page_text = pytesseract.image_to_string(img)
        if page_text:
            text += page_text + "\n"

    return text.strip()
