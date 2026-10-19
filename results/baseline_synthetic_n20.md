# Results: baseline_synthetic_n20

Documents: 20

## Field-level scores

| Field | Precision | Recall | F1 |
|---|---|---|---|
| vendor | 100.0% | 100.0% | 100.0% |
| invoice_number | 100.0% | 100.0% | 100.0% |
| date | 100.0% | 100.0% | 100.0% |
| currency | 100.0% | 100.0% | 100.0% |
| subtotal | 100.0% | 90.0% | 94.7% |
| tax | 100.0% | 95.0% | 97.4% |
| total | 100.0% | 100.0% | 100.0% |
| **overall (micro)** | 100.0% | 97.9% | 98.9% |

Documents with every field correct: **85.0%**

## By group

| Group | Docs | F1 (micro) | All fields correct |
|---|---|---|---|
| all | 20 | 98.9% | 85.0% |
| lang=en | 10 | 99.3% | 90.0% |
| lang=fr | 10 | 98.6% | 80.0% |
| kind=pdf | 10 | 100.0% | 100.0% |
| kind=scan | 10 | 97.8% | 70.0% |
| en/pdf | 5 | 100.0% | 100.0% |
| en/scan | 5 | 98.6% | 80.0% |
| fr/pdf | 5 | 100.0% | 100.0% |
| fr/scan | 5 | 97.1% | 60.0% |

## Timing (this machine, CPU only)

| Parse method | Docs | Mean parse time | Mean extract time |
|---|---|---|---|
| native | 10 | 0.05 s | 1.2 ms |
| ocr | 10 | 1.43 s | 1.0 ms |