from backend.app.services.embedder import EmbeddingService
from backend.app.services.qdrant_manager import QdrantManager


# Question from the user
query = "What was the company's revenue growth in 2025?"


# 1. Create embedding for the question
embedder = EmbeddingService()

query_embedding = embedder.embed_texts(
    [query]
)[0]


# 2. Search Qdrant
qdrant = QdrantManager()

results = qdrant.search_chunks(
    query_embedding=query_embedding,
    limit=5,
    case_id=1
)


# 3. Display retrieved chunks
print("\nRetrieved chunks:\n")

for i, result in enumerate(results, start=1):

    print(f"Result {i}")
    print(f"Score: {result.score}")
    print(f"Page: {result.payload.get('page_number')}")
    print(f"Document type: {result.payload.get('document_type')}")
    print(f"Text: {result.payload.get('text')}")
    print("-" * 80)