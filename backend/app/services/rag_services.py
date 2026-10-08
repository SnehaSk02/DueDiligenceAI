from typing import List, Dict
from backend.app.services.cloudflare_embedder import (
    cloudflare_embedding_service as embedding_service
)
# from backend.app.services.embedder import embedding_service
from backend.app.services.qdrant_manager import QdrantManager
from backend.app.services.llm_gateway import gateway
# from backend.app.services.reranker import reranker
from backend.app.services.cloudflare_reranker import (
    cloudflare_reranker as reranker
)
from backend.app.services.guardrails.retrieval_guardrails import(
    validate_retrieval_query,
    validate_case_id,
    validate_retrieval_parameters,
    filter_retrieved_results,
    validate_retrieval_quality
)
from backend.app.services.token_budget import token_budget_manager
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
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve the most relevant document chunks
        for a question within a specific due diligence case.
        """
        question = validate_retrieval_query(question)

        case_id = validate_case_id(case_id)

        retrieval_k =10
        rerank_k = top_k

        validate_retrieval_parameters(retrieval_k=retrieval_k,rerank_k=rerank_k)

        # 1. Embed the user's question
        query_embedding = embedding_service.embed_texts([question])[0]

        # 2. Search Qdrant
        results = self.qdrant.search_chunks(
            query_embedding=query_embedding,
            limit=retrieval_k,
            case_id=case_id
        )

        # 3. Convert Qdrant results into dictionaries
        retrieved_chunks = []

        for result in results:
            payload = result.payload or {}

            retrieved_chunks.append({
                "score": result.score,
                "case_id": payload.get("case_id"),
                "document_id": payload.get("document_id"),
                "document_type": payload.get("document_type"),
                "page_number": payload.get("page_number"),
                "content_type": payload.get("content_type"),
                "chunk_index": payload.get("chunk_index"),
                "text": payload.get("text")
            })
        retrieved_chunks = filter_retrieved_results(
        results=retrieved_chunks,
        case_id=case_id,
        limit=retrieval_k
    )
        retrieved_chunks = reranker.rerank(question=question,
                                           documents=retrieved_chunks,
                                           top_k=rerank_k)
        quality = validate_retrieval_quality(results=retrieved_chunks)

        if not quality["sufficient"]:
            return []
        return retrieved_chunks

    def build_context(
        self,
        retrieved_chunks: List[Dict]
    ) -> str:
        """
        Convert retrieved chunks into structured context
        for the LLM.
        """

        prepared_chunks = token_budget_manager.prepare_chunks(retrieved_chunks)
        return token_budget_manager.build_context(prepared_chunks)
    

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
    
            # Generate answer through the LLM gateway
            response = gateway.generate(
                prompt=f"""
            Answer the question using only the provided context.

            Question:
            {question}

            Context:
            {context}
            """,
                temperature=0
            )

            answer = response["content"]
    
            #prepare source information
            sources = []
            for chunk in retrieved_chunks:
                sources.append({
                    "document_id": chunk["document_id"],
                    "document_type": chunk['document_type'],
                    "page_number": chunk['page_number'],
                    "content_type": chunk['content_type'],
                    "score": chunk["score"],
                    "rerank_score": chunk.get("rerank_score"),
                    "text": chunk.get("text", "")
                })
            return{
                "answer": answer,
                "sources":sources,
                "llm_metadata": {
                        "provider": response.get("provider"),
                        "model": response.get("model"),
                        "usage": response.get("usage"),
                        "latency_seconds": response.get("latency_seconds"),
                        "attempts": response.get("attempts")
}
            }
    
            