# from backend.app.services.rag_services import RAGService

# rag = RAGService()

# question = "What are Microsoft's main products and services?"

# result = rag.answer_question(
#     question=question,
#     case_id=13,
#     top_k=5
# )

# print("\nANSWER:")
# print(result["answer"])

# print("\nSOURCES:")

# for source in result["sources"]:
#     print(
#         f"Document: {source['document_type']} | "
#         f"Page: {source['page_number']} | "
#         f"Score: {source['score']}"
#     )

# from backend.app.services.rag_services import RAGService

# rag_service = RAGService()

# question = "What are Microsoft's main products and services?"

# results = rag_service.retrieve(
#     question=question,
#     case_id=13,
#     top_k=5
# )

# print("\nReranked Results:\n")

# for result in results:
#     print(
#         f"page={result['page_number']} | "
#         f"chunk={result['chunk_index']} | "
#         f"qdrant_score={result['score']:.4f} | "
#         f"rerank_score={result['rerank_score']:.4f}"
#     )

from backend.app.services.rag_services import RAGService
from backend.app.services.llm_service import LLMService


rag_service = RAGService()
llm_service = LLMService()

question = "What happened to Microsoft's revenue in 2025?"
case_id = 13

# Retrieve reranked evidence
results = rag_service.retrieve(
    question=question,
    case_id=case_id,
    top_k=5
)

print("\nRetrieved Evidence:\n")

for result in results:
    print(
        f"Page: {result['page_number']} | "
        f"Chunk: {result['chunk_index']} | "
        f"Qdrant: {result['score']:.4f} | "
        f"Rerank: {result['rerank_score']:.4f}"
    )

# Build context for LLM
context = "\n\n".join(
    [
        f"Page {result['page_number']}:\n{result['text']}"
        for result in results
    ]
)

prompt = f"""
Answer the question using only the provided evidence.

Question:
{question}

Evidence:
{context}

If the evidence does not contain enough information to answer,
say that the information is not available in the provided documents.
"""

answer = llm_service.generate_judge_response(prompt)

print("\nAnswer:\n")
print(answer)