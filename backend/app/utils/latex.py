import re

def escape_latex(text: str) -> str:
    """
    Escape special LaTeX characters in a string.
    """
    if not text:
        return ""
    
    # List of characters that need to be escaped by prefixing with a backslash
    chars_to_escape = ['&', '%', '$', '#', '_', '{', '}']
    
    result = text
    for char in chars_to_escape:
        result = result.replace(char, f"\\{char}")
    
    # Handle characters that require more than just a backslash
    # Note: we do these after the simple escapes to avoid double-escaping
    result = result.replace('~', r'\textasciitilde{}')
    result = result.replace('^', r'\textasciicircum{}')
    # result = result.replace('\\', r'\textbackslash{}') # Usually content doesn't have literal backslashes we want to escape unless it's code
    
    return result
