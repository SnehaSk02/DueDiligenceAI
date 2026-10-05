from fastapi import FastAPI, Depends, UploadFile, File,HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.case import DueDiligenceCase
from backend.app.models.documents import Document
from backend.app.schemas import DueDiligenceRequest
from backend.app.services.guardrails.security_guardrails import (
    validate_filename,
    validate_file_extension,
    validate_file_size,
    build_safe_upload_path,
    validate_pdf_signature,
    validate_case_access,
    validate_user_input,
    validate_required_environment_variables
)
import os
import shutil

validate_required_environment_variables()
app= FastAPI(
    title="DueDiligenceAI API",
    description="Backend API for AI-powered company and investments due diligence",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return{
        "status":"healthy",
        "service":"DueDiligence AI API"
    }

@app.post("/api/v1/due-diligence")
def start_due_diligence(request: DueDiligenceRequest,
                        db: Session = Depends(get_db)):

    case = DueDiligenceCase(
        company_name = request.company,
        case_type = request.due_diligence_type
    )

    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "message": "Due diligence case created",
        "case_id": case.id,
        "company": case.company_name,
        "due_diligence_type": case.case_type,
        "status": case.status,
        "created_time" :case.created_at,
        "updated_time":case.updated_at
    }

# @app.post("/api/v1/due-diligence/{case_id}/documents")
# def upload_document(
#     case_id: int,
#     document_type: str,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     print(
#         f"UPLOAD ENDPOINT REACHED | case_id={case_id} | filename={file.filename}",
#         flush=True
#     )
#     # ======================================================
#     # 1. SECURITY VALIDATION + FILE SAVING
#     # ======================================================
#     from backend.app.services.indexing_service import DocumentIndexingService

#     try:
#         validate_case_access(requested_case_id=case_id,
#                              authenticated_case_id=case_id)

#         # Validate filename
#         filename = validate_filename(file.filename)

#         existing_document = db.query(Document).filter(
#             Document.case_id == case_id,
#             Document.filename == filename
#         ).first()

#         if existing_document:
#             raise HTTPException(
#                 status_code=409,
#                 detail=f"The file '{filename}' has already been uploaded for this case. "
#             "Please check the file and try again."
#             )

#         # Validate extension
#         validate_file_extension(filename)

#         # Validate file size
#         file.file.seek(0, os.SEEK_END)
#         file_size = file.file.tell()
#         file.file.seek(0)

#         validate_file_size(file_size)

#         # Create case-specific directory
#         upload_dir = os.path.join(
#             "uploads",
#             "cases",
#             str(case_id)
#         )

#         os.makedirs(
#             upload_dir,
#             exist_ok=True
#         )

#         # Build safe path
#         file_path = build_safe_upload_path(
#             upload_dir,
#             filename
#         )

