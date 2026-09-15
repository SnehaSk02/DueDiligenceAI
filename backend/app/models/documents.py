from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base

class Document(Base):
    __tablename__="documents"

    id : Mapped[int] = mapped_column(primary_key=True,autoincrement=True)

    case_id : Mapped[int] = mapped_column(ForeignKey("due_diligence_cases.id"), nullable=False)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    document_type: Mapped[str] = mapped_column(String(50), nullable=False)

    file_path : Mapped[str] = mapped_column(String(500), nullable=False)

    status : Mapped[str] = mapped_column(String(50), nullable=False,default="uploaded")

    created_at : Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    updated_at : Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate = datetime.utcnow)
    
    case = relationship("DueDiligenceCase", back_populates="documents")