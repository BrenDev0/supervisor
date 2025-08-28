from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    UnstructuredWordDocumentLoader
)
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import os
import uuid
import time
from typing import Optional, List, Dict, Any

class EmbeddingService:
    def __init__(self, embedding_model: Optional[OpenAIEmbeddings] = None):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        self.embedding_model = embedding_model or OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        self.loader_mapping = {
            'application/pdf': PyPDFLoader,
            'text/plain': TextLoader,
            'text/csv': CSVLoader,
            'application/vnd.ms-excel': UnstructuredExcelLoader,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': UnstructuredExcelLoader,
            'application/msword': UnstructuredWordDocumentLoader,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': UnstructuredWordDocumentLoader
        }

    @staticmethod
    def get_collection_name(user_id: str, agent_id: str) -> str:
        return f"user_{user_id}_agent_{agent_id}"
    
    async def create_collection(self, user_id: str, agent_id: str) -> bool:
        collection_name = self.get_collection_name(user_id, agent_id)
        
        try:
            self.client.get_collection(collection_name)
            return False  # Collection already exists
        except Exception:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=3072,
                    distance=Distance.COSINE
                ),
            )
            return True

    async def delete_user_data(self, user_id: str) -> int:
        deleted_count = 0
        collections = self.client.get_collections()
        prefix = f"user_{user_id}_agent_"
        
        for collection in collections.collections:
            if collection.name.startswith(prefix):
                self.client.delete_collection(collection.name)
                deleted_count += 1
                
        return deleted_count

    async def _load_document_from_url(
        self,
        s3_url: str,
        file_type: str,
        filename: str
    ) -> List[Dict[str, Any]]:
        loader_class = self.loader_mapping.get(file_type)
        if not loader_class:
            raise ValueError(f"Unsupported file type: {file_type}")

        loader = loader_class(s3_url)
        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)

        return [{
            "text": chunk.page_content,
            "metadata": {
                **chunk.metadata,
                "original_filename": filename,
                "chunk_id": str(uuid.uuid4())
            }
        } for chunk in chunks]

    async def embed_uploaded_document(
        self,
        s3_url: str,
        file_type: str,
        filename: str,
        user_id: str,
        agent_id: str,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        collection_name = self.get_collection_name(user_id, agent_id)
        await self.create_collection(user_id, agent_id)

        chunks = await self._load_document_from_url(s3_url, file_type, filename)
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.embedding_model.aembed_documents(texts)

        points = []
        for chunk, embedding in zip(chunks, embeddings):
            metadata = {
                "user_id": user_id,
                "agent_id": agent_id,
                "upload_timestamp": int(time.time()),
                **chunk["metadata"]
            }

            if custom_metadata:
                metadata.update(custom_metadata)

            points.append({
                "id": str(uuid.uuid4()),
                "vector": embedding,
                "payload": {
                    "text": chunk["text"],
                    "metadata": metadata
                }
            })

        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

        return {
            "status": "success",
            "chunks_processed": len(points),
            "collection": collection_name,
            "document_id": str(uuid.uuid4())
        }

    async def similarity_search(
        self,
        query: str,
        collection_name: str,
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        query_embedding = await self.embedding_model.aembed_query(query)

        search_results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True
        )

        return [
            {
                "text": item.payload["text"],
                "metadata": item.payload.get("metadata", {}),
                "score": item.score
            }
            for item in search_results
        ]

    async def search_for_context(
        self,
        query: str,
        collection_name: str,
        top_k: int = 4
    ) -> Optional[str]:
        try:
            results = await self.similarity_search(
                query=query,
                collection_name=collection_name,
                limit=top_k
            )
            
            if not results:
                return None
                
            return "\n\n".join([result["text"] for result in results])
            
        except Exception as e:
            print(f"Error searching for context: {e}")
            return None

    def get_collection_contents(
        self, 
        user_id: str, 
        agent_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        collection_name = self.get_collection_name(user_id, agent_id)
        
        try:
            results, _ = self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_payload=True
            )
            
            return [
                {
                    "id": point.id,
                    "text": point.payload.get("text", ""),
                    "metadata": point.payload.get("metadata", {})
                }
                for point in results
            ]
            
        except Exception as e:
            print(f"Error getting collection contents: {e}")
            return []