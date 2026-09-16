from backend.app.services.qdrant_manager import QdrantManager


qdrant = QdrantManager()

qdrant.create_collection()
qdrant.create_payload_indexes()