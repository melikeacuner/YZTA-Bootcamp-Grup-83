import uuid
from dataclasses import dataclass

from app.infrastructure.repositories.qdrant_repository import QdrantUnavailableError


@dataclass
class FakeScoredPoint:
    id: str
    score: float
    payload: dict


class FakeQdrantRepository:
    """QdrantRepository'nin gercek Qdrant sunucusu olmadan test edilebilen sahte surumu."""

    def __init__(
        self,
        fail_times: int = 0,
        search_results: list[FakeScoredPoint] | None = None,
        always_fail: bool = False,
    ) -> None:
        self.fail_times = fail_times
        self.always_fail = always_fail
        self.search_results = search_results or []
        self.upserted: list[tuple[uuid.UUID, list[float], dict]] = []
        self.search_calls: list[dict] = []
        self._upsert_attempts = 0

    def upsert(self, record_id: uuid.UUID, vector: list[float], payload: dict) -> None:
        self._upsert_attempts += 1
        if self.always_fail or self._upsert_attempts <= self.fail_times:
            raise QdrantUnavailableError("Qdrant erisilemedi")
        self.upserted.append((record_id, vector, payload))

    def search(self, vector, limit, score_threshold, query_filter=None):
        if self.always_fail:
            raise QdrantUnavailableError("Qdrant erisilemedi")
        self.search_calls.append(
            {
                "vector": vector,
                "limit": limit,
                "score_threshold": score_threshold,
                "query_filter": query_filter,
            }
        )
        return self.search_results

    def delete(self, record_id: uuid.UUID) -> None:
        if self.always_fail:
            raise QdrantUnavailableError("Qdrant erisilemedi")
