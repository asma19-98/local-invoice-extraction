"""Generate synthetic EN/FR invoices with ground-truth labels."""
import argparse
import io
import json
import random
from datetime import date, timedelta
from pathlib import Path

import fitz  # PyMuPDF
from faker import Faker
from PIL import Image, ImageFilter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

FR_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
             "août", "septembre", "octobre", "novembre", "décembre"]
SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£"}
FONTS = {"Helvetica": "Helvetica-Bold", "Times-Roman": "Times-Bold", "Courier": "Courier-Bold"}

LABELS = {
    "en": {
        "title": "INVOICE",
        "number": ["Invoice No:", "Invoice #:", "Invoice Number:"],
        "date": ["Date:", "Invoice Date:", "Issued:"],
        "cols": ["Description", "Qty", "Unit price", "Amount"],
        "subtotal": ["Subtotal", "Sub-total", "Net amount"],
        "tax": ["VAT", "Tax", "Sales tax"],
        "total": ["Total", "Total Due", "Amount Due"],
    },
    "fr": {
        "title": "FACTURE",
        "number": ["Facture n°", "N° de facture :", "Facture no :"],
        "date": ["Date :", "Date de facture :", "Émise le :"],
        "cols": ["Désignation", "Qté", "Prix unitaire", "Montant"],
        "subtotal": ["Sous-total HT", "Total HT", "Montant HT"],
        "tax": ["TVA", "T.V.A."],
        "total": ["Total TTC", "Net à payer", "Montant TTC"],
    },
}


def safe(s: str) -> str:
    """Drop characters the built-in PDF fonts can't encode (keeps labels == rendered text)."""
    return s.encode("cp1252", "ignore").decode("cp1252")


def fmt_amount(x: float, lang: str) -> str:
    s = f"{x:,.2f}"
    if lang == "fr":
        s = s.replace(",", " ").replace(".", ",")
    return s


def money(x: float, lang: str, currency: str) -> str:
    sym, a = SYMBOLS[currency], fmt_amount(x, lang)
    return f"{a} {sym}" if lang == "fr" else f"{sym}{a}"


def fmt_date(d: date, lang: str, rng: random.Random) -> str:
    if lang == "fr":
        choice = rng.choice(["slash", "dash", "long"])
        if choice == "slash":
            return d.strftime("%d/%m/%Y")
        if choice == "dash":
            return d.strftime("%d-%m-%Y")
        return f"{d.day} {FR_MONTHS[d.month - 1]} {d.year}"
    return d.strftime(rng.choice(["%Y-%m-%d", "%B %d, %Y", "%d %b %Y"]))


def make_doc(lang: str, rng: random.Random, fake: Faker) -> dict:
    currency = "EUR" if lang == "fr" else rng.choice(["USD", "GBP", "EUR"])
    items = []
    for _ in range(rng.randint(2, 6)):
        qty = rng.randint(1, 10)
        unit = round(rng.uniform(5, 400), 2)
        items.append({"desc": safe(fake.catch_phrase())[:42], "qty": qty,
                      "unit": unit, "amount": round(qty * unit, 2)})
    subtotal = round(sum(i["amount"] for i in items), 2)
    rate = rng.choice([0.20, 0.10, 0.055]) if lang == "fr" else rng.choice([0.0, 0.05, 0.08, 0.10, 0.20])
    tax = round(subtotal * rate, 2)
    issued = date(2023, 1, 1) + timedelta(days=rng.randint(0, 900))
    prefix = "FAC" if lang == "fr" else "INV"
    n = rng.randint(1, 9999)
    number = rng.choice([f"{prefix}-{issued.year}-{n:04d}", f"{prefix}{issued.year}{n:05d}", str(1000 + n)])
    return {
        "truth": {
            "vendor": safe(fake.company()),
            "invoice_number": number,
            "date": issued.isoformat(),
            "currency": currency,
            "subtotal": subtotal,
            "tax": tax,
            "total": round(subtotal + tax, 2),
        },
        "items": items,
        "rate": rate,
        "address": [safe(fake.street_address()), safe(f"{fake.postcode()} {fake.city()}")],
        "date_text": fmt_date(issued, lang, rng),
    }


