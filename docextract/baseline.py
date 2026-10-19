"""Rule-based extractor: the baseline any LLM approach must beat."""
import re

from .normalize import find_amounts, parse_date, unaccent

TITLE_RE = re.compile(r"\b(invoice|facture)\b", re.I)
NUMBER_RE = re.compile(
    r"(?:invoice[ \t]*(?:no\.?|number|#)|facture[ \t]*(?:no|n\W{0,2})|n\W{0,2}[ \t]*de[ \t]*facture)"
    r"[ \t]*[:.]?[ \t]*([A-Z0-9][A-Z0-9\-]{2,})",
    re.I,
)
SUBTOTAL_RE = re.compile(r"sub-?\s?total|sous-?\s?total|total\s+ht|montant\s+ht|net\s+amount")
TAX_RE = re.compile(r"\btva\b|t\.v\.a|\bvat\b|\btax\b")
TOTAL_RE = re.compile(r"total\s+ttc|net\s+a\s+payer|montant\s+ttc|total\s+due|amount\s+due|\btotal\b")
DATE_LABEL_RE = re.compile(r"\bdate\b|issued|emise le")
CURRENCY_RE = re.compile(r"(€|\$|£|\bEUR\b|\bUSD\b|\bGBP\b)")
CURRENCY_MAP = {"€": "EUR", "EUR": "EUR", "$": "USD", "USD": "USD", "£": "GBP", "GBP": "GBP"}


def extract(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    out = {k: None for k in
           ("vendor", "invoice_number", "date", "currency", "subtotal", "tax", "total")}

    for l in lines:  # vendor = first non-empty line minus the "INVOICE"/"FACTURE" title
        v = TITLE_RE.sub("", l).strip(" -|:,")
        if v:
            out["vendor"] = v
            break

    for l in lines:
        m = NUMBER_RE.search(l)
        if m:
            out["invoice_number"] = m.group(1)
            break

    dated = [l for l in lines if DATE_LABEL_RE.search(unaccent(l).lower())]
    out["date"] = parse_date("\n".join(dated)) or parse_date(text)

    m = CURRENCY_RE.search(text)
    if m:
        out["currency"] = CURRENCY_MAP[m.group(1)]

    # Totals sit at the bottom of an invoice, so the LAST matching line wins.
    for l in lines:
        low = unaccent(l).lower()
        amounts = find_amounts(l)
        if not amounts:
            continue
        if SUBTOTAL_RE.search(low):
            out["subtotal"] = amounts[-1]
        elif TAX_RE.search(low):
            out["tax"] = amounts[-1]
        elif TOTAL_RE.search(low):
            out["total"] = amounts[-1]
    return out