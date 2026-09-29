import os
import re
from pathlib import Path
from typing import Dict, Any


# ============================================================
# CONFIGURATION
# ============================================================

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

MAX_FILENAME_LENGTH = 255

ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf"
}


# ============================================================
# 1. FILENAME VALIDATION
# ============================================================

def validate_filename(
    filename: str
) -> str:
    """
    Validate an uploaded filename.

    Prevents path traversal such as:
        ../../secret.txt
    """

    if not filename:
        raise ValueError(
            "Filename is required."
        )

    filename = Path(filename).name

    if not filename:
        raise ValueError(
            "Invalid filename."
        )

    if len(filename) > MAX_FILENAME_LENGTH:
        raise ValueError(
            "Filename is too long."
        )

    # Reject suspicious path traversal patterns
    if ".." in filename:
        raise ValueError(
            "Invalid filename."
        )

    return filename


# ============================================================
# 2. FILE EXTENSION VALIDATION
# ============================================================

def validate_file_extension(
    filename: str
) -> str:

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    return extension


# ============================================================
# 3. FILE SIZE VALIDATION
# ============================================================

def validate_file_size(
    file_size: int
) -> int:

    if file_size is None:
        raise ValueError(
            "File size is required."
        )

    if file_size <= 0:
        raise ValueError(
            "File cannot be empty."
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File exceeds the maximum allowed size "
            f"of {MAX_FILE_SIZE_MB} MB."
        )

    return file_size


# ============================================================
# 4. SAFE UPLOAD PATH
# ============================================================

def build_safe_upload_path(
    upload_directory: str,
    filename: str
) -> Path:
    """
    Create a safe path inside the upload directory.
    """

    filename = validate_filename(
        filename
    )

    upload_dir = Path(
        upload_directory
    ).resolve()

    upload_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    target_path = (
        upload_dir / filename
    ).resolve()

    # Make sure target remains inside upload directory
    try:
        target_path.relative_to(
            upload_dir
        )

    except ValueError:
        raise ValueError(
            "Invalid upload path."
        )

    return target_path


# ============================================================
# 5. PDF SIGNATURE VALIDATION
# ============================================================

def validate_pdf_signature(
    file_path: str
) -> bool:
    """
    Check the PDF magic bytes.

    A PDF normally starts with:
        %PDF-
    """

    path = Path(file_path)

    if not path.exists():
        raise ValueError(
            "Uploaded file does not exist."
        )

    with path.open("rb") as file:

        signature = file.read(5)

    if signature != b"%PDF-":
        raise ValueError(
            "File does not contain a valid PDF signature."
        )

    return True


# ============================================================
# 6. CASE ACCESS VALIDATION
# ============================================================

def validate_case_access(
    requested_case_id: int,
    authenticated_case_id: int
) -> bool:
    """
    Basic authorization boundary.

    In the current single-user application,
    these may be the same value.

    In a multi-user production system,
    authenticated_case_id should come from
    the authenticated user's authorization context.
    """

    if requested_case_id is None:
        raise ValueError(
            "Case ID is required."
        )

    if authenticated_case_id is None:
        raise PermissionError(
            "Authenticated case context is required."
        )

    if int(requested_case_id) != int(
        authenticated_case_id
    ):
        raise PermissionError(
            "You are not authorized to access this case."
        )

    return True


# ============================================================
# 7. API KEY VALIDATION
# ============================================================

def validate_required_environment_variables():
    """
    Make sure critical secrets/configuration exist.
    """

    required_variables = [
        "GROQ_API_KEY",
        "QDRANT_URL",
        "QDRANT_API_KEY"
    ]

    missing_variables = []

    for variable in required_variables:

        value = os.getenv(variable)

        if not value:
            missing_variables.append(
                variable
            )

    if missing_variables:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing_variables)
        )

    return True


# ============================================================
# 8. USER QUERY LENGTH
# ============================================================

def validate_user_input(
    question: str,
    max_length: int = 2000
) -> str:

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )

    question = question.strip()

    if not question:
        raise ValueError(
            "Question cannot be empty."
        )

    if len(question) > max_length:
        raise ValueError(
            f"Question cannot exceed "
            f"{max_length} characters."
        )

    return question