from app.services.methodology.base import MethodologyEngine, StepDefinition

_DISCIPLINE_PROMPTS = [
    ("d1_team", "D1 - Ekip: Problemi cozecek ekibi ve rollerini tanimlayin."),
    ("d2_problem_description", "D2 - Problem Tanimi: Problemi net ve olculebilir sekilde tanimlayin."),
    ("d3_containment_actions", "D3 - Gecici Onlemler: Etkiyi sinirlamak icin alinan acil onlemler nelerdir?"),
    ("d4_root_cause", "D4 - Kok Neden: Problemin kok nedeni nedir?"),
    ("d5_corrective_actions", "D5 - Duzeltici Faaliyetler: Kok nedeni ortadan kaldiracak faaliyetler nelerdir?"),
    ("d6_implementation", "D6 - Uygulama: Duzeltici faaliyetler nasil ve ne zaman uygulandi?"),
    ("d7_prevention", "D7 - Onleme: Benzer problemlerin tekrarini onlemek icin ne yapildi?"),
    ("d8_closure", "D8 - Kapanis: Ekip ve sonuc nasil onaylandi/kapatildi?"),
]


class EightDEngine(MethodologyEngine):
    """8D metodolojisinin sekiz disiplinini adim adim yonetir; tumu zorunludur."""

    @property
    def steps(self) -> list[StepDefinition]:
        return [StepDefinition(name=name, prompt=prompt) for name, prompt in _DISCIPLINE_PROMPTS]
