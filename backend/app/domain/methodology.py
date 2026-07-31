from pydantic import BaseModel, Field, field_validator

from app.domain.enums import IshikawaCategory


class IshikawaData(BaseModel):
    """Ishikawa (balık kılçığı) analizinin altı kategorisi için yanıtlar."""

    man: list[str] = Field(default_factory=list)
    machine: list[str] = Field(default_factory=list)
    method: list[str] = Field(default_factory=list)
    material: list[str] = Field(default_factory=list)
    measurement: list[str] = Field(default_factory=list)
    environment: list[str] = Field(default_factory=list)

    @field_validator("man", "machine", "method", "material", "measurement", "environment")
    @classmethod
    def validate_entry_length(cls, entries: list[str]) -> list[str]:
        for entry in entries:
            if not (1 <= len(entry) <= 500):
                raise ValueError("Ishikawa kategori yanıtı 1-500 karakter olmalıdır")
        return entries

    def categories(self) -> dict[IshikawaCategory, list[str]]:
        return {
            IshikawaCategory.MAN: self.man,
            IshikawaCategory.MACHINE: self.machine,
            IshikawaCategory.METHOD: self.method,
            IshikawaCategory.MATERIAL: self.material,
            IshikawaCategory.MEASUREMENT: self.measurement,
            IshikawaCategory.ENVIRONMENT: self.environment,
        }


class WhyChain(BaseModel):
    """5 Why kök neden analizi zinciri (3-7 soru-cevap)."""

    questions: list[str] = Field(min_length=3, max_length=7)
    answers: list[str] = Field(min_length=3, max_length=7)

    @field_validator("answers")
    @classmethod
    def validate_matching_length(cls, answers: list[str], info) -> list[str]:
        questions = info.data.get("questions")
        if questions is not None and len(answers) != len(questions):
            raise ValueError("Soru ve cevap sayısı eşit olmalıdır")
        return answers

    def has_circular_logic(self, overlap_threshold: float = 0.7) -> bool:
        """Ardışık cevaplar arasında yüksek kelime örtüşmesi varsa döngüsel mantık işareti sayılır."""
        for i in range(len(self.answers) - 1):
            words_a = set(self.answers[i].lower().split())
            words_b = set(self.answers[i + 1].lower().split())
            if not words_a or not words_b:
                continue
            overlap = len(words_a & words_b) / len(words_a | words_b)
            if overlap >= overlap_threshold:
                return True
        return False


EIGHT_D_DISCIPLINES = (
    "d1_team",
    "d2_problem_description",
    "d3_containment_actions",
    "d4_root_cause",
    "d5_corrective_actions",
    "d6_implementation",
    "d7_prevention",
    "d8_closure",
)


class EightDReport(BaseModel):
    """8D metodolojisinin sekiz disiplini; tamamlanmış oturumda hepsi zorunludur."""

    d1_team: str = Field(min_length=10)
    d2_problem_description: str = Field(min_length=10)
    d3_containment_actions: str = Field(min_length=10)
    d4_root_cause: str = Field(min_length=10)
    d5_corrective_actions: str = Field(min_length=10)
    d6_implementation: str = Field(min_length=10)
    d7_prevention: str = Field(min_length=10)
    d8_closure: str = Field(min_length=10)

    def is_complete(self) -> bool:
        return all(getattr(self, discipline).strip() for discipline in EIGHT_D_DISCIPLINES)


class PDCACycle(BaseModel):
    """Plan-Do-Check-Act döngüsü adımları."""

    plan: str = Field(min_length=10)
    do: str = Field(min_length=10)
    check: str = Field(min_length=10)
    act: str = Field(min_length=10)
