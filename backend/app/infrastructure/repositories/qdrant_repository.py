import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import get_settings


class QdrantUnavailableError(Exception):
    pass


def build_filter(
    *,
    methodology: str | None = None,
    industry: str | None = None,
    department: str | None = None,
) -> qmodels.Filter | None:
    conditions = []
    if methodology:
        conditions.append(qmodels.FieldCondition(key="methodology", match=qmodels.MatchValue(value=methodology)))
    if industry:
        conditions.append(qmodels.FieldCondition(key="industry", match=qmodels.MatchValue(value=industry)))
    if department:
        conditions.append(qmodels.FieldCondition(key="department", match=qmodels.MatchValue(value=department)))

    if not conditions:
        return None
    return qmodels.Filter(must=conditions)


class QdrantRepository:
    """Qdrant uzerinde ProblemRecord vektorleri icin upsert/arama/silme islemleri."""

    def __init__(
        self,
        client: QdrantClient | None = None,
        collection_name: str | None = None,
        vector_size: int | None = None,
    ) -> None:
        settings = get_settings()
        self._collection_name = collection_name or settings.qdrant_collection
        self._vector_size = vector_size or settings.embedding_dimension
        self._client = client or QdrantClient(url=settings.qdrant_url)

    def ensure_collection(self) -> None:
        try:
            existing = [c.name for c in self._client.get_collections().collections]
            if self._collection_name not in existing:
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self._vector_size, distance=qmodels.Distance.COSINE
                    ),
                )
        except Exception as exc:
            raise QdrantUnavailableError(str(exc)) from exc

    def upsert(self, record_id: uuid.UUID, vector: list[float], payload: dict) -> None:
        try:
            self._client.upsert(
                collection_name=self._collection_name,
                points=[qmodels.PointStruct(id=str(record_id), vector=vector, payload=payload)],
            )
        except Exception as exc:
            raise QdrantUnavailableError(str(exc)) from exc

    def search(
        self,
        vector: list[float],
        limit: int,
        score_threshold: float,
        query_filter: qmodels.Filter | None = None,
    ) -> list[qmodels.ScoredPoint]:
        try:
            return self._client.search(
                collection_name=self._collection_name,
                query_vector=vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )
        except Exception as exc:
            raise QdrantUnavailableError(str(exc)) from exc

    def delete(self, record_id: uuid.UUID) -> None:
        try:
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=qmodels.PointIdsList(points=[str(record_id)]),
            )
        except Exception as exc:
            raise QdrantUnavailableError(str(exc)) from exc
