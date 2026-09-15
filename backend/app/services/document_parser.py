from backend.app.services.text_cleaner import clean_text
from backend.app.services.table_normalizer import normalize_table


def build_page_content(page_data: dict) -> dict:
    """
    Convert raw page extraction output into
    a unified page representation.
    """

    # Clean extracted text
    text = clean_text(
        page_data.get("text", "")
    )

    # Normalize tables
    normalized_tables = []

    for table in page_data.get(
        "tables",
        []
    ):

        normalized_table = normalize_table(
            table
        )

        normalized_tables.append(
            normalized_table
        )

    return {
        "page_number": page_data[
            "page_number"
        ],

        "content_type": page_data[
            "content_type"
        ],

        "content_types": page_data.get(
            "content_types",
            []
        ),

        "text": text,

        "has_text": page_data.get(
            "has_text",
            False
        ),

        "has_table": page_data.get(
            "has_table",
            False
        ),

        "has_image": page_data.get(
            "has_image",
            False
        ),

        "tables": normalized_tables
    }