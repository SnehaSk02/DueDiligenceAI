import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams,PayloadSchemaType, PointStruct
from uuid import uuid5, NAMESPACE_DNS
load_dotenv()

class QdrantManager:
    def __init__(self, collection_name: str = "due_diligence_chunks"):
        self.collection_name = collection_name

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url:
            raise ValueError("QDRANT_URL is not configured.")

        if not qdrant_api_key:
            raise ValueError("QDRANT_API_KEY is not configured.")

        self.client =QdrantClient(url = qdrant_url,api_key=qdrant_api_key,timeout=60)

    def create_collection(self):
        collections = self.client.get_collections()

        existing_collections = [collection.name for collection in collections.collections]

        if self.collection_name in existing_collections:
            print(f"Collection '{self.collection_name}' already exists")
            return 

        self.client.create_collection(collection_name= self.collection_name,
                                      vectors_config=VectorParams(size = 1024, distance =Distance.COSINE))

        print(f"Collection '{self.collection_name}' created successfully.")

    #storing vectors
    def upsert_chunks(self,embeddings,chunks,batch_size:int =32):
        if not embeddings:
            return

        if len(embeddings) != len(chunks):
            raise ValueError(
            "Number of embeddings does not match number of chunks.")

        total_chunks = len(chunks)

        for start in range(0, total_chunks, batch_size):

            end = min(start + batch_size, total_chunks)

            batch_embeddings = embeddings[start:end]
            batch_chunks = chunks[start:end]

            points = []

            for embedding, chunk in zip(batch_embeddings,batch_chunks):
                point= PointStruct(
                    id=str(uuid5(NAMESPACE_DNS,
                                    f"{chunk['case_id']}_{chunk['document_id']}_{chunk['chunk_index']}")),                
                    vector = embedding,
                    payload = {
                    "case_id": chunk["case_id"],
                    "document_id": chunk["document_id"],
                    "document_type": chunk["document_type"],
                    "page_number": chunk["page_number"],
                    "content_type": chunk["content_type"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"]

                }
            )
                points.append(point)

            self.client.upsert(collection_name=self.collection_name,
                           points=points)

            print(
            f"Uploaded chunks {start + 1}-{end} "
            f"of {total_chunks}"
        )

        print(f"{total_chunks} chunks stored in Qdrant.")

    def create_payload_indexes(self):
        """
        Create payload indexes required for filtered retrieval.
        """

        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="case_id",
            field_schema=PayloadSchemaType.INTEGER
        )

        print("Payload index for 'case_id' created successfully.")

    #searching for vectors
    def search_chunks(self, 
                      query_embedding,
                      limit: int =5,
                      case_id:int |None=None):
        query_filter = None

        if case_id is not None:
            query_filter = {
                "must" : [
                    {
                        "key":"case_id",
                        "match":{
                            "value":case_id
                        }
                    }
                ]
            }
        results = self.client.query_points(
            collection_name = self.collection_name,
            query=query_embedding,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        ).points

        return results