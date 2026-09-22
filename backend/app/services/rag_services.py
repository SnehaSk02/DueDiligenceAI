from typing import List, Dict

from backend.app.services.embedder import embedding_service
from backend.app.services.qdrant_manager import QdrantManager
from backend.app.services.llm_service import LLMService
from backend.app.services.reranker import reranker
class RAGService:
    """
    Handles query embedding and retrieval of relevant
    document chunks from Qdrant.
    """

    def __init__(self):
        self.qdrant = QdrantManager()

    def retrieve(
        self,
        question: str,
        case_id: int,
        top_k: int = 5,
        rerank: bool = False,
        retrieval_k: int = 10
    ) -> List[Dict]:
        """
        Retrieve the most relevant document chunks
        for a question within a specific due diligence case.
        """

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        # 1. Embed the user's question
        query_embedding = embedding_service.embed_texts(
            [question]
        )[0]

        # 2. Search Qdrant
        results = self.qdrant.search_chunks(
            query_embedding=query_embedding,
            limit=top_k,
            case_id=case_id
        )

        # 3. Convert Qdrant results into dictionaries
        retrieved_chunks = []

        for result in results:
            payload = result.payload or {}

            retrieved_chunks.append({
                "score": result.score,
                "document_id": payload.get("document_id"),
                "document_type": payload.get("document_type"),
                "page_number": payload.get("page_number"),
                "content_type": payload.get("content_type"),
                "chunk_index": payload.get("chunk_index"),
                "text": payload.get("text")
            })
        retrieved_chunks = reranker.rerank(question=question,
                                           documents=retrieved_chunks,
                                           top_k=top_k)

        return retrieved_chunks

    def build_context(
        self,
        retrieved_chunks: List[Dict]
    ) -> str:
        """
        Convert retrieved chunks into structured context
        for the LLM.
        """

        context_parts = []

        for i, chunk in enumerate(retrieved_chunks, start=1):

            context_parts.append(
                f"""
SOURCE {i}
Document: {chunk["document_type"]}
Page: {chunk["page_number"]}
Content type: {chunk["content_type"]}

{chunk["text"]}
"""
            )

        return "\n".join(context_parts)
    def answer_question(
                self,
                question: str,
                case_id: int,
                top_k:int =5
        )->Dict:
            #retrieve relevant chunks
            retrieved_chunks = self.retrieve(question=question,
                                             case_id=case_id,
                                             top_k=top_k)
    
            if not retrieved_chunks:
                return{
                    "answer":"The information is not available in the provided documents.",
                    "sources" : []
                }
            #build context for the LLM
            context = self.build_context(retrieved_chunks)
    
            #generate answer using  groq
            llm = LLMService()
            answer = llm.generate_answer(question=question,context=context)
    
            #prepare source information
            sources = []
            for chunk in retrieved_chunks:
                sources.append({
                    "document_id": chunk["document_id"],
                    "document_type": chunk['document_type'],
                    "page_number": chunk['page_number'],
                    "content_type": chunk['content_type'],
                    "score": chunk["score"]
                })
            return{
                "answer": answer,
                "sources":sources
            }
    
            