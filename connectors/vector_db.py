from __future__ import annotations

from ollama import Client
from qdrant_client import QdrantClient, models as qm
from datetime import datetime, timezone



class QClient:
    client = None
    lama_client = None
    dim = 768
    text_docs = "text_docs"
    model = "nomic-embed-text"
    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6333)
        self.lama_client= Client(host="http://localhost:11434")
        self.setup_text_docs_collection()

    def ensure_index(self, field, schema, coll):
        info = self.client.get_collection(coll)
        if (info.payload_schema or {}).get(field) is None:
            self.client.create_payload_index(coll, field_name=field, field_schema=schema)

    def setup_text_docs_collection(self) -> None:
        if self.client.collection_exists(self.text_docs) is False:
            self.client.create_collection(
                collection_name=self.text_docs,
                vectors_config=qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE),
                on_disk_payload=True
            )
        for field, schema in [
            ("doc_id", qm.PayloadSchemaType.KEYWORD),
            ("doc_type", qm.PayloadSchemaType.KEYWORD),
            ("published_at", qm.PayloadSchemaType.INTEGER),  # epoch seconds
            ("title", qm.PayloadSchemaType.TEXT),
            ("summary", qm.PayloadSchemaType.TEXT),
            ("provider", qm.PayloadSchemaType.KEYWORD),
            ("ticker", qm.PayloadSchemaType.KEYWORD),
            ("instrument_type", qm.PayloadSchemaType.KEYWORD),
            ("instrument_id", qm.PayloadSchemaType.KEYWORD),
            ("language", qm.PayloadSchemaType.KEYWORD),
        ]:
            self.ensure_index(field, schema, self.text_docs)

    def embed_document(self, ticker: str, inst_type: str, doc: {}) -> bool:
        text = doc.get("article")
        res = self.lama_client.embeddings(model=self.model, prompt=text)
        pub_date = doc.get("pubDate")
        payload = {
            "doc_id": doc["id"],
            "doc_type": "news",
            "published_at": int(datetime.fromisoformat(pub_date.replace('Z', '+00:00')).timestamp()),
            "title": doc["title"],
            "summary": doc["summary"],
            "provider": doc["provider"],
            "ticker": ticker,
            "instrument_type": inst_type,
            "language": "English",
            # optional now, useful later
            "instrument_id": None,
            "url": doc["canonicalUrl"],
        }
        point = qm.models.PointStruct(id=doc.get("id"), vector=res["embedding"], payload=payload)
        self.client.upsert(collection_name=self.text_docs, points=[point])
        return True

