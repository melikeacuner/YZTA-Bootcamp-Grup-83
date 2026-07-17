from app.services.methodology.base import MethodologyEngine, StepDefinition

_STEP_PROMPTS = [
    ("plan", "Plan: Problemi ve hedeflenen iyilestirmeyi planlayin."),
    ("do", "Do (Uygula): Plani kucuk olcekte/test olarak uygulayin."),
    ("check", "Check (Kontrol Et): Uygulama sonuclarini beklenenle karsilastirin."),
    ("act", "Act (Onlem Al): Sonuclara gore standartlastirin veya plani revize edin."),
]


class PDCAEngine(MethodologyEngine):
    """Plan-Do-Check-Act dongusunun dort adimini yonetir."""

    @property
    def steps(self) -> list[StepDefinition]:
        return [StepDefinition(name=name, prompt=prompt) for name, prompt in _STEP_PROMPTS]
