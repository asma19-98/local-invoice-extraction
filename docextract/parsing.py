"""Turn a PDF or image into text: native text layer first, OCR as fallback."""
import io
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import os
import pymupdf as fitz  # PyMuPDF (the `fitz` name is deprecated, which caused your warning)
import pytesseract
from PIL import Image

from . import config

log = logging.getLogger(__name__)
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
os.environ["TESSDATA_PREFIX"] = config.TESSDATA_DIR
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


@dataclass
class ParsedDoc:
    text: str
    method: str  # "native" or "ocr"
    seconds: float
    pages: int


def _page_lines(page) -> str:
    """Rebuild visual lines from words so labels and values share a line."""
    words = page.get_text("words")  # (x0, y0, x1, y1, word, block, line, wordno)
    words.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    lines, cur, cur_y = [], [], None
    for w in words:
        yc = (w[1] + w[3]) / 2
        if cur and abs(yc - cur_y) > 4:
            lines.append(cur)
            cur = []
        if not cur:
            cur_y = yc
        cur.append(w)
    if cur:
        lines.append(cur)
    return "\n".join(" ".join(w[4] for w in sorted(line, key=lambda w: w[0])) for line in lines)


def _ocr(img: Image.Image) -> str:
    return pytesseract.image_to_string(
        img, lang=config.OCR_LANGS, config=f"--psm {config.OCR_PSM}"
    )


def parse_document(path) -> ParsedDoc:
    path = Path(path)
    t0 = time.perf_counter()
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        with fitz.open(str(path)) as doc:
            native = "\n".join(_page_lines(p) for p in doc)
            if len(native.strip()) >= config.MIN_NATIVE_CHARS:
                return ParsedDoc(native, "native", time.perf_counter() - t0, len(doc))
            log.info("%s has no usable text layer, falling back to OCR", path.name)
            texts = []
            for p in doc:
                pix = p.get_pixmap(dpi=200)
                texts.append(_ocr(Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")))
            return ParsedDoc("\n".join(texts), "ocr", time.perf_counter() - t0, len(doc))

    if suffix in IMAGE_SUFFIXES:
        with Image.open(path) as img:
            text = _ocr(img.convert("RGB"))
        return ParsedDoc(text, "ocr", time.perf_counter() - t0, 1)

    raise ValueError(f"Unsupported file type: {path.suffix}")