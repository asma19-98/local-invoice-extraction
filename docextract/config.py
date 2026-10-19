import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"

TESSERACT_CMD = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA_DIR = os.environ.get("TESSDATA_DIR", str(ROOT / "tessdata"))
OCR_LANGS = os.environ.get("OCR_LANGS", "eng+fra")
OCR_PSM = os.environ.get("OCR_PSM", "6")  # 6 = assume one uniform block of text
MIN_NATIVE_CHARS = 30  # fewer characters than this => treat the PDF as a scan


def text_dir(data_dir) -> Path:
    """Where cached parsed text lives for a given dataset folder."""
    return ROOT / "data" / "text" / Path(data_dir).name