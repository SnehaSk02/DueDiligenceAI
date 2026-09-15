from backend.app.services.pdf_extractor import extract_pdf
from backend.app.services.document_parser import build_page_content
from backend.app.services.chunker import build_chunks, chunk_text

PDF_PATH = "uploads/cases/due_diligence_sample.pdf"

CASE_ID =1
DOCUMENT_ID =1
DOCUMENT_TYPE= "Annual Report"

#extract pdf
pdf_result = extract_pdf(PDF_PATH)
print("\n==============================")
print("PDF EXTRACTION")
print("==============================")

print("Total pages:", pdf_result["page_count"])

print("\n==============================")
print("PAGE CONTENT CHECK")
print("==============================")

for page in pdf_result["pages"]:
    print("\nPage:", page["page_number"])
    print("Text length:", page["text_length"])
    print("Content type:", page["content_type"])
    print("Content types:", page["content_types"])
    print("Has text:", page["has_text"])
    print("Has table:", page["has_table"])
    print("Number of tables:", len(page["tables"]))

#Parse pages
parsed_pages=[]
for page in pdf_result["pages"]:
    parsed_page = build_page_content(page)
    parsed_pages.append(parsed_page)

print("\n==============================")
print("PARSED PAGE CHECK")
print("==============================")

for page in parsed_pages:
    print("\nPage:", page["page_number"])
    print("Text length:", len(page["text"]))
    print("Has text:", page["has_text"])
    print("Has table:", page["has_table"])
    print("Number of tables:", len(page["tables"]))

print("\n==============================")
print("PAGE 2 CHUNK TEST")
print("==============================")

page_2 = parsed_pages[1]

print("Page number:", page_2["page_number"])
print("Text length:", len(page_2["text"]))

text_chunks = chunk_text(
    text=page_2["text"],
    chunk_size=1000,
    chunk_overlap=150
)

print("Text chunks:", len(text_chunks))

for i, chunk in enumerate(text_chunks):
    print("\nChunk", i)
    print(chunk[:300])

#build chunks
chunks = build_chunks(parsed_pages=parsed_pages,
                      case_id=CASE_ID,
                      document_id=DOCUMENT_ID,
                      document_type=DOCUMENT_TYPE)

print("\n==============================")
print("CHUNKS BY PAGE")
print("==============================")

for page_number in range(
    1,
    pdf_result["page_count"] + 1
):

    page_chunks = [
        chunk
        for chunk in chunks
        if chunk["page_number"] == page_number
    ]

    print(
        f"Page {page_number}: "
        f"{len(page_chunks)} chunks"
    )

#display results
print("\n==============================")
print("CHUNKING RESULT")
print("==============================")

print("Total chunks:",len(chunks))


for chunk in chunks:

    print("\n------------------------------")

    print("Chunk index:",chunk["chunk_index"])

    print("Page:",chunk["page_number"])

    print("Content type:",chunk["content_type"])

    if chunk["content_type"] == "table":

        print("Table:",chunk["table_index"])

    print("\nText:")
    print(chunk["text"][:500])