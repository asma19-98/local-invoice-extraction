"""Prompt and worked example for the LLM extractor (version recorded in llm.PROMPT_VERSION)."""

SYSTEM = (
    "You extract data from invoice text. The text comes from a PDF or from OCR and may contain "
    "recognition errors; it is in English or French. Fill every field that appears in the text. "
    "Use null only when a field is truly absent or unreadable. "
    "invoice_number: the identifier printed next to 'Invoice No', 'Invoice #', 'Facture n°' and "
    "similar labels, copied exactly. "
    "date: the invoice date converted to YYYY-MM-DD (for example '5 mars 2024' becomes '2024-03-05', "
    "and numeric dates are day/month/year, so '05/03/2024' also becomes '2024-03-05'). "
    "currency: a 3-letter code; the symbol € means EUR, $ means USD and £ means GBP. "
    "vendor: the name of the company that issued the invoice, at the top of the document; do not "
    "include the word INVOICE or FACTURE and do not include an address. "
    "subtotal: the amount before tax. tax: the tax amount in money, not the percentage. "
    "total: the final amount due including tax. "
    "Amounts are plain numbers with a dot as the decimal separator and no symbols or spaces "
    "('1 234,56 €' becomes 1234.56)."
)

SHOT_TEXT = """Atelier Morel SARL FACTURE
14 rue du Port
13002 Marseille
Facture n° FAC-2025-0042
Date : 7 janvier 2025
Désignation Qté Prix unitaire Montant
Câble réseau 3 12,50 € 37,50 €
Routeur 1 80,00 € 80,00 €
Sous-total HT 117,50 €
TVA (20 %) 23,50 €
Total TTC 141,00 €"""

SHOT_ANSWER = {"vendor": "Atelier Morel SARL", "invoice_number": "FAC-2025-0042",
               "date": "2025-01-07", "currency": "EUR",
               "subtotal": 117.5, "tax": 23.5, "total": 141.0}