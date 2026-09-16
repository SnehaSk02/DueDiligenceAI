from backend.app.services.embedder import EmbeddingService
from backend.app.services.qdrant_manager import QdrantManager


# Sample chunk
chunks = [
    {
        "case_id": 1,
        "document_id": 1,
        "document_type": "Annual Report",
        "page_number": 10,
        "content_type": "text",
        "chunk_index": 0,
        "text": (
            "The company reported strong revenue growth in 2025, "
            "with total revenue increasing by 18% compared with the "
            "previous financial year."
        )
    }
]


# 1. Generate embeddings
embedder = EmbeddingService()

texts = [
    chunk["text"]
    for chunk in chunks
]

embeddings = embedder.embed_texts(texts)

print("Number of embeddings:", len(embeddings))
print("Embedding dimension:", len(embeddings[0]))


# 2. Connect to Qdrant
qdrant = QdrantManager()

# Make sure collection exists
qdrant.create_collection()


# 3. Store embeddings + metadata
qdrant.upsert_chunks(
    embeddings=embeddings,
    chunks=chunks
)

print("Vector pipeline test completed successfully.")