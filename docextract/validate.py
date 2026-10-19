"""Deterministic checks and arithmetic repair for extracted invoices."""
from datetime import date

TOL = 0.015  # one cent of rounding slack
REQUIRED = ["vendor", "invoice_number", "date", "currency", "subtotal", "tax", "total"]
AMOUNTS = ["subtotal", "tax", "total"]
KNOWN_CURRENCIES = {"EUR", "USD", "GBP"}


def check(fields: dict) -> list[str]:
    """Return the list of problems found. An empty list means every check passed."""
    problems = [f"missing_{k}" for k in REQUIRED if fields.get(k) is None]

    for k in AMOUNTS:
        v = fields.get(k)
        if v is not None and v < 0:
            problems.append(f"negative_{k}")

    sub, tax, tot = (fields.get(k) for k in AMOUNTS)
    if None not in (sub, tax, tot) and abs(sub + tax - tot) > TOL:
        problems.append("totals_mismatch")

    cur = fields.get("currency")
    if cur is not None and cur not in KNOWN_CURRENCIES:
        problems.append("unknown_currency")

    d = fields.get("date")
    if d is not None:
        try:
            date.fromisoformat(d)
        except ValueError:
            problems.append("bad_date")
    return problems


def repair(fields: dict) -> tuple[dict, list[str]]:
    """If exactly one of subtotal/tax/total is missing, derive it from the other two."""
    out = dict(fields)
    missing = [k for k in AMOUNTS if out.get(k) is None]
    if len(missing) != 1:
        return out, []

    m = missing[0]
    if m == "subtotal":
        val = out["total"] - out["tax"]
    elif m == "tax":
        val = out["total"] - out["subtotal"]
    else:
        val = out["subtotal"] + out["tax"]

    if val < 0:  # an impossible result means one of the inputs is wrong too
        return out, []
    out[m] = round(val, 2)
    return out, [f"derived_{m}"]