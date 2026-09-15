import fitz
from backend.app.services.table_extractor import extract_tables_from_page
from backend.app.services.table_normalizer import normalize_table
PDF_PATH = "uploads/cases/sample-tables.pdf"

pdf = fitz.open(PDF_PATH)


print("\n==============================")
print("TABLE NORMALIZATION RESULT")
print("==============================")

total_tables = 0
for page_number, page in enumerate(pdf, start=1):
    tables = extract_tables_from_page(page)

    if not tables:
        continue


    print(f"\nPAGE {page_number}")
    print("-" * 40)

    for table in tables:

        normalized_table = normalize_table(table)

        total_tables += 1

        print(
            f"\nTable {normalized_table['table_index']}"
        )

        print(
            "Status:",
            normalized_table["extraction_status"]
        )

        print(
            "Columns:",
            normalized_table["column_count"]
        )

        print(
            "Rows:",
            normalized_table["row_count"]
        )

        print("\nHeaders:")

        for header in normalized_table["headers"]:
            print(header)

        print("\nData:")

        for row in normalized_table["rows"]:
            print(row)


pdf.close()


print("\n==============================")
print("TOTAL TABLES:", total_tables)
print("==============================")