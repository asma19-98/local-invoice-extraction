"""Parsing helpers for amounts and dates in EN/FR documents."""
import re
import unicodedata
from datetime import date


def unaccent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


# 1 234,56 | 1,234.56 | 1.234,56 | 45.90 | 45,90  (always exactly two decimals)
AMOUNT_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[ \u00a0\u202f.,]\d{3})+|\d+)[.,](\d{2})(?!\d)")


def find_amounts(line: str) -> list[float]:
    out = []
    for m in AMOUNT_RE.finditer(line):
        whole = re.sub(r"[ \u00a0\u202f.,]", "", m.group(1))
        out.append(float(f"{whole}.{m.group(2)}"))
    return out


MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
    "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
}


def _iso(y: int, m: int, d: int):
    try:
        return date(y, m, d).isoformat()
    except ValueError:
        return None


def parse_date(text: str):
    """Return an ISO date string or None. Numeric dates are read as DD/MM/YYYY."""
    t = unaccent(text)
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", t)
    if m:
        return _iso(int(m[1]), int(m[2]), int(m[3]))
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", t)
    if m:
        return _iso(int(m[3]), int(m[2]), int(m[1]))
    for m in re.finditer(r"\b(\d{1,2})\s+([A-Za-z]+)\.?\s+(\d{4})\b", t):  # 5 mars 2024
        if m[2].lower() in MONTHS:
            return _iso(int(m[3]), MONTHS[m[2].lower()], int(m[1]))
    for m in re.finditer(r"\b([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})\b", t):  # March 05, 2024
        if m[1].lower() in MONTHS:
            return _iso(int(m[3]), MONTHS[m[1].lower()], int(m[2]))
    return None