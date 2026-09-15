from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped,mapped_column,relationship

from backend.app.database.base import Base

class DueDiligenceCase(Base):
    __tablename__ = "due_diligence_cases"

    id:Mapped[int] = mapped_column(primary_key=True,autoincrement=True)

    company_name:Mapped[str] =mapped_column(String(200), nullable= False)

    case_type : Mapped[str] = mapped_column(String(50),nullable=False)

    status: Mapped[str] = mapped_column(String(50),nullable=False,default="pending")

    created_at : Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

    updated_at : Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow,onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="case")
