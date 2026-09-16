from typing import List,Dict

from backend.app.services.pdf_extractor import extract_pdf
from backend.app.services.document_parser import build_page_content
from backend.app.services.chunker import build_chunks
from backend.app.services.embedder import embedding_service
from backend.app.services.qdrant_manager import QdrantManager

class DocumentIndexingService:
    """
    Handles the complete document indexing pipeline.

    PDF
        ↓
    PDF extraction
        ↓
    Text cleaning + table normalization
        ↓
    RAG chunking
        ↓
    BGE-M3 embeddings
        ↓
    Qdrant storage
    """

    def __init__(self):

        #Qdrant service
        self.qdrant = QdrantManager()

        #Make sure collection and required indexes exist
        self.qdrant.create_collection()
        self.qdrant.create_payload_indexes()

    def parse_document(self,file_path:str) ->List[Dict]:
        """
        Extract and parse a PDF into structured pages.
        """
        #extract raw PDF
        extracted_document = extract_pdf(file_path)

        parsed_pages = []

        #clean and normalize each page
        for page_data in extracted_document["pages"]:
            parsed_page = build_page_content(page_data)

            parsed_pages.append(parsed_page)

        return parsed_pages

    def index_document(self,
                       file_path:str,
                       case_id: int,
                       document_id:int,
                       document_type:str)->Dict:
        """
        Complete document indexing pipeline.
        """

        # ---------------------------------
        # 1. PDF extraction + parsing
        # ---------------------------------

        parsed_pages = self.parse_document(
            file_path
        )

        # ---------------------------------
        # 2. Create RAG chunks
        # ---------------------------------

        chunks = build_chunks(
            parsed_pages=parsed_pages,
            case_id=case_id,
            document_id=document_id,
            document_type=document_type
        )

        if not chunks:
            raise ValueError(
                "No usable chunks were generated from the document."
            )

        # ---------------------------------
        # 3. Generate BGE-M3 embeddings
        # ---------------------------------

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = embedding_service.embed_texts(
            texts
        )

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Number of embeddings does not match number of chunks."
            )

        # ---------------------------------
        # 4. Store vectors in Qdrant
        # ---------------------------------

        self.qdrant.upsert_chunks(
            embeddings=embeddings,
            chunks=chunks
        )

        # ---------------------------------
        # 5. Return indexing information
        # ---------------------------------

        return {
            "pages_processed": len(parsed_pages),
            "chunks_created": len(chunks),
            "embeddings_created": len(embeddings),
            "embedding_dimension": len(embeddings[0]),
            "status": "indexed"
        }