#         # Save file
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(
#                 file.file,
#                 buffer
#             )

#         # Validate actual PDF signature
#         validate_pdf_signature(
#             str(file_path)
#         )

#         # Create database record
#         document = Document(
#             case_id=case_id,
#             filename=filename,
#             document_type=document_type,
#             file_path=str(file_path),
#             status="uploaded"
#         )

#         db.add(document)
#         db.commit()
#         db.refresh(document)
#     except HTTPException:
#         raise

#     except ValueError as exc:

#         # Security validation failure
#         raise HTTPException(
#             status_code=400,
#             detail=str(exc)
#         )

#     except Exception:

#         # Remove partially saved file
#         if (
#             "file_path" in locals()
#             and os.path.exists(file_path)
#         ):
#             os.remove(file_path)

#         db.rollback()

#         raise HTTPException(
#             status_code=500,
#             detail="Document upload failed."
#         )

#     # ======================================================
#     # 2. DOCUMENT INDEXING
#     # ======================================================

#     try:

#         indexing_service = DocumentIndexingService()

#         indexing_result = indexing_service.index_document(
#             file_path=str(file_path),
#             case_id=case_id,
#             document_id=document.id,
#             document_type=document_type
#         )

#         # Indexing successful
#         document.status = "indexed"

#         db.commit()
#         db.refresh(document)

#     except Exception as exc:

#         # File was uploaded and DB record exists,
#         # but indexing failed.
#         document.status = "indexing_failed"

#         db.commit()

#         raise HTTPException(
#             status_code=500,
#             detail=f"Document indexing failed:{exc}"
#         )

#     # ======================================================
#     # 3. RESPONSE
#     # ======================================================

#     return {
#         "message": "Document uploaded and indexed successfully",
#         "document_id": document.id,
#         "case_id": document.case_id,
#         "filename": document.filename,
#         "document_type": document.document_type,
#         "status": document.status,
#         "indexing": indexing_result
#     }
@app.post("/api/v1/due-diligence/{case_id}/documents")
async def upload_document(
    case_id: int,
    document_type: str,
    file: UploadFile = File(...)
):
    print(
        f"UPLOAD REACHED | case={case_id} | "
        f"filename={file.filename} | type={document_type}",
        flush=True
    )

    content = await file.read()

    print(
        f"FILE RECEIVED | size={len(content)} bytes",
        flush=True
    )

    return {
        "message": "Render received the file",
        "case_id": case_id,
        "filename": file.filename,
        "document_type": document_type,
        "file_size": len(content)
    }
@app.get("/api/v1/due-diligence/{case_id}/documents")
def get_documents(
    case_id: int,
    db: Session = Depends(get_db)
):
    documents = (
        db.query(Document)
        .filter(Document.case_id == case_id)
        .all()
    )

    return [
        {
            "document_id": document.id,
            "filename": document.filename,
            "document_type": document.document_type,
            "status": document.status,
            "file_path": document.file_path,
        }
        for document in documents
    ]

@app.post("/api/v1/due-diligence/{case_id}/ask")
def ask_question(
    case_id:int,
    question: str,
    db:Session = Depends(get_db)
):
    from backend.app.services.rag_services import RAGService

    rag_service = RAGService()

    try:

        question = validate_user_input(question)
        result = rag_service.answer_question(
            question=question,
            case_id=case_id,
            top_k=5
        )
        print("\n========== DEBUG FOLLOW-UP SOURCES ==========")
        print(result["sources"])
        print("=============================================\n")

        return {
            "case_id":case_id,
            "question":question,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Question answering failed:{str(e)}"
        )

@app.post("/api/v1/due-diligence/{case_id}/generate-report")
def generate_report(
    case_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a structured due diligence report.
    """
    # --------------------------------------------------
    # 2. Check that the case exists
    # --------------------------------------------------
    from backend.app.agents.graph import due_diligence_graph

    case = (
        db.query(DueDiligenceCase)
        .filter(DueDiligenceCase.id == case_id)
        .first()
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Due diligence case not found."
        )

    # --------------------------------------------------
    # 3. Check that documents exist
    # --------------------------------------------------

    documents = (
        db.query(Document)
        .filter(Document.case_id == case_id)
        .all()
    )

    if not documents:
        raise HTTPException(
            status_code=400,
            detail=(
                "No documents are available for this case. "
                "Upload and index documents before generating a report."
            )
        )

    # --------------------------------------------------
    # 4. Check document indexing status
    # --------------------------------------------------

    failed_documents = [
        document.filename
        for document in documents
        if document.status != "indexed"
    ]

    if failed_documents:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Some documents are not successfully indexed.",
                "documents": failed_documents
            }
        )

    # --------------------------------------------------
    # 5. Build LangGraph initial state
    # --------------------------------------------------

    initial_state = {
        "case_id": case_id,
        "question": "Generate a due diligence report.",
        "due_diligence_type": case.case_type,
        "report_type": "full",
        "agent_answers": [],
        "llm_metrics": []
    }

    # --------------------------------------------------
    # 6. Run report workflow
    # --------------------------------------------------

    try:

        result = due_diligence_graph.invoke(
            initial_state
        )

    except Exception as e:

        print("\nREPORT GENERATION FAILED")
        print("Reason:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )

    # --------------------------------------------------
    # 7. Return report
    # --------------------------------------------------

    report = result.get("report")

    if not report:
        raise HTTPException(
            status_code=500,
            detail="Report generation completed without a report."
        )

    return {
        "message": "Due diligence report generated successfully.",
        "case_id": case_id,
        "company": case.company_name,
        "report_type": "full",
        "report": report,
        "sources": result.get("sources", []),
        "retrieved_evidence": result.get(
            "retrieved_evidence",
            []
        ),
        "synthesis_llm_metrics": result.get(
            "synthesis_llm_metrics",
            {}
        )
    }

@app.get("/api/v1/due-diligence")
def get_due_diligence_cases( db: Session = Depends(get_db) ):
    cases = ( db.query(DueDiligenceCase) .order_by(DueDiligenceCase.created_at.desc()) .all() )
    return [ { "case_id": case.id,
               "company": case.company_name,
                "due_diligence_type": case.case_type,
                "status": case.status,
                "created_time": case.created_at,
                "updated_time": case.updated_at, } 
                for case in cases ]