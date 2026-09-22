from typing import List, Dict
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, 
                 model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        print(f"Loading reranker model:{self.model_name}")

        self.model = CrossEncoder(self.model_name)
        print("Reranker model loaded successfully.")

    def rerank(self,
               question:str,
               documents: List[Dict],
               top_k:int =5) ->List[Dict]:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if not documents:
            return []

        #create question-document pairs
        pairs=[
            [
                question,
                document.get("text","")
            ]
            for document in documents
        ]

        #get relevance score
        scores = self.model.predict(pairs)

        #attach reranking score
        reranked_documents = []
        for document, score in zip(documents,scores):
            updated_document = document.copy()
            updated_document["rerank_score"]= float(score)

            reranked_documents.append(updated_document)

        #sort by reranker score
        reranked_documents.sort(key=lambda item: item["rerank_score"],
                                reverse= True)

        #return top-k
        return reranked_documents[:top_k]

reranker = Reranker()