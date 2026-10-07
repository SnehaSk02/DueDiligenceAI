import os

from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET = os.getenv(
    "SUPABASE_BUCKET",
    "due-diligence-documents"
)


if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is not configured.")

if not SUPABASE_SERVICE_KEY:
    raise ValueError(
        "SUPABASE_SERVICE_KEY is not configured."
    )


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)


def upload_pdf(
    file_path: str,
    storage_path: str
) -> str:

    with open(file_path, "rb") as file:
        file_data = file.read()

    supabase.storage.from_(
        SUPABASE_BUCKET
    ).upload(
        storage_path,
        file_data,
        {
            "content-type": "application/pdf",
            "upsert": False
        }
    )

    return storage_path


def download_pdf(
    storage_path: str,
    destination_path: str
) -> str:

    file_data = (
        supabase.storage
        .from_(SUPABASE_BUCKET)
        .download(storage_path)
    )

    with open(destination_path, "wb") as file:
        file.write(file_data)

    return destination_path


def delete_pdf(storage_path: str) -> None:

    supabase.storage.from_(
        SUPABASE_BUCKET
    ).remove([storage_path])