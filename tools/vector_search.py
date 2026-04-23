"""ChromaDB vector search tool for CampaignPilot knowledge base."""

import os
import logging
from typing import Any
import uuid
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class VectorSearchTool:
    """Wrapper around ChromaDB for vector-based document search and ingestion.

    Manages connections to ChromaDB (HTTP or in-memory) and provides methods
    for ingesting documents and searching the knowledge base.
    """

    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        """Initialize ChromaDB client.

        Args:
            host: ChromaDB host. Defaults to CHROMA_HOST env var or 'localhost'.
            port: ChromaDB port. Defaults to CHROMA_PORT env var or 8000.
        """
        host = host or os.getenv("CHROMA_HOST", "localhost")
        port = port or int(os.getenv("CHROMA_PORT", 8000))

        try:
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"Connected to ChromaDB at {host}:{port}")
        except Exception as e:
            logger.warning(
                f"Failed to connect to ChromaDB at {host}:{port}, "
                f"falling back to in-memory client: {e}"
            )
            self.client = chromadb.Client()

    def ingest_document(
        self,
        text: str,
        metadata: dict[str, Any],
        collection: str,
        doc_id: str | None = None
    ) -> str:
        """Ingest a single document into a collection.

        Args:
            text: Document text content.
            metadata: Document metadata dictionary.
            collection: Collection name.
            doc_id: Optional document ID. If not provided, a UUID is generated.

        Returns:
            The document ID.

        Raises:
            Exception: If ChromaDB operation fails.
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())

        try:
            col = self.client.get_or_create_collection(name=collection)
            col.add(documents=[text], metadatas=[metadata], ids=[doc_id])
            logger.debug(f"Ingested document {doc_id} into collection {collection}")
            return doc_id
        except Exception as e:
            logger.error(
                f"Failed to ingest document {doc_id} into collection {collection}: {e}"
            )
            raise

    def ingest_batch(
        self,
        documents: list[dict[str, Any]],
        collection: str
    ) -> list[str]:
        """Ingest multiple documents efficiently.

        Args:
            documents: List of dicts with keys:
                - text (str): Document content
                - metadata (dict): Document metadata
                - id (str | None): Optional document ID
            collection: Collection name.

        Returns:
            List of document IDs.

        Raises:
            Exception: If ChromaDB operation fails.
        """
        try:
            col = self.client.get_or_create_collection(name=collection)

            texts = []
            metadatas = []
            ids = []

            for doc in documents:
                doc_id = doc.get("id") or str(uuid.uuid4())
                texts.append(doc["text"])
                metadatas.append(doc.get("metadata", {}))
                ids.append(doc_id)

            col.upsert(documents=texts, metadatas=metadatas, ids=ids)
            logger.info(f"Ingested {len(documents)} documents into collection {collection}")
            return ids
        except Exception as e:
            logger.error(
                f"Failed to ingest batch into collection {collection}: {e}"
            )
            raise

    def search(
        self,
        query: str,
        collection: str,
        n_results: int = 5,
        where: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search for documents in a collection.

        Args:
            query: Search query text.
            collection: Collection name.
            n_results: Maximum number of results to return.
            where: Optional ChromaDB where filter.

        Returns:
            List of result dicts with keys:
                - text (str): Document content
                - metadata (dict): Document metadata
                - distance (float): Similarity distance
                - id (str): Document ID
        """
        try:
            col = self.client.get_collection(name=collection)
        except Exception as e:
            logger.warning(f"Collection {collection} not found: {e}")
            return []

        try:
            results = col.query(
                query_texts=[query],
                n_results=n_results,
                where=where if where else None
            )

            # Flatten results into list of dicts
            output = []
            if results.get("ids") and len(results["ids"]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    output.append({
                        "id": doc_id,
                        "text": results["documents"][0][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else None
                    })

            return output
        except Exception as e:
            logger.error(f"Search failed in collection {collection}: {e}")
            raise

    def get_collection_count(self, collection: str) -> int:
        """Get the number of documents in a collection.

        Args:
            collection: Collection name.

        Returns:
            Number of documents, or 0 if collection doesn't exist.
        """
        try:
            col = self.client.get_collection(name=collection)
            return col.count()
        except Exception as e:
            logger.warning(f"Failed to get count for collection {collection}: {e}")
            return 0

    def delete_collection(self, collection: str) -> None:
        """Delete a collection.

        Args:
            collection: Collection name.

        Raises:
            Exception: If ChromaDB operation fails.
        """
        try:
            self.client.delete_collection(name=collection)
            logger.info(f"Deleted collection {collection}")
        except Exception as e:
            logger.warning(f"Failed to delete collection {collection}: {e}")
            raise
