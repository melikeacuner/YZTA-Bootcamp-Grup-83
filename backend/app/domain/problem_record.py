import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import EmbeddingStatus, MethodologyType, SessionStatus
from app.domain.methodology import EightDReport, IshikawaData, PDCACycle, WhyChain
from app.domain.validation import validate_lessons_learned


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProblemRecord(BaseModel):
    """Tamamlanmış bir problem çözme oturumunun kalıcı, aranabilir kaydı."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=20, max_length=2000)
    methodology: MethodologyType
    industry: str | None = None
    department: str | None = None

    ishikawa_data: IshikawaData | None = None
    why_chain: WhyChain | None = None
    eight_d_report: EightDReport | None = None
    pdca_cycle: PDCACycle | None = None

    root_cause: str | None = None
    corrective_actions: str | None = None
    lessons_learned: str = Field(min_length=1)

    status: SessionStatus = SessionStatus.COMPLETED
    embedding_status: EmbeddingStatus = EmbeddingStatus.PENDING

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @field_validator("lessons_learned")
    @classmethod
    def validate_lessons_learned_word_count(cls, value: str) -> str:
        return validate_lessons_learned(value)

    def model_dump_json_pretty(self) -> str:
        """2 boşluklu girinti ve sözlük sırasıyla anahtarlar (round-trip serileştirme için)."""
        import json

        return json.dumps(
            self.model_dump(mode="json"),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
