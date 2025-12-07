# invoice_qc/utils.py
import re
from datetime import datetime
from typing import Optional

def parse_float_universal(s: str) -> float:
    """ Universally parses strings into floats. """
    if not s: return 0.0
    s = str(s).strip()
    s = re.sub(r'[^\d,.\-]', '', s)
    if not s: return 0.0
    
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'): clean = s.replace('.', '').replace(',', '.')
        else: clean = s.replace(',', '')
    elif ',' in s: clean = s.replace(',', '.')
    else: clean = s
        
    try:
        return float(clean)
    except:
        return 0.0

def parse_date_universal(date_str: str) -> Optional[str]:
    """ Parses common date formats (DD.MM.YYYY, DD/MM/YYYY) into ISO YYYY-MM-DD. """
    if not date_str: return None
    
    # Clean separators
    cleaned_date = date_str.replace('/', '.').replace('-', '.')
    
    # Try common formatsimport re
from datetime import datetime
from typing import Optional

def parse_float_universal(s: str) -> float:
    """ Universally parses strings into floats. """
    if not s: return 0.0
    s = str(s).strip()
    s = re.sub(r'[^\d,.\-]', '', s)
    if not s: return 0.0
    
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'): clean = s.replace('.', '').replace(',', '.')
        else: clean = s.replace(',', '')
    elif ',' in s: clean = s.replace(',', '.')
    else: clean = s
        
    try:
        return float(clean)
    except:
        return 0.0

def parse_date_universal(date_str: str) -> Optional[str]:
    """ Parses common date formats (DD.MM.YYYY, DD/MM/YYYY) into ISO YYYY-MM-DD. """
    if not date_str: return None
    
    cleaned_date = date_str.replace('/', '.').replace('-', '.')
    
    formats_to_try = [
        "%d.%m.%Y", "%d.%m.%y", 
        "%Y.%m.%d", "%y.%m.%d"
    ]
    
    for fmt in formats_to_try:
        try:
            dt_obj = datetime.strptime(cleaned_date, fmt)
            return dt_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    return None
    for fmt in formats_to_try:
        try:
            dt_obj = datetime.strptime(cleaned_date, fmt)
            return dt_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    return None