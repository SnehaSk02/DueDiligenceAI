from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf"}

MAX_FILE_SIZE = 50*1024*1024 # 50MB

def validate_pdf(file_path:str) -> None:
    "Validate PDF before Processing"
    path = Path(file_path)

    #check whether file exists
    if not path.exists():
        raise ValueError("File does not exist.")

    #check file extension
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Only PDF files are supported.")

    #check file size
    if path.stat().st_size == 0:
        raise ValueError("PDF file is empty.")

    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("PDF file exceeds the 50MB size limit.")