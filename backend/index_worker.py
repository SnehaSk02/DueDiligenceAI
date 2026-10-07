import os
import tempfile
import time
from backend.app.database.session import SessionLocal
from backend.app.models import DueDiligenceCase, Document
from backend.app.services.indexing_service import DocumentIndexingService
from backend.app.services.storage_services import download_pdf

def get_next_uploaded_document(db):
    return (
        db.query(Document)
        .filter(
            Document.status == "uploaded",
            Document.storage_path.isnot(None)
        )
        .order_by(Document.id.asc())
        .first()
    )
def index_document(document_id: int):
    db = SessionLocal()

    temp_file_path = None

    try:
        # -----------------------------------------
        # 1. Get document
        # -----------------------------------------
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        if not document:
            raise ValueError(
                f"Document {document_id} not found."
            )

        # -----------------------------------------
        # 2. Validate storage path
        # -----------------------------------------
        if not document.storage_path:
            raise ValueError(
                f"Document {document_id} has no storage path."
            )

        # -----------------------------------------
        # 3. Mark as indexing
        # -----------------------------------------
        document.status = "indexing"
        db.commit()

        # -----------------------------------------
        # 4. Create temporary PDF path
        # -----------------------------------------
        temp_dir = tempfile.mkdtemp(
            prefix="due_diligence_"
        )

        temp_file_path = os.path.join(
            temp_dir,
            document.filename
        )

        # -----------------------------------------
        # 5. Download from Supabase
        # -----------------------------------------
        print(
            f"Downloading document {document.id} "
            f"from Supabase..."
        )

        download_pdf(
            storage_path=document.storage_path,
            destination_path=temp_file_path
        )

        print(
            f"PDF downloaded to: {temp_file_path}"
        )

        # -----------------------------------------
        # 6. Run indexing pipeline
        # -----------------------------------------
        print(
            f"Starting indexing for document "
            f"{document.id}..."
        )

        indexing_service = DocumentIndexingService()

        result = indexing_service.index_document(
            file_path=temp_file_path,
            case_id=document.case_id,
            document_id=document.id,
            document_type=document.document_type
        )

        # -----------------------------------------
        # 7. Update status
        # -----------------------------------------
        document.status = "indexed"
        db.commit()

        print()
        print("=" * 60)
        print("INDEXING SUCCESSFUL")
        print("=" * 60)
        print(result)

        return result

    except Exception as exc:

        db.rollback()

        # Try to update document status
        try:
            document = (
                db.query(Document)
                .filter(Document.id == document_id)
                .first()
            )

            if document:
                document.status = "indexing_failed"
                db.commit()

        except Exception:
            db.rollback()

        print()
        print("=" * 60)
        print("INDEXING FAILED")
        print("=" * 60)
        print(str(exc))

        raise

    finally:

        # -----------------------------------------
        # 8. Delete temporary PDF
        # -----------------------------------------
        if temp_file_path and os.path.exists(
            temp_file_path
        ):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass

        # Remove temporary directory
        if temp_file_path:
            temp_dir = os.path.dirname(
                temp_file_path
            )

            if os.path.isdir(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except Exception:
                    pass

        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("DUE DILIGENCE INDEX WORKER STARTED")
    print("=" * 60)

    while True:
        db = SessionLocal()

        try:
            document = get_next_uploaded_document(db)

            if not document:
                print("No uploaded documents waiting. Checking again in 10 seconds...")
            else:
                print(
                    f"Found document {document.id}: "
                    f"{document.filename}"
                )

                index_document(document.id)

        except Exception as exc:
            print("=" * 60)
            print("WORKER ERROR")
            print("=" * 60)
            print(str(exc))

        finally:
            db.close()

        time.sleep(10)