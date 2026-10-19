import json

from docextract import config, llm

GOOD = {"vendor": "Acme", "invoice_number": "1", "date": "2024-01-01",
        "currency": "EUR", "subtotal": 1, "tax": 0, "total": 1}


def test_schema_normalizes_values():
    f = llm.InvoiceFields(currency=" eur ", date="2024-13-45", vendor="  Acme  ")
    assert f.currency == "EUR" and f.date is None and f.vendor == "Acme"


def test_extract_uses_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "LLM_CACHE_DIR", tmp_path)
    calls = []

    def fake_call(text):
        calls.append(text)
        return {"message": {"content": json.dumps(GOOD)}}

    monkeypatch.setattr(llm, "_call", fake_call)
    a, b = llm.extract("some invoice"), llm.extract("some invoice")
    assert a == b and a["total"] == 1.0 and len(calls) == 1


def test_extract_abstains_on_invalid_output(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "LLM_CACHE_DIR", tmp_path)
    monkeypatch.setattr(llm, "_call", lambda text: {"message": {"content": "not json"}})
    before = llm.extract.failures
    result = llm.extract("x")
    assert all(v is None for v in result.values())
    assert llm.extract.failures == before + 1