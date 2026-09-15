from backend.app.database.connection import engine
from backend.app.database.base import Base
#import model so that SQLAlchemy also knows
from backend.app.models.case import DueDiligenceCase
from backend.app.models.documents import Document
Base.metadata.create_all(bind=engine)
print("Table created successfully!")