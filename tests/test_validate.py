from docextract.validate import check, repair

GOOD = {"vendor": "A", "invoice_number": "1", "date": "2024-01-01", "currency": "EUR",
        "subtotal": 100.0, "tax": 20.0, "total": 120.0}


def test_check_passes_consistent_invoice():
    assert check(GOOD) == []


def test_check_flags_arithmetic_mismatch():
    assert "totals_mismatch" in check({**GOOD, "total": 121.0})


def test_check_flags_missing_and_invalid_values():
    assert "missing_tax" in check({**GOOD, "tax": None})
    assert "bad_date" in check({**GOOD, "date": "2024-13-45"})
    assert "unknown_currency" in check({**GOOD, "currency": "XYZ"})


def test_repair_derives_each_missing_amount():
    for field in ("subtotal", "tax", "total"):
        fixed, notes = repair({**GOOD, field: None})
        assert fixed[field] == GOOD[field]
        assert notes == [f"derived_{field}"]


def test_repair_refuses_to_guess_with_two_missing():
    fixed, notes = repair({**GOOD, "tax": None, "total": None})
    assert notes == [] and fixed["tax"] is None