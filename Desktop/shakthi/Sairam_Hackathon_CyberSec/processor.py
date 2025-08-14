import pytesseract
from pytesseract import Output
import cv2
import re
import os
from werkzeug.utils import secure_filename

# 🔹 Set Tesseract path for Windows (adjust if installed elsewhere)
# On Linux/Mac, you can remove this line
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Regex patterns for sensitive data
patterns = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),  # Email
    re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),  # Phone
    re.compile(r"\b\d{5}(?:-\d{4})?\b"),  # ZIP
    re.compile(r"\b\d{6,}\b"),  # Long numeric sequences
]

# Common sensitive keywords
keywords = ["name", "dob", "birth", "address", "city", "state", "country", "passport", "license", "id"]

def is_sensitive(word):
    """Check if a word matches sensitive patterns or contains sensitive keywords."""
    for p in patterns:
        if p.search(word):
            return True
    if any(kw.lower() in word.lower() for kw in keywords):
        return True
    return False

def blur_area(img, x, y, w, h):
    roi = img[y:y+h, x:x+w]
    if roi.size > 0:
        blur = cv2.GaussianBlur(roi, (51, 51), 0)
        img[y:y+h, x:x+w] = blur
    return img

def blackout_area(img, x, y, w, h):
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), -1)
    return img

def process_image(img_path, output_path, mask_type):
    """Mask sensitive data in an image."""
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Could not load image: {img_path}")
    
    try:
        data = pytesseract.image_to_data(img, output_type=Output.DICT)
    except Exception as e:
        raise RuntimeError(f"OCR failed: {e}")
    
    for i, word in enumerate(data["text"]):
        if not word.strip():
            continue
        if is_sensitive(word):
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            if mask_type == "black":
                img = blackout_area(img, x, y, w, h)
            else:
                img = blur_area(img, x, y, w, h)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not cv2.imwrite(output_path, img):
        raise RuntimeError(f"Could not save output image: {output_path}")

def process_pdf(pdf_path, output_dir, mask_type):
    """Process each page of a PDF (requires poppler installed)."""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise RuntimeError("pdf2image is not installed.")
    
    pages = convert_from_path(pdf_path, 300)
    os.makedirs(output_dir, exist_ok=True)
    output_files = []
    
    for idx, page in enumerate(pages):
        img_path = os.path.join(output_dir, f"page_{idx+1}.jpg")
        masked_path = os.path.join(output_dir, f"masked_page_{idx+1}.jpg")
        page.save(img_path, "JPEG")
        process_image(img_path, masked_path, mask_type)
        output_files.append(masked_path)
    
    return output_files

def process_file(filepath, mask_type):
    """Main entry for masking files."""
    ext = os.path.splitext(filepath)[1].lower()
    output_dir = os.path.join("static", "output")
    os.makedirs(output_dir, exist_ok=True)

    safe_filename = secure_filename(os.path.basename(filepath))
    if ext == ".pdf":
        return process_pdf(filepath, output_dir, mask_type)
    elif ext in [".jpg", ".jpeg", ".png", ".tiff"]:
        output_path = os.path.join(output_dir, f"masked_{safe_filename}")
        process_image(filepath, output_path, mask_type)
        return output_path
    else:
        raise ValueError(f"Unsupported file type: {ext}")
