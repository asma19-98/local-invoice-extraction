"""LLM extractor: local model via Ollama, schema-constrained output, validated with Pydantic."""
import hashlib
import json
import logging
import time
from datetime import date

import requests
from pydantic import BaseModel, Field, ValidationError, field_validator

from . import config

log = logging.getLogger(__name__)
PROMPT_VERSION = "v1"  # bump when the prompt or schema changes, so old cached answers are not reused

SYSTEM = (
    "You extract data from invoice text. The text comes from a PDF or from OCR, so it may contain "
    "recognition errors, and it may be in English or French. Return only what is written in the text. "
    "Rules: use null for any field you cannot find or are not sure about; never guess or calculate "
    "values; write amounts as plain numbers with a dot as the decimal separator and no currency symbol "
    "(for example '1 234,56 EUR' becomes 1234.56); write the date as YYYY-MM-DD; give the currency as "
    "a 3-letter ISO code. The vendor is the company that issued the invoice, usually at the top of the "
    "document, not a street address. The subtotal is the amount before tax, the tax is the VAT/sales "
    "tax amount, and the total is the final amount due including tax."
)


class InvoiceFields(BaseModel):
    vendor: str | None = Field(None, description="Name of the company that issued the invoice")
    invoice_number: str | None = Field(None, description="Invoice identifier exactly as printed")
    date: str | None = Field(None, description="Invoice date, format YYYY-MM-DD")
    currency: str | None = Field(None, description="ISO 4217 code such as EUR, USD or GBP")
    subtotal: float | None = Field(None, description="Amount before tax, plain number")
    tax: float | None = Field(None, description="Tax amount, plain number")
    total: float | None = Field(None, description="Final amount due including tax, plain number")

    @field_validator("vendor", "invoice_number")
    @classmethod
    def _strip(cls, v):
        return v.strip() or None if v is not None else None

    @field_validator("currency")
    @classmethod
    def _currency(cls, v):
        return v.strip().upper() or None if v is not None else None

    @field_validator("date")
    @classmethod
    def _date(cls, v):
        if v is None:
            return None
        try:
            return date.fromisoformat(v.strip()).isoformat()
        except ValueError:
            return None  # an invalid date becomes an abstention


def _down(e: Exception) -> RuntimeError:
    return RuntimeError(f"Cannot reach Ollama at {config.OLLAMA_URL}. "
                        "Start the Ollama app (or run `ollama serve`) and retry.")


def warm_up() -> None:
    """Load the model into memory so the first document's timing is not inflated."""
    try:
        requests.post(f"{config.OLLAMA_URL}/api/generate",
                      json={"model": config.OLLAMA_MODEL, "keep_alive": "10m"},
                      timeout=config.LLM_TIMEOUT).raise_for_status()
    except requests.ConnectionError as e:
        raise _down(e) from e


def _call(text: str) -> dict:
    payload = {
        "model": config.OLLAMA_MODEL,
        "stream": False,
        "format": InvoiceFields.model_json_schema(),
        "keep_alive": "10m",
        "options": {"temperature": 0, "seed": 0, "num_ctx": config.LLM_NUM_CTX},
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": f"Invoice text:\n\n{text}"}],
    }
    try:
        r = requests.post(f"{config.OLLAMA_URL}/api/chat", json=payload, timeout=config.LLM_TIMEOUT)
        r.raise_for_status()
    except requests.ConnectionError as e:
        raise _down(e) from e
    return r.json()


def extract(text: str) -> dict:
    key = hashlib.sha256(f"{PROMPT_VERSION}|{config.OLLAMA_MODEL}|{text}".encode()).hexdigest()
    path = config.LLM_CACHE_DIR / f"{key}.json"
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        extract.last_seconds = cached["seconds"]  # report the original inference time
        return cached["fields"]

    t0 = time.perf_counter()
    try:
        data = _call(text)
        fields = InvoiceFields.model_validate_json(data["message"]["content"]).model_dump()
    except (requests.RequestException, ValueError, KeyError) as e:  # ValidationError is a ValueError
        extract.failures += 1
        extract.last_seconds = time.perf_counter() - t0
        log.warning("LLM extraction failed: %s", e)
        return {k: None for k in InvoiceFields.model_fields}

    seconds = time.perf_counter() - t0
    extract.last_seconds = seconds
    config.LLM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "fields": fields, "seconds": seconds, "model": config.OLLAMA_MODEL,
        "tokens": {"prompt": data.get("prompt_eval_count"), "output": data.get("eval_count")},
    }), encoding="utf-8")
    return fields


extract.failures = 0
extract.last_seconds = 0.0