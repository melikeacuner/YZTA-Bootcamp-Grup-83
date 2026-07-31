from abc import ABC, abstractmethod
from dataclasses import dataclass

MAX_FOLLOW_UP_QUESTIONS_PER_STEP = 3


@dataclass(frozen=True)
class StepDefinition:
    name: str
    prompt: str
    min_response_length: int = 10


class MethodologyEngine(ABC):
    """Bir metodolojinin adim sirasini, doğrulama kurallarini ve tamlik kontrolunu tanimlar."""

    @property
    @abstractmethod
    def steps(self) -> list[StepDefinition]:
        ...

    @property
    def min_steps_to_complete(self) -> int:
        """Oturumun tamamlanmasi icin en az kac adimin yanitlanmis olmasi gerektigi."""
        return len(self.steps)

    def step_at(self, index: int) -> StepDefinition:
        if not (0 <= index < len(self.steps)):
            raise IndexError("Adim index'i metodoloji adim sayisinin disinda")
        return self.steps[index]

    def validate_response(self, step: StepDefinition, response: str) -> None:
        if len(response.strip()) < step.min_response_length:
            raise ValueError(
                f"'{step.name}' adimi icin yanit en az {step.min_response_length} "
                "karakter olmalidir"
            )

    def is_complete(self, answered_steps: dict[str, str]) -> bool:
        required_names = [s.name for s in self.steps[: self.min_steps_to_complete]]
        return all(name in answered_steps for name in required_names)
