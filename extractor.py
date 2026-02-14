from pdf2image import convert_from_bytes
import pytesseract

def extract_text_from_pdf(uploaded_file):
    try:
        images = convert_from_bytes(uploaded_file.read(), dpi=200)

        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)

        return text.strip()

    except Exception as e:
        return ""