def render_pdf(path: Path, lang: str, doc: dict, rng: random.Random) -> None:
    t, items, rate = doc["truth"], doc["items"], doc["rate"]
    L = LABELS[lang]
    font = rng.choice(list(FONTS))
    bold = FONTS[font]
    W, H = A4
    c = canvas.Canvas(str(path), pagesize=A4)

    # Header
    c.setFont(bold, 16)
    c.drawString(50, H - 60, t["vendor"])
    c.setFont(font, 10)
    for k, line in enumerate(doc["address"]):
        c.drawString(50, H - 78 - 14 * k, line)
    c.setFont(bold, 22)
    c.drawRightString(W - 50, H - 60, L["title"])

    # Invoice number and date (left or right: layout variation)
    c.setFont(font, 11)
    if rng.random() < 0.5:
        x, draw = W - 50, c.drawRightString
    else:
        x, draw = 50, c.drawString
    draw(x, H - 140, f'{rng.choice(L["number"])} {t["invoice_number"]}')
    draw(x, H - 156, f'{rng.choice(L["date"])} {doc["date_text"]}')

    # Line items
    y = H - 230
    c.setFont(bold, 10)
    c.drawString(50, y, L["cols"][0])
    c.drawString(320, y, L["cols"][1])
    c.drawRightString(440, y, L["cols"][2])
    c.drawRightString(W - 50, y, L["cols"][3])
    c.line(50, y - 5, W - 50, y - 5)
    c.setFont(font, 10)
    for it in items:
        y -= 20
        c.drawString(50, y - 5, it["desc"])
        c.drawString(320, y - 5, str(it["qty"]))
        c.drawRightString(440, y - 5, money(it["unit"], lang, t["currency"]))
        c.drawRightString(W - 50, y - 5, money(it["amount"], lang, t["currency"]))

    # Totals (right-aligned or left-aligned block)
    pct = f"{rate * 100:g}"
    pct = pct.replace(".", ",") + " %" if lang == "fr" else pct + "%"
    rows = [
        (rng.choice(L["subtotal"]), t["subtotal"]),
        (f'{rng.choice(L["tax"])} ({pct})', t["tax"]),
        (rng.choice(L["total"]), t["total"]),
    ]
    lx, vx = (50, 250) if rng.random() < 0.3 else (360, W - 50)
    y -= 40
    for k, (label, val) in enumerate(rows):
        c.setFont(bold if k == 2 else font, 11)
        c.drawString(lx, y, label)
        c.drawRightString(vx, y, money(val, lang, t["currency"]))
        y -= 18
    c.save()


def to_scan(pdf_path: Path, png_path: Path, rng: random.Random) -> None:
    """Rasterize the PDF and degrade it so it looks like a scan; delete the PDF (no text layer)."""
    pdf = fitz.open(str(pdf_path))
    pix = pdf[0].get_pixmap(dpi=150)
    pdf.close()
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    img = img.rotate(rng.uniform(-2.0, 2.0), resample=Image.BICUBIC,
                     expand=True, fillcolor=(255, 255, 255))
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 0.9)))
    noise = Image.effect_noise(img.size, rng.uniform(10, 30)).convert("RGB")
    img = Image.blend(img, noise, 0.06)
    img.save(png_path)
    pdf_path.unlink()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/synthetic")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    Faker.seed(args.seed)
    fakes = {"en": Faker("en_US"), "fr": Faker("fr_FR")}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    labels = {}
    for i in range(args.n):
        lang = ["en", "fr"][i % 2]
        kind = ["pdf", "scan"][(i // 2) % 2]
        doc = make_doc(lang, rng, fakes[lang])
        doc_id = f"{lang}_{kind}_{i:04d}"
        pdf_path = out / f"{doc_id}.pdf"
        render_pdf(pdf_path, lang, doc, rng)
        if kind == "scan":
            file = f"{doc_id}.png"
            to_scan(pdf_path, out / file, rng)
        else:
            file = pdf_path.name
        labels[doc_id] = {"file": file, "lang": lang, "kind": kind, "fields": doc["truth"]}

    (out / "labels.json").write_text(
        json.dumps(labels, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(labels)} documents to {out}")


if __name__ == "__main__":
    main()