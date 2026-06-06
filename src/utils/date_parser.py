import re
from datetime import datetime, date

def parse_publish_date(date_str):
    """
    Parses a publish date string into a datetime.date object (or string 'YYYY-MM-DD').
    Supports:
    - dd/mm/yyyy
    - yyyy-mm-dd
    - yyyy/mm/dd
    - dd-mm-yyyy
    - Q1/2024, Q2-2024, Q3 2024 (end of quarter)
    - 2024 (end of year)
    Returns:
        datetime.date or None
    """
    if not date_str:
        return None
        
    date_str = str(date_str).strip()
    if not date_str:
        return None

    # 1. Clean and normalize
    # Check for Quarter formats like Q1/2024, Q2-2024, Q3 2024, Quý 3/2024
    quarter_match = re.search(r'(?:[qQ]|Quý\s*)([1-4])[\s\-/]+([0-9]{4})', date_str)
    if quarter_match:
        q_num = int(quarter_match.group(1))
        year = int(quarter_match.group(2))
        # Quarter mappings: Q1 -> Mar 31, Q2 -> Jun 30, Q3 -> Sep 30, Q4 -> Dec 31
        q_mappings = {
            1: (3, 31),
            2: (6, 30),
            3: (9, 30),
            4: (12, 31)
        }
        month, day = q_mappings[q_num]
        try:
            return date(year, month, day)
        except ValueError:
            return None

    # 2. Check for 4-digit Year only (e.g. 2024)
    year_match = re.match(r'^([0-9]{4})$', date_str)
    if year_match:
        year = int(year_match.group(1))
        try:
            return date(year, 12, 31) # End of year convention
        except ValueError:
            return None

    # 3. Standard date formats
    date_formats = [
        ('%d/%m/%Y', True),   # dd/mm/yyyy
        ('%d-%m-%Y', True),   # dd-mm-yyyy
        ('%Y-%m-%d', False),  # yyyy-mm-dd
        ('%Y/%m/%d', False),  # yyyy/mm/dd
    ]

    for fmt, _ in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.date()
        except ValueError:
            continue

    # Fallback attempt to parse with simple split if standard patterns didn't match perfectly
    # Try splitting by /, -, or .
    parts = re.split(r'[\s\-/.]+', date_str)
    if len(parts) == 3:
        try:
            # check if first part is year or day
            if len(parts[0]) == 4: # yyyy-mm-dd
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            elif len(parts[2]) == 4: # dd-mm-yyyy
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                return None
            return date(year, month, day)
        except (ValueError, IndexError):
            pass

    return None

def format_date_display(date_val):
    """
    Formats a date object or string into dd/mm/yyyy format for presentation.
    """
    if not date_val:
        return "N/A"
        
    if isinstance(date_val, (date, datetime)):
        return date_val.strftime('%d/%m/%Y')
        
    if isinstance(date_val, str):
        # Try parsing it first
        parsed = parse_publish_date(date_val)
        if parsed:
            return parsed.strftime('%d/%m/%Y')
        return date_val
        
    return str(date_val)
