"""Parse every document once and cache the text (OCR is the slow part)."""
import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

from docextract import config
from docextract.parsing import parse_document

log = logging.getLogger("build_text")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/synthetic")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    data_dir = Path(args.data)
    labels = json.loads((data_dir / "labels.json").read_text(encoding="utf-8"))
    ids = list(labels)[: args.limit] if args.limit else list(labels)
    out_dir = config.text_dir(data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for doc_id in ids:
        out = out_dir / f"{doc_id}.json"
        if out.exists() and not args.force:
            continue
        try:
            parsed = parse_document(data_dir / labels[doc_id]["file"])
        except Exception:
            log.exception("failed to parse %s", doc_id)
            continue
        out.write_text(json.dumps(asdict(parsed), ensure_ascii=False), encoding="utf-8")
        log.info("%s method=%s %.2fs", doc_id, parsed.method, parsed.seconds)


if __name__ == "__main__":
    main()