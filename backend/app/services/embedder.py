from typing import List
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self,model_name : str = "BAAI/bge-m3"):
        self.model_name= model_name
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple text chunks.
        """

        if not texts:
            return []

        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

        return embeddings.tolist()

#shared embedding service
embedding_service = EmbeddingService()