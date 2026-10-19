from docextract.baseline import extract
from docextract.metrics import field_match, score
from docextract.normalize import find_amounts, parse_date

FR_INVOICE = """Dupont SA FACTURE
12 rue des Lilas
Facture n° FAC-2024-0012
Date : 5 mars 2024
Désignation Qté Prix unitaire Montant
Widget 2 10,00 € 20,00 €
Sous-total HT 1 000,00 €
TVA (20 %) 200,00 €
Total TTC 1 200,00 €
"""


def test_find_amounts_handles_locales():
    assert find_amounts("Total 1 234,56 €") == [1234.56]
    assert find_amounts("Total $1,234.56") == [1234.56]
    assert find_amounts("TVA (5,5 %) 12,34 €") == [12.34]


def test_parse_date_formats():
    assert parse_date("15 février 2024") == "2024-02-15"
    assert parse_date("March 05, 2023") == "2023-03-05"
    assert parse_date("03/04/2024") == "2024-04-03"  # numeric dates are read as DD/MM
    assert parse_date("2024-01-31") == "2024-01-31"


def test_baseline_on_french_invoice():
    r = extract(FR_INVOICE)
    assert r == {"vendor": "Dupont SA", "invoice_number": "FAC-2024-0012", "date": "2024-03-05",
                 "currency": "EUR", "subtotal": 1000.0, "tax": 200.0, "total": 1200.0}


def test_field_match_rules():
    assert field_match("total", 45.9, 45.90)
    assert not field_match("total", 45.99, 45.90)
    assert field_match("vendor", "Dupont, S.A.", "dupont s a")
    assert not field_match("invoice_number", None, "X1")


def test_score_precision_vs_recall():
    truth = {"d1": {"vendor": "A", "invoice_number": "1", "date": "2024-01-01",
                    "currency": "EUR", "subtotal": 1.0, "tax": 0.0, "total": 1.0}}
    perfect = score(truth, truth)
    assert perfect["overall"]["f1"] == 1.0 and perfect["exact_match"] == 1.0
    partial = score({"d1": {**truth["d1"], "total": None}}, truth)  # abstained on one field
    assert partial["overall"]["precision"] == 1.0
    assert partial["overall"]["recall"] < 1.0
    assert partial["exact_match"] == 0.0