import os
import sys
import io
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

# Configure UTF-8 encoding for Windows consoles
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

from app.tamil.tamil_extractor import extract_tamil_document, has_extractable_text

def test_digital_tamil_pdf():
    print("\n--- Testing Digital Tamil PDF Ingestion ---")
    pdf_path = "temp_test_digital_ta.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    
    font_path = "C:/Windows/Fonts/Nirmala.ttc"
    if os.path.exists(font_path):
        page.insert_font(fontname="tamilfont", fontfile=font_path)
        font_arg = {"fontname": "tamilfont"}
    else:
        font_arg = {}
    
    # Insert extractable text
    text_content = (
        "திருக்குறள் (Thirukkural) தமிழ் மொழியின் தலைசிறந்த நீதி நூல்.\n"
        "அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு.\n"
        "இதனை இயற்றியவர் திருவள்ளுவர் ஆவார்."
    )
    page.insert_text((50, 72), text_content, fontsize=12, **font_arg)
    doc.save(pdf_path)
    doc.close()
    
    # Verify has_extractable_text
    check_doc = fitz.open(pdf_path)
    is_digital = has_extractable_text(check_doc, min_char_threshold=20)
    check_doc.close()
    print(f"Has digital extractable text: {is_digital}")
    assert is_digital is True
    
    # Test extraction
    extracted = extract_tamil_document(pdf_path)
    print(f"Extracted pages: {len(extracted)}")
    print(f"Page 1 text snippet: {extracted[0]['text'][:80]}")
    print(f"Input type: {extracted[0]['input_type']}")
    
    assert extracted[0]["input_type"] == "text"
    assert "திருவள்ளுவர்" in extracted[0]["text"]
    
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    print("✓ Digital Tamil PDF extraction test passed.")

def test_scanned_tamil_pdf_detection():
    print("\n--- Testing Scanned Tamil PDF Detection & Routing ---")
    pdf_path = "temp_test_scanned_ta.pdf"
    
    # Create an image-only PDF (no text stream)
    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Scanned Image Document", fill=(0, 0, 0))
    img_temp = "temp_page.png"
    img.save(img_temp)
    
    doc = fitz.open()
    page = doc.new_page(width=600, height=400)
    page.insert_image(fitz.Rect(0, 0, 600, 400), filename=img_temp)
    doc.save(pdf_path)
    doc.close()
    
    # Check digital text
    check_doc = fitz.open(pdf_path)
    is_digital = has_extractable_text(check_doc, min_char_threshold=50)
    check_doc.close()
    print(f"Has extractable text in scanned PDF: {is_digital}")
    assert is_digital is False
    
    # Clean up
    if os.path.exists(img_temp):
        os.remove(img_temp)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        
    print("✓ Scanned Tamil PDF detection test passed.")

if __name__ == "__main__":
    test_digital_tamil_pdf()
    test_scanned_tamil_pdf_detection()
