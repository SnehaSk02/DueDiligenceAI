def clean_cell(cell):
    """
    Clean an individual table cell.
    """

    if cell is None:
        return ""

    return str(cell).strip()


def normalize_table(table: dict) -> dict:
    """
    Normalize an extracted table while preserving
    its row and column relationships.
    """

    rows = table.get("rows", [])

    if not rows:
        return {
            "content_type": "table",
            "table_index": table.get("table_index"),
            "headers": [],
            "rows": [],
            "row_count": 0,
            "column_count": 0,
            "extraction_status": table.get(
                "extraction_status",
                "failed"
            )
        }

    # Clean every cell
    cleaned_rows = []

    for row in rows:

        cleaned_row = [
            clean_cell(cell)
            for cell in row
        ]

        cleaned_rows.append(cleaned_row)

    # First row is retained as the header candidate.
    # We do not discard any rows.
    header_candidate = cleaned_rows[0]

    data_rows = cleaned_rows[1:]

    column_count = max(
        (
            len(row)
            for row in cleaned_rows
        ),
        default=0
    )

    return {
        "content_type": "table",

        "table_index": table.get(
            "table_index"
        ),

        "headers": header_candidate,

        "rows": data_rows,

        "row_count": len(data_rows),

        "column_count": column_count,

        "extraction_status": table.get(
            "extraction_status",
            "success"
        )
    }