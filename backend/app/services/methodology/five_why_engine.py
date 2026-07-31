from app.services.methodology.base import MethodologyEngine, StepDefinition

MIN_WHY_QUESTIONS = 3
MAX_WHY_QUESTIONS = 7


class FiveWhyEngine(MethodologyEngine):
    """5 Why kok neden analizi: en az 3, en fazla 7 'neden' adimi."""

    @property
    def steps(self) -> list[StepDefinition]:
        return [
            StepDefinition(name=f"why_{i}", prompt=f"Neden {i}: Bir onceki nedenin sebebi nedir?")
            for i in range(1, MAX_WHY_QUESTIONS + 1)
        ]

    @property
    def min_steps_to_complete(self) -> int:
        return MIN_WHY_QUESTIONS
