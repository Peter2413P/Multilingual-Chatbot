import os
from typing import List, Tuple
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import fitz  # PyMuPDF

def render_pdf_page_to_image(page: fitz.Page, dpi: int = 300) -> Image.Image:
    """
    Renders a PyMuPDF page to a high-resolution PIL Image.
    """
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

def preprocess_tamil_ocr_image(image: Image.Image) -> Image.Image:
    """
    Independent image preprocessing pipeline optimized for Tamil OCR.
    Enhances contrast, normalizes sharpness, and converts to high-contrast grayscale.
    """
    # 1. Convert to grayscale
    gray = image.convert("L")
    
    # 2. Auto-contrast enhancement
    contrast_img = ImageOps.autocontrast(gray, cutoff=1)
    
    # 3. Increase contrast slightly for crisp character borders
    enhancer = ImageEnhance.Contrast(contrast_img)
    contrast_img = enhancer.enhance(1.4)
    
    # 4. Light sharpening
    sharp_img = contrast_img.filter(ImageFilter.SHARPEN)
    
    # Return 3-channel RGB as expected by most OCR engines
    return sharp_img.convert("RGB")

def render_pdf_to_preprocessed_images(pdf_path: str, dpi: int = 300) -> List[Tuple[int, Image.Image]]:
    """
    Extracts each page of a PDF as a preprocessed image for OCR.
    Returns a list of tuples: (page_number_1_indexed, preprocessed_pil_image)
    """
    doc = fitz.open(pdf_path)
    results = []
    
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            raw_img = render_pdf_page_to_image(page, dpi=dpi)
            preprocessed_img = preprocess_tamil_ocr_image(raw_img)
            results.append((page_idx + 1, preprocessed_img))
    finally:
        doc.close()
        
    return results
