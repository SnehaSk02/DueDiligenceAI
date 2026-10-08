import os
import requests
from typing import List, Dict


class CloudflareReranker:
    def __init__(self):
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")

        if not account_id or not api_token:
            raise ValueError("Cloudflare AI credentials are missing.")

        self.api_token = api_token
        self.url = (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{account_id}/ai/run/@cf/baai/bge-reranker-base"
        )

    def rerank(
        self,
        question: str,
        documents: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if not documents:
            return []

        contexts = [
            {"text": document.get("text") or ""}
            for document in documents
        ]

        response = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            json={
                "query": question,
                "contexts": contexts,
            },
            timeout=60,
        )

        response.raise_for_status()

        scores = response.json()["result"]["response"]

        reranked_documents = []

        for item in scores:
            index = int(item["id"])

            if index < 0 or index >= len(documents):
                raise ValueError("Invalid reranker document index.")

            updated_document = documents[index].copy()
            updated_document["rerank_score"] = float(item["score"])

            reranked_documents.append(updated_document)

        reranked_documents.sort(
            key=lambda item: item["rerank_score"],
            reverse=True,
        )

        return reranked_documents[:top_k]


cloudflare_reranker = CloudflareReranker()