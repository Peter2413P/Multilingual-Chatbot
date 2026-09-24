import os
from typing import List, Dict, Any
import fitz  # PyMuPDF
import docx

from app.tamil.tamil_preprocessor import render_pdf_to_preprocessed_images
from app.tamil.tamil_ocr import run_tamil_ocr_on_image
from app.tamil.tamil_cleaner import clean_tamil_text

def has_extractable_text(doc: fitz.Document, min_char_threshold: int = 50) -> bool:
    """
    Checks if a PDF has digital extractable text (e.g. at least min_char_threshold characters).
    """
    total_chars = 0
    for page in doc:
        text = page.get_text()
        if text:
            total_chars += len(text.strip())
            if total_chars >= min_char_threshold:
                return True
    return False

def extract_tamil_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts Tamil text from PDF:
    - If digital text is present -> extracts text per page directly (input_type="text")
    - If scanned / no text -> runs Tamil OCR pipeline (input_type="ocr")
    """
    doc = fitz.open(pdf_path)
    page_results = []
    
    try:
        is_digital = has_extractable_text(doc)
        
        if is_digital:
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                raw_text = page.get_text()
                cleaned = clean_tamil_text(raw_text)
                page_results.append({
                    "page_number": page_idx + 1,
                    "text": cleaned,
                    "input_type": "text",
                    "confidence_avg": 1.0,
                    "raw_text": raw_text
                })
        else:
            # Scanned PDF: Render pages and run Tamil PaddleOCR
            preprocessed_pages = render_pdf_to_preprocessed_images(pdf_path, dpi=300)
            for page_num, img in preprocessed_pages:
                ocr_out = run_tamil_ocr_on_image(img, page_number=page_num)
                cleaned = clean_tamil_text(ocr_out["full_text"])
                page_results.append({
                    "page_number": page_num,
                    "text": cleaned,
                    "input_type": "ocr",
                    "confidence_avg": ocr_out.get("confidence_avg", 0.0),
                    "ocr_lines": ocr_out.get("lines", []),
                    "raw_text": ocr_out["full_text"]
                })
    finally:
        doc.close()
        
    return page_results

def extract_tamil_from_docx(docx_path: str) -> List[Dict[str, Any]]:
    doc = docx.Document(docx_path)
    full_text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    cleaned = clean_tamil_text(full_text)
    return [{
        "page_number": 1,
        "text": cleaned,
        "input_type": "text",
        "confidence_avg": 1.0,
        "raw_text": full_text
    }]

def extract_tamil_from_txt(txt_path: str) -> List[Dict[str, Any]]:
    # Try utf-8 first
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except UnicodeDecodeError:
        with open(txt_path, "r", encoding="utf-8-sig", errors="ignore") as f:
            raw_text = f.read()
            
    cleaned = clean_tamil_text(raw_text)
    return [{
        "page_number": 1,
        "text": cleaned,
        "input_type": "text",
        "confidence_avg": 1.0,
        "raw_text": raw_text
    }]

def extract_tamil_document(file_path: str) -> List[Dict[str, Any]]:
    """
    Dispatcher for Tamil document extraction based on file extension.
    """
    ext = file_path.split('.')[-1].lower()
    
    if ext == 'pdf':
        return extract_tamil_from_pdf(file_path)
    elif ext == 'docx':
        return extract_tamil_from_docx(file_path)
    elif ext in ['txt', 'md']:
        return extract_tamil_from_txt(file_path)
    else:
        # Fallback to general loader if text readable
        return extract_tamil_from_txt(file_path)
