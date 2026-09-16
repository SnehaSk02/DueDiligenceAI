from backend.app.services.rag_services import RAGService

rag = RAGService()

question = "What happened to the company's revenue in 2025?"

result = rag.answer_question(
    question=question,
    case_id=1,
    top_k=5
)

print("\nANSWER:")
print(result["answer"])

print("\nSOURCES:")

for source in result["sources"]:
    print(
        f"Document: {source['document_type']} | "
        f"Page: {source['page_number']} | "
        f"Score: {source['score']}"
    )