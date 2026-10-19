"""Print the cached parsed text for documents: python -m scripts.show_text fr_scan_0003 ..."""
import json
import sys

from docextract import config

for doc_id in sys.argv[1:]:
    f = config.text_dir("data/synthetic") / f"{doc_id}.json"
    print(f"===== {doc_id} =====")
    print(json.loads(f.read_text(encoding="utf-8"))["text"])