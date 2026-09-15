from backend.app.services.pdf_extractor import extract_pdf

PDF_PATH = "uploads/cases/image-doc.pdf"

result = extract_pdf(PDF_PATH)

print("Page count:", result["page_count"])
print("OCR candidates:", result["ocr_candidates"])

for page in result["pages"]:
    print("Page:", page["page_number"])
    print("Content type:", page["content_type"])
    print("Text length:", page["text_length"])
    print("Image count:", page["image_count"])
    print("Image coverage:", page["image_coverage"])
    print("Text density:", page["text_density"])
    print("OCR score:", page["ocr_score"])
    print("Needs OCR:", page["needs_ocr"])
    print("Text preview:")
    print(page["text"][:500])