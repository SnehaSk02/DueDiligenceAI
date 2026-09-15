import fitz

from backend.app.services.table_extractor import extract_tables_from_page


PDF_PATH = "uploads/cases/sample-tables.pdf"


pdf = fitz.open(PDF_PATH)


for page_number, page in enumerate(pdf, start=1):

    tables = extract_tables_from_page(page)

    if tables:

        print("\n================================")
        print("PAGE:", page_number)
        print("TABLES FOUND:", len(tables))
        print("================================")

        for table in tables:

            print("\nTable:", table["table_index"])
            print("Rows:", table["row_count"])
            print("Columns:", table["column_count"])

            for row in table["rows"]:
                print(row)


pdf.close()