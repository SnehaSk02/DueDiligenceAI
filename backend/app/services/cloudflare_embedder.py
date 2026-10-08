import os
import requests
from typing import List


class CloudflareEmbeddingService:
    def __init__(self):
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")

        if not account_id or not api_token:
            raise ValueError("Cloudflare AI credentials are missing.")

        self.api_token = api_token
        self.url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{account_id}/ai/run/@cf/baai/bge-m3"
        )

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        response = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            json={"text": texts},
            timeout=60,
        )

        response.raise_for_status()

        embeddings = response.json()["result"]["data"]

        if len(embeddings) != len(texts):
            raise ValueError("Unexpected number of embeddings.")

        if any(len(vector) != 1024 for vector in embeddings):
            raise ValueError("Unexpected embedding dimension.")

        return embeddings


cloudflare_embedding_service = CloudflareEmbeddingService()