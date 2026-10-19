"""Run an extractor over the cached text and print/save the results table."""
import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

from docextract import baseline, config
from docextract.metrics import FIELDS, field_match, score
from docextract.validate import check, repair
def baseline_repaired(text):
    return repair(baseline.extract(text))[0]


EXTRACTORS = {"baseline": baseline.extract, "baseline_repaired": baseline_repaired}

def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractor", default="baseline", choices=EXTRACTORS)
    ap.add_argument("--data", default="data/synthetic")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--show-errors", type=int, default=0)
    args = ap.parse_args()

    data_dir = Path(args.data)
    labels = json.loads((data_dir / "labels.json").read_text(encoding="utf-8"))
    ids = list(labels)[: args.limit] if args.limit else list(labels)
    extract = EXTRACTORS[args.extractor]
    cache = config.text_dir(data_dir)

    preds, truths, parse_s, extract_s = {}, {}, defaultdict(list), defaultdict(list)
    for doc_id in ids:
        f = cache / f"{doc_id}.json"
        if not f.exists():
            print(f"skipping {doc_id}: run scripts.build_text first")
            continue
        parsed = json.loads(f.read_text(encoding="utf-8"))
        t0 = time.perf_counter()
        preds[doc_id] = extract(parsed["text"])
        extract_s[parsed["method"]].append(time.perf_counter() - t0)
        parse_s[parsed["method"]].append(parsed["seconds"])
        truths[doc_id] = labels[doc_id]["fields"]

    if not truths:
        raise SystemExit("No documents evaluated.")

    s = score(preds, truths)
    name = f"{args.extractor}_{data_dir.name}" + (f"_n{args.limit}" if args.limit else "")

    md = [f"# Results: {name}", "", f"Documents: {s['n']}", "",
          "## Field-level scores", "",
          "| Field | Precision | Recall | F1 |", "|---|---|---|---|"]
    for fld in FIELDS:
        r = s["fields"][fld]
        md.append(f"| {fld} | {pct(r['precision'])} | {pct(r['recall'])} | {pct(r['f1'])} |")
    o = s["overall"]
    md.append(f"| **overall (micro)** | {pct(o['precision'])} | {pct(o['recall'])} | {pct(o['f1'])} |")
    md += ["", f"Documents with every field correct: **{pct(s['exact_match'])}**", "",
           "## By group", "", "| Group | Docs | F1 (micro) | All fields correct |", "|---|---|---|---|"]

    groups = {"all": list(truths)}
    for key in ("lang", "kind"):
        for v in sorted({labels[d][key] for d in truths}):
            groups[f"{key}={v}"] = [d for d in truths if labels[d][key] == v]
    for lang in sorted({labels[d]["lang"] for d in truths}):
        for kind in sorted({labels[d]["kind"] for d in truths}):
            groups[f"{lang}/{kind}"] = [d for d in truths
                                         if labels[d]["lang"] == lang and labels[d]["kind"] == kind]
    for g, gids in groups.items():
        gs = score({d: preds[d] for d in gids}, {d: truths[d] for d in gids})
        md.append(f"| {g} | {gs['n']} | {pct(gs['overall']['f1'])} | {pct(gs['exact_match'])} |")

    md += ["", "## Timing (this machine, CPU only)", "",
           "| Parse method | Docs | Mean parse time | Mean extract time |", "|---|---|---|---|"]
    for m in sorted(parse_s):
        md.append(f"| {m} | {len(parse_s[m])} | {sum(parse_s[m]) / len(parse_s[m]):.2f} s | "
                  f"{1000 * sum(extract_s[m]) / len(extract_s[m]):.1f} ms |")
    def all_ok(d):
        return all(field_match(f, preds[d].get(f), truths[d][f]) for f in FIELDS)

    accepted = [d for d in truths if not check(preds[d])]
    flagged = [d for d in truths if check(preds[d])]
    silent = [d for d in accepted if not all_ok(d)]
    md += ["", "## Review routing (documents with failed checks go to a human)", "",
           "| Outcome | Docs | Fully correct |", "|---|---|---|",
           f"| auto-accepted | {len(accepted)} | {len(accepted) - len(silent)} |",
           f"| flagged for review | {len(flagged)} | {sum(all_ok(d) for d in flagged)} |",
           "", f"Silent errors (auto-accepted but wrong): **{len(silent)}**"]
    report = "\n".join(md)
    print(report)
    config.RESULTS_DIR.mkdir(exist_ok=True)
    (config.RESULTS_DIR / f"{name}.md").write_text(report, encoding="utf-8")
    (config.RESULTS_DIR / f"{name}_predictions.json").write_text(
        json.dumps(preds, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.show_errors:
        print("\n## Sample errors\n")
        shown = 0
        for d in truths:
            for fld in FIELDS:
                if not field_match(fld, preds[d].get(fld), truths[d][fld]) and shown < args.show_errors:
                    print(f"{d:<18} {fld:<15} predicted={preds[d].get(fld)!r:<28} truth={truths[d][fld]!r}")
                    shown += 1


if __name__ == "__main__":
    main()