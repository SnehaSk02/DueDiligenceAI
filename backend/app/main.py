from fastapi import FastAPI, Depends, UploadFile, File,HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.case import DueDiligenceCase
from backend.app.models.documents import Document
from backend.app.schemas import DueDiligenceRequest

import os
import shutil


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

@app.post("/api/v1/due-diligence/{case_id}/documents")
def upload_document(case_id : int,
                    document_type: str, 
                    file:UploadFile = File(...),
                    db: Session = Depends(get_db)):
    #to check file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    #to create case- specific upload directory
    upload_dir = f"uploads/cases/{case_id}"
    os.makedirs(upload_dir, exist_ok= True)

    #File path
    file_path=os.path.join(upload_dir, file.filename)

    #save uploaded file
    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)

    #for database record in document
    document =  Document(case_id=case_id,
                         filename=file.filename,
                         document_type=document_type,
                         file_path=file_path,
                         status='uploaded')

    db.add(document)
    db.commit()
    db.refresh(document)

    return{
        "message":"Document uploaded successfully",
        "document_id":document.id,
        "case_id":case_id,
        "filename":file.filename,
        "file_path":file_path,
        "document_type":document.document_type,
        "status": document.status
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