"""Compare prompt variants on a few documents. Not cached; for diagnosis only.
   python -m scripts.probe_llm --n 6 --variants v1 v2 v3"""
import argparse
import json
import time

import requests

from docextract import config, llm
from docextract.metrics import FIELDS, field_match

V2 = (
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
               "date": "2025-01-07", "currency": "EUR", "subtotal": 117.5, "tax": 23.5, "total": 141.0}

VARIANTS = {
    "v1": (llm.SYSTEM, []),                         # current prompt
    "v2": (V2, []),                                 # explicit field definitions, abstain only if absent
    "v3": (V2, [(SHOT_TEXT, SHOT_ANSWER)]),         # v2 plus one worked example
}


def run(system, shots, text, model):
    messages = [{"role": "system", "content": system}]
    for t, a in shots:
        messages += [{"role": "user", "content": f"Invoice text:\n\n{t}"},
                     {"role": "assistant", "content": json.dumps(a, ensure_ascii=False)}]
    messages.append({"role": "user", "content": f"Invoice text:\n\n{text}"})
    payload = {"model": model, "stream": False, "keep_alive": "10m",
               "format": llm.InvoiceFields.model_json_schema(),
               "options": {"temperature": 0, "seed": 0, "num_ctx": config.LLM_NUM_CTX},
               "messages": messages}
    t0 = time.perf_counter()
    r = requests.post(f"{config.OLLAMA_URL}/api/chat", json=payload, timeout=config.LLM_TIMEOUT)
    r.raise_for_status()
    fields = llm.InvoiceFields.model_validate_json(r.json()["message"]["content"]).model_dump()
    return fields, time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS), choices=list(VARIANTS))
    ap.add_argument("--model", default=config.OLLAMA_MODEL)
    ap.add_argument("--data", default="data/synthetic")
    args = ap.parse_args()

    labels = json.loads((config.ROOT / args.data / "labels.json").read_text(encoding="utf-8"))
    ids = list(labels)[: args.n]
    cache = config.text_dir(args.data)
    llm.warm_up()

    for name in args.variants:
        system, shots = VARIANTS[name]
        counts = {"OK": 0, "WRONG": 0, "NONE": 0}
        total_s = 0.0
        print(f"\n===== {name} (model {args.model}) =====")
        for doc_id in ids:
            text = json.loads((cache / f"{doc_id}.json").read_text(encoding="utf-8"))["text"]
            fields, secs = run(system, shots, text, args.model)
            total_s += secs
            cells = []
            for f in FIELDS:
                truth = labels[doc_id]["fields"][f]
                if fields[f] is None:
                    status = "NONE"
                elif field_match(f, fields[f], truth):
                    status = "OK"
                else:
                    status = "WRONG"
                counts[status] += 1
                cells.append(f"{f}:{status}")
                if status == "WRONG":
                    print(f"    {doc_id} {f}: got {fields[f]!r}, truth {truth!r}")
            print(f"  {doc_id} {secs:4.1f}s  " + " ".join(cells))
        print(f"  TOTAL {counts}  mean {total_s / len(ids):.1f}s per document")


if __name__ == "__main__":
    main()