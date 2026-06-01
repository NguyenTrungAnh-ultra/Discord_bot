import sys
import os

sys.path.append(os.getcwd())
from src.modules.deep_research.db.date_utils import parse_publish_date, format_date_display

test_cases = [
    ("01/12/2024", "01/12/2024"),
    ("2024-05-15", "15/05/2024"),
    ("Q3/2024", "30/09/2024"),
    ("Q1-2025", "31/03/2025"),
    ("Quý 2/2024", "30/06/2024"),
    ("2023", "31/12/2023"),
    ("invalid", "N/A"),
    (None, "N/A")
]

print("Running tests on date_utils.py:")
all_passed = True
for val, expected in test_cases:
    parsed = parse_publish_date(val)
    formatted = format_date_display(parsed)
    if formatted != expected:
        print(f"FAILED: Input: {val} -> Parsed: {parsed} -> Formatted: {formatted} (Expected: {expected})")
        all_passed = False
    else:
        print(f"PASSED: Input: {val} -> Parsed: {parsed} -> Formatted: {formatted}")

if all_passed:
    print("All date_utils tests passed successfully!")
