# Results: baseline_synthetic

Documents: 120

## Field-level scores

| Field | Precision | Recall | F1 |
|---|---|---|---|
| vendor | 99.2% | 99.2% | 99.2% |
| invoice_number | 100.0% | 100.0% | 100.0% |
| date | 100.0% | 100.0% | 100.0% |
| currency | 99.2% | 99.2% | 99.2% |
| subtotal | 100.0% | 98.3% | 99.2% |
| tax | 100.0% | 97.5% | 98.7% |
| total | 100.0% | 100.0% | 100.0% |
| **overall (micro)** | 99.8% | 99.2% | 99.5% |

Documents with every field correct: **94.2%**

## By group

| Group | Docs | F1 (micro) | All fields correct |
|---|---|---|---|
| all | 120 | 99.5% | 94.2% |
| lang=en | 60 | 99.5% | 95.0% |
| lang=fr | 60 | 99.4% | 93.3% |
| kind=pdf | 60 | 100.0% | 100.0% |
| kind=scan | 60 | 98.9% | 88.3% |
| en/pdf | 30 | 100.0% | 100.0% |
| en/scan | 30 | 99.0% | 90.0% |
| fr/pdf | 30 | 100.0% | 100.0% |
| fr/scan | 30 | 98.8% | 86.7% |

## Timing (this machine, CPU only)

| Parse method | Docs | Mean parse time | Mean extract time |
|---|---|---|---|
| native | 60 | 0.08 s | 1.1 ms |
| ocr | 60 | 1.51 s | 0.9 ms |

## Review routing (documents with failed checks go to a human)

| Outcome | Docs | Fully correct |
|---|---|---|
| auto-accepted | 115 | 113 |
| flagged for review | 5 | 0 |

Silent errors (auto-accepted but wrong): **2**