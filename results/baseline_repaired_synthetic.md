# Results: baseline_repaired_synthetic

Documents: 120

## Field-level scores

| Field | Precision | Recall | F1 |
|---|---|---|---|
| vendor | 99.2% | 99.2% | 99.2% |
| invoice_number | 100.0% | 100.0% | 100.0% |
| date | 100.0% | 100.0% | 100.0% |
| currency | 99.2% | 99.2% | 99.2% |
| subtotal | 100.0% | 100.0% | 100.0% |
| tax | 100.0% | 100.0% | 100.0% |
| total | 100.0% | 100.0% | 100.0% |
| **overall (micro)** | 99.8% | 99.8% | 99.8% |

Documents with every field correct: **98.3%**

## By group

| Group | Docs | F1 (micro) | All fields correct |
|---|---|---|---|
| all | 120 | 99.8% | 98.3% |
| lang=en | 60 | 99.8% | 98.3% |
| lang=fr | 60 | 99.8% | 98.3% |
| kind=pdf | 60 | 100.0% | 100.0% |
| kind=scan | 60 | 99.5% | 96.7% |
| en/pdf | 30 | 100.0% | 100.0% |
| en/scan | 30 | 99.5% | 96.7% |
| fr/pdf | 30 | 100.0% | 100.0% |
| fr/scan | 30 | 99.5% | 96.7% |

## Timing (this machine, CPU only)

| Parse method | Docs | Mean parse time | Mean extract time |
|---|---|---|---|
| native | 60 | 0.08 s | 0.6 ms |
| ocr | 60 | 1.51 s | 0.7 ms |

## Review routing (documents with failed checks go to a human)

| Outcome | Docs | Fully correct |
|---|---|---|
| auto-accepted | 120 | 118 |
| flagged for review | 0 | 0 |

Silent errors (auto-accepted but wrong): **2**