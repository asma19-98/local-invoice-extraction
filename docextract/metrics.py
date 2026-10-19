"""Field-level evaluation."""
import re

from .normalize import unaccent

FIELDS = ["vendor", "invoice_number", "date", "currency", "subtotal", "tax", "total"]
AMOUNTS = {"subtotal", "tax", "total"}


def _norm_text(s) -> str:
    s = unaccent(str(s)).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", s).split())


def _norm_id(s) -> str:
    return "".join(str(s).split()).casefold()


def field_match(field: str, pred, truth) -> bool:
    if pred is None:
        return False
    try:
        if field in AMOUNTS:
            return abs(float(pred) - float(truth)) < 0.005
        if field == "vendor":
            return _norm_text(pred) == _norm_text(truth)
        if field == "invoice_number":
            return _norm_id(pred) == _norm_id(truth)
        return str(pred).strip().upper() == str(truth).strip().upper()
    except (TypeError, ValueError):
        return False


def prf(tp: int, n_pred: int, n_truth: int) -> dict:
    p = tp / n_pred if n_pred else 0.0
    r = tp / n_truth if n_truth else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": p, "recall": r, "f1": f}


def score(preds: dict, truths: dict) -> dict:
    """preds/truths: doc_id -> {field: value}. One value per field per document."""
    stats = {f: {"tp": 0, "n_pred": 0, "n_truth": 0} for f in FIELDS}
    exact = 0
    for doc_id, truth in truths.items():
        pred = preds.get(doc_id, {})
        all_ok = True
        for f in FIELDS:
            stats[f]["n_truth"] += 1
            if pred.get(f) is not None:
                stats[f]["n_pred"] += 1
            ok = field_match(f, pred.get(f), truth[f])
            stats[f]["tp"] += int(ok)
            all_ok = all_ok and ok
        exact += int(all_ok)

    fields = {f: {**s, **prf(s["tp"], s["n_pred"], s["n_truth"])} for f, s in stats.items()}
    tp = sum(s["tp"] for s in stats.values())
    n_pred = sum(s["n_pred"] for s in stats.values())
    n_truth = sum(s["n_truth"] for s in stats.values())
    n = len(truths)
    return {"n": n, "fields": fields, "overall": prf(tp, n_pred, n_truth),
            "exact_match": exact / n if n else 0.0}