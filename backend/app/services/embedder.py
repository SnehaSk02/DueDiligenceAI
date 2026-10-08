from typing import List
# from sentence_transformers import SentenceTransformer
import os
import requests
from typing import List
from dotenv import load_dotenv

# class EmbeddingService:
#     def __init__(self,model_name : str = "BAAI/bge-m3"):
#         self.model_name= model_name
#         self.model = SentenceTransformer(model_name)

#     def embed_texts(self, texts: List[str]) -> List[List[float]]:
#         """
#         Generate embeddings for multiple text chunks.
#         """

#         if not texts:
#             return []

#         embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

#         return embeddings.tolist()

# #shared embedding service
# embedding_service = EmbeddingService()

class EmbeddingService:
    def __init__(self):
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")

        if not self.account_id or not self.api_token:
            raise ValueError("Cloudflare AI credentials are missing.")

        self.url = (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{self.account_id}/ai/run/@cf/baai/bge-m3"
        )

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        response = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            },
            json={"text": texts},
            timeout=60
        )

        response.raise_for_status()

        embeddings = response.json()["result"]["data"]

        if any(len(vector) != 1024 for vector in embeddings):
            raise ValueError("Unexpected embedding dimension.")

        return embeddings


embedding_service = EmbeddingService()