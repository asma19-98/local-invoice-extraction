import pytesseract
from PIL import Image, ImageDraw

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

img = Image.new("RGB", (600, 120), "white")
ImageDraw.Draw(img).text((20, 40), "Facture 2024-117  Total: 45,90 EUR", fill="black")
print(pytesseract.image_to_string(img, lang="eng+fra").strip())