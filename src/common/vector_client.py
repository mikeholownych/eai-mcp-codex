"""Vector database client for local Qdrant integration."""

import os
import hashlib
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

import httpx
from src.common.logging import get_logger

logger = get_logger("vector_client")


@dataclass
class VectorDocument:
    """Vector document structure."""

    id: Union[str, int]
    text: str
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None


@dataclass
class SearchResult:
    """Vector search result structure."""

    id: Union[str, int]
    score: float
    document: VectorDocument


class VectorClient:
    """Client for interacting with local Qdrant vector database."""

    def __init__(
        self, qdrant_url: Optional[str] = None, collection_name: str = "rag_documents"
    ):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = collection_name

        # Use the FastAPI LLM router for embeddings
        self.llm_router_url = os.getenv("LOCAL_LLM_URL", "http://localhost:8000")

    async def ensure_collection(self) -> bool:
        """Ensure the collection exists, create if not."""
        try:
            async with httpx.AsyncClient() as client:
                # Check if collection exists
                response = await client.get(
                    f"{self.qdrant_url}/collections/{self.collection_name}"
                )

                if response.status_code == 200:
                    logger.info(f"Collection {self.collection_name} already exists")
                    return True

                # Create collection with default vector size
                collection_config = {
                    "vectors": {
                        "size": 384,  # Standard embedding size
                        "distance": "Cosine",
                    }
                }

                response = await client.put(
                    f"{self.qdrant_url}/collections/{self.collection_name}",
                    json=collection_config,
                )

                if response.status_code in [200, 201]:
                    logger.info(
                        f"Collection {self.collection_name} created successfully"
                    )
                    return True
                else:
                    logger.error(f"Failed to create collection: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            return False

    async def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> bool:
        """Add a document to the vector database."""
        try:
            # Ensure collection exists
            if not await self.ensure_collection():
                return False

            # Generate document ID if not provided
            if doc_id is None:
                doc_id = hashlib.md5(text.encode()).hexdigest()

            # Add document through FastAPI LLM router (which handles embeddings)
            async with httpx.AsyncClient() as client:
                payload = {
                    "text": text,
                    "metadata": metadata or {},
                    "collection_name": self.collection_name,
                }

                response = await client.post(
                    f"{self.llm_router_url}/documents", json=payload
                )

                if response.status_code in [200, 201]:
                    logger.info(f"Document {doc_id} added successfully")
                    return True
                else:
                    logger.error(f"Failed to add document: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False

    async def search(
        self, query: str, limit: int = 5, score_threshold: float = 0.7
    ) -> List[SearchResult]:
        """Search for similar documents."""
        try:
            # Search through FastAPI LLM router
            async with httpx.AsyncClient() as client:
                payload = {
                    "query": query,
                    "collection_name": self.collection_name,
                    "limit": limit,
                }

                response = await client.post(
                    f"{self.llm_router_url}/search", json=payload
                )

                if response.status_code != 200:
                    logger.error(f"Search failed: {response.text}")
                    return []

                result = response.json()
                search_results = []

                for item in result.get("results", []):
                    if item.get("score", 0) >= score_threshold:
                        doc = VectorDocument(
                            id=item["id"],
                            text=item["payload"].get("text", ""),
                            metadata=item["payload"],
                        )

                        search_results.append(
                            SearchResult(
                                id=item["id"], score=item["score"], document=doc
                            )
                        )

                logger.info(f"Found {len(search_results)} relevant documents")
                return search_results

        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    async def get_context(self, query: str, max_context_length: int = 2000) -> str:
        """Get relevant context for a query."""
        try:
            search_results = await self.search(query, limit=5)

            if not search_results:
                return ""

            # Build context from search results
            context_parts = []
            total_length = 0

            for result in search_results:
                doc_text = result.document.text
                if total_length + len(doc_text) < max_context_length:
                    context_parts.append(f"[Score: {result.score:.3f}] {doc_text}")
                    total_length += len(doc_text)
                else:
                    # Truncate the last document to fit
                    remaining = max_context_length - total_length
                    if remaining > 100:  # Only add if meaningful length remains
                        truncated = doc_text[: remaining - 10] + "..."
                        context_parts.append(f"[Score: {result.score:.3f}] {truncated}")
                    break

            context = "\n\n".join(context_parts)
            logger.info(
                f"Generated context of {len(context)} characters from {len(context_parts)} documents"
            )

            return context

        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return ""

    async def list_collections(self) -> List[str]:
        """List all collections in Qdrant."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.qdrant_url}/collections")

                if response.status_code == 200:
                    data = response.json()
                    collections = [
                        col["name"]
                        for col in data.get("result", {}).get("collections", [])
                    ]
                    return collections
                else:
                    logger.error(f"Failed to list collections: {response.text}")
                    return []

        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []

    async def delete_collection(self) -> bool:
        """Delete the current collection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.qdrant_url}/collections/{self.collection_name}"
                )

                if response.status_code in [
                    200,
                    404,
                ]:  # 404 is OK (already doesn't exist)
                    logger.info(f"Collection {self.collection_name} deleted")
                    return True
                else:
                    logger.error(f"Failed to delete collection: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test connection to Qdrant and FastAPI services."""
        try:
            # Test Qdrant connection
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.qdrant_url}/")
                if response.status_code != 200:
                    logger.warning("Qdrant service not available")
                    return False

                # Test FastAPI LLM router connection
                response = await client.get(f"{self.llm_router_url}/health")
                if response.status_code != 200:
                    logger.warning("FastAPI LLM router not available")
                    return False

            logger.info("Vector database connection test successful")
            return True

        except Exception as e:
            logger.error(f"Vector database connection test failed: {e}")
            return False


# Singleton instance
_vector_client: Optional[VectorClient] = None


def get_vector_client(collection_name: str = "rag_documents") -> VectorClient:
    """Get singleton vector client instance."""
    global _vector_client
    if _vector_client is None or _vector_client.collection_name != collection_name:
        _vector_client = VectorClient(collection_name=collection_name)
    return _vector_client
