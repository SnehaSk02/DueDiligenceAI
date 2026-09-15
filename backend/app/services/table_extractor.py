import fitz

def extract_tables_from_page(page):
    """
    Detect and extract tables from a PDF page.

    Returns:
        A list of extracted table dictionaries.
    """

    extracted_tables = []

    try:

        tables = page.find_tables()

        for table_index, table in enumerate(
            tables.tables
        ):

            rows = table.extract()

            if not rows:
                continue

            extracted_tables.append({
                "content_type": "table",

                "table_index": table_index,

                "rows": rows,

                "row_count": len(rows),

                "column_count": max(
                    (
                        len(row)
                        for row in rows
                    ),
                    default=0
                ),

                "extraction_status": "success"
            })

    except Exception as e:

        extracted_tables.append({
            "content_type": "table",

            "table_index": None,

            "rows": [],

            "row_count": 0,

            "column_count": 0,

            "extraction_status": "failed",

            "error": str(e)
        })

    return extracted_tables