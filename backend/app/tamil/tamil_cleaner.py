import re

def clean_tamil_text(text: str) -> str:
    """
    Cleans Tamil text without over-cleaning or stripping Unicode nuances.
    
    Preserves:
    - Tamil Unicode characters (\u0B80-\u0BFF)
    - Tamil numerals (\u0BE6-\u0BEF)
    - English words and numbers
    - Punctuation (.,!?:;-"'()[]/ மற்றும் பிற)
    - Structural paragraph boundaries (\n\n) and headings
    """
    if not text:
        return ""
    
    # 1. Normalize unicode form (NFC)
    import unicodedata
    text = unicodedata.normalize("NFC", text)
    
    # 2. Remove null bytes and unprintable control chars (preserve standard \n, \r, \t)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\uFFFD]', '', text)
    
    # 3. Normalize carriage returns
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 4. Normalize spaces per line (convert multiple horizontal spaces/tabs to a single space)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned_line = re.sub(r'[ \t\f\v]+', ' ', line).strip()
        cleaned_lines.append(cleaned_line)
        
    text = '\n'.join(cleaned_lines)
    
    # 5. Collapse 3+ consecutive newlines to maximum 2 newlines (preserves paragraph structure)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()
