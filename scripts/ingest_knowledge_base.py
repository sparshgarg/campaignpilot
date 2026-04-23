"""Ingest Meta knowledge base and creative examples into ChromaDB."""

import os
import json
import logging
import sys
from pathlib import Path

import chromadb
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from brands.config import get_active_brand

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    char_chunk_size = chunk_size * 4
    char_overlap = overlap * 4
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + char_chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - char_overlap
    return chunks


def init_chroma():
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", "8000"))
    try:
        client = chromadb.HttpClient(host=host, port=port)
        return client
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB at {host}:{port}: {e}")
        raise


def ingest_knowledge_base():
    brand = get_active_brand()
    client = init_chroma()

    collection_name = f"{brand.brand_id}_knowledge_base"
    kb_collection = client.get_or_create_collection(name=collection_name)
    creative_collection = client.get_or_create_collection(name="creative_examples")

    logger.info(f"Ingesting {brand.company_name} knowledge base into `{collection_name}`...")

    kb_path = brand.knowledge_base_path
    files = list(kb_path.rglob("*")) if kb_path.exists() else []

    doc_count = 0
    for file_path in files:
        if file_path.suffix not in (".md", ".json", ".txt"):
            continue
        content = file_path.read_text(encoding="utf-8")
        for i, chunk in enumerate(chunk_text(content)):
            kb_collection.upsert(
                documents=[chunk],
                metadatas=[{"source": file_path.name, "chunk": i, "brand": brand.brand_id}],
                ids=[f"{file_path.name}_chunk_{i}"],
            )
            doc_count += 1

    logger.info(f"Ingested {doc_count} chunks into `{collection_name}`.")

    logger.info("Ingesting creative golden dataset into `creative_examples`...")
    golden_file = Path(__file__).parent.parent / "data/golden_datasets/creative_golden.json"
    creative_count = 0
    if golden_file.exists():
        data = json.loads(golden_file.read_text())
        for i, item in enumerate(data):
            expected = item.get("expected_output", {})
            content_str = "\n".join(f"{k}: {v}" for k, v in expected.items())
            if not content_str.strip():
                continue
            doc_id = item.get("id", f"creative_example_{i}")
            creative_collection.upsert(
                documents=[content_str],
                metadatas=[{"source": "creative_golden.json", "id": doc_id, "brand": brand.brand_id}],
                ids=[doc_id],
            )
            creative_count += 1
    else:
        logger.warning(f"{golden_file} not found — skipping creative examples.")

    logger.info(f"Ingested {creative_count} documents into `creative_examples`.")
    logger.info(f"Done. KB collection: `{collection_name}` ({doc_count} chunks), creative_examples ({creative_count} docs).")


if __name__ == "__main__":
    ingest_knowledge_base()
