# Invoice Masker Tool

## Install
pip install -r requirements.txt
python -m spacy download en_core_web_sm

Install Tesseract OCR:
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Mac: brew install tesseract
- Linux: sudo apt install tesseract-ocr

## Run
python app.py

Go to: http://127.0.0.1:5000
Upload your document, choose "Blur" or "Blackout", and see the masked result instantly.
For multi-page PDFs, all pages are shown with scrolling and can be downloaded as a ZIP.