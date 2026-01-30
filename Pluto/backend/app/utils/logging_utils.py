"""
Logging utilities for safe text output on Windows
"""
import re


def safe_text(text: str, max_length: int = 80) -> str:
    """
    Sanitize text for safe logging on Windows (avoiding Unicode errors)
    
    Args:
        text: The text to sanitize
        max_length: Maximum length after sanitization (for truncation)
        
    Returns:
        ASCII-safe text suitable for logging
    """
    if not text:
        return ""
    
    # Convert to ASCII, replacing non-ASCII characters with '?'
    # This prevents UnicodeEncodeError on Windows cp1252 logging
    try:
        # First try to encode as ASCII, replacing errors
        safe = text.encode('ascii', errors='replace').decode('ascii')
        
        # Replace common problematic characters with ASCII equivalents
        replacements = {
            '\u2502': '|',  # Box drawing vertical
            '\u251c': '|-', # Box drawing right
            '\u2514': '`-', # Box drawing up-right
            '\u2500': '-',  # Box drawing horizontal
            '\uf041': '',   # Private use area character (often from PDFs)
            '\u2022': '*',  # Bullet point
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
        }
        
        for char, replacement in replacements.items():
            safe = safe.replace(char, replacement)
        
        # Remove any remaining control characters except newlines/tabs
        safe = re.sub(r'[^\x20-\x7E\n\t]', '', safe)
        
        # Normalize whitespace
        safe = ' '.join(safe.split())
        
        # Truncate if needed
        if len(safe) > max_length:
            safe = safe[:max_length]
        
        return safe
        
    except Exception as e:
        # Fallback: return safe placeholder
        return f"<text encoding error: {str(e)[:30]}>"
