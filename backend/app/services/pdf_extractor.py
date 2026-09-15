import  fitz

from backend.app.services.document_validator import validate_pdf
from backend.app.services.table_extractor import extract_tables_from_page

MIN_TEXT_LENGTH = 70
HIGH_IMAGE_COVERAGE = 0.60
VERY_HIGH_IMAGE_COVERAGE = 0.80
LOW_TEXT_DENSITY = 0.002

def calculate_image_coverage(page):
    """
    Estimate how much of the page is occupied by images.
    """
    page_area = page.rect.width *page.rect.height

    if page_area ==0:
        return 0.0

    image_area = 0.0

    for image in page.get_images(full=True):
        try:
            image_rects = page.get_image_rects(image)

            for rect in image_rects:
                image_area +=rect.width *rect.height

        except Exception:
            continue

    coverage = image_area / page_area

    #prevent impossible values caused by overlapping images.
    return min(coverage, 1.0)

def calculate_text_density(page,text):
    """
    Estimate how much text exists relative to page area.
    """

    page_area = page.rect.width *page.rect.height

    if page_area ==0:
        return 0.0

    return len(text.strip()) / page_area

# def calculate_ocr_score(
#         text_length,
#         image_count,
#         image_coverage,
#         text_density
# ):
#     """
#     Calculate a heuristic OCR score.
#     Higher score means the page is more likely to benefit from OCR."""

#     score=0
#     # Very little extracted text
#     if text_length < MIN_TEXT_LENGTH:
#         score += 2

#     # Large image area
#     if image_coverage >= HIGH_IMAGE_COVERAGE:
#         score += 2

#     # Extremely image-heavy page
#     if image_coverage >= VERY_HIGH_IMAGE_COVERAGE:
#         score += 1

#     # Very low text density
#     if text_density < LOW_TEXT_DENSITY:
#         score += 1

#     # Page contains images
#     if image_count > 0:
#         score += 1

#     return score

def classify_page(
    text_length,
    image_count,
    image_coverage,
    # text_density,
    # ocr_score
):
    """
    Classify the page based on its content characteristics.
    """

    has_text = text_length >= MIN_TEXT_LENGTH
    has_image = image_count > 0

    if has_text and has_image:
        return "MIXED"

    if has_image and not has_text:
        return "IMAGE_HEAVY"

    if has_text:
        return "TEXT"

    return "EMPTY"

    # Strong indication of a scanned/image page
    # if ocr_score >= 5 and image_coverage >= 0.80:
    #     return "SCANNED"

    # # Large amount of visual content
    # if image_coverage >= 0.60:
    #     return "IMAGE_HEAVY"

    # # Text + images
    # if image_count > 0 and text_length >= MIN_TEXT_LENGTH:
    #     return "MIXED"

    # # Very little text and no significant images
    # if text_length < MIN_TEXT_LENGTH:
    #     return "SCANNED"

    # # Default
    # return "TEXT"

def extract_pdf(file_path:str) ->dict:
    """
    Extract text from a PDF page by page.

    Pages with very little extracted text are flagged
    as possible OCR candidates.
    """

    #Validate the document
    validate_pdf(file_path)

    #open PDF
    pdf = fitz.open(file_path)

    pages = []
    # ocr_candidates = []
    try:

    #process every page
        for page_number, page in enumerate(pdf, start=1):
            # Extract text
            text = page.get_text("text").strip()

            # Count images
            images = page.get_images(full=True)
            image_count = len(images)

            # Calculate image coverage
            image_coverage = calculate_image_coverage(page)

            # Calculate text density
            text_density = calculate_text_density(
                page,
                text
            )

            # -----------------------------
                # Table extraction
                # -----------------------------

            tables = extract_tables_from_page(page)

            has_table = len(tables) > 0

            # # Calculate OCR score
            # ocr_score = calculate_ocr_score(
            #     text_length=len(text),
            #     image_count=image_count,
            #     image_coverage=image_coverage,
            #     text_density=text_density
            # )

        #     
        # -----------------------------
                # Content detection
                # -----------------------------

            has_text = len(text) >= MIN_TEXT_LENGTH

            has_image = image_count > 0

            content_type = classify_page(
                    text_length=len(text),
                    image_count=image_count,
                    image_coverage=image_coverage
                )

            content_types = []

            if has_text:
                    content_types.append("text")

            if has_table:
                    content_types.append("table")

            if has_image:
                    content_types.append("image")

                # -----------------------------
                # Page data
                # -----------------------------

            page_data = {
                    "page_number": page_number,

                    "text": text,

                    "text_length": len(text),

                    "image_count": image_count,

                    "image_coverage": round(
                        image_coverage,
                        3
                    ),

                    "text_density": round(
                        text_density,
                        5
                    ),

                    "content_type": content_type,

                    "content_types": content_types,

                    "has_text": has_text,

                    "has_table": has_table,

                    "has_image": has_image,

                    "tables": tables
                }

            pages.append(page_data)

    finally:
        pdf.close()

    return {
        "file_path": file_path,
        "page_count": len(pages),
        "pages": pages
    }