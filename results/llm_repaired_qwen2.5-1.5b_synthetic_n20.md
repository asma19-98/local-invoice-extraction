# Results: llm_repaired_qwen2.5-1.5b_synthetic_n20

Documents: 20

## Field-level scores

| Field | Precision | Recall | F1 |
|---|---|---|---|
| vendor | 87.5% | 70.0% | 77.8% |
| invoice_number | 100.0% | 10.0% | 18.2% |
| date | 100.0% | 10.0% | 18.2% |
| currency | 0.0% | 0.0% | 0.0% |
| subtotal | 84.6% | 55.0% | 66.7% |
| tax | 92.3% | 60.0% | 72.7% |
| total | 95.0% | 95.0% | 95.0% |
| **overall (micro)** | 90.9% | 42.9% | 58.3% |

Documents with every field correct: **0.0%**

## By group

| Group | Docs | F1 (micro) | All fields correct |
|---|---|---|---|
| all | 20 | 58.3% | 0.0% |
| lang=en | 10 | 56.6% | 0.0% |
| lang=fr | 10 | 59.8% | 0.0% |
| kind=pdf | 10 | 62.7% | 0.0% |
| kind=scan | 10 | 53.8% | 0.0% |
| en/pdf | 5 | 60.0% | 0.0% |
| en/scan | 5 | 53.1% | 0.0% |
| fr/pdf | 5 | 65.4% | 0.0% |
| fr/scan | 5 | 54.5% | 0.0% |

## Timing (this machine, CPU only)

| Parse method | Docs | Mean parse time | Mean extract time |
|---|---|---|---|
| native | 10 | 0.05 s | 17330.2 ms |
| ocr | 10 | 1.43 s | 18037.5 ms |

## Review routing (documents with failed checks go to a human)

| Outcome | Docs | Fully correct |
|---|---|---|
| auto-accepted | 0 | 0 |
| flagged for review | 20 | 0 |

Silent errors (auto-accepted but wrong): **0**

LLM calls that failed (counted as abstentions): **0**