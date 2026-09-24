import os
import numpy as np
from typing import List, Dict, Any, Optional
from PIL import Image

_ocr_engine = None

def get_tamil_ocr_engine():
    """
    Lazy initialization of PaddleOCR instance with Tamil language configuration.
    """
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR
            # PP-OCRv5 Tamil configuration
            # In PaddleOCR, lang='ta' selects Tamil detection and recognition models
            _ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang='ta',
                show_log=False
            )
        except ImportError:
            raise ImportError(
                "PaddleOCR is not installed. Please install it using: pip install paddlepaddle paddleocr"
            )
    return _ocr_engine

def run_tamil_ocr_on_image(image: Image.Image, page_number: int = 1) -> Dict[str, Any]:
    """
    Runs Tamil OCR on a single PIL Image.
    Preserves text, confidence scores, bounding boxes, and page number.
    
    Returns:
    {
        "page_number": int,
        "full_text": str,
        "confidence_avg": float,
        "lines": [
            {
                "text": str,
                "confidence": float,
                "box": list
            }
        ]
    }
    """
    ocr = get_tamil_ocr_engine()
    
    # Convert PIL Image to RGB NumPy array
    img_array = np.array(image.convert("RGB"))
    
    result = ocr.ocr(img_array, cls=True)
    
    lines = []
    total_conf = 0.0
    valid_count = 0
    
    if result and len(result) > 0 and result[0] is not None:
        for line in result[0]:
            if line and len(line) >= 2:
                box = line[0]
                text_info = line[1]
                if isinstance(text_info, (tuple, list)) and len(text_info) >= 2:
                    text, conf = text_info[0], float(text_info[1])
                    lines.append({
                        "text": text,
                        "confidence": round(conf, 4),
                        "box": box
                    })
                    total_conf += conf
                    valid_count += 1
                    
    full_text = "\n".join([item["text"] for item in lines])
    avg_conf = (total_conf / valid_count) if valid_count > 0 else 0.0
    
    return {
        "page_number": page_number,
        "full_text": full_text,
        "confidence_avg": round(avg_conf, 4),
        "lines": lines
    }
