from app.domain.enums import IshikawaCategory
from app.services.methodology.base import MethodologyEngine, StepDefinition

_CATEGORY_PROMPTS = {
    IshikawaCategory.MAN: "Insan (Man): Bu probleme insan/operator kaynakli hangi etkenler katkida bulunuyor?",
    IshikawaCategory.MACHINE: "Makine (Machine): Ekipman/makine ile ilgili hangi etkenler soz konusu?",
    IshikawaCategory.METHOD: "Yontem (Method): Surec/yontemle ilgili hangi etkenler soz konusu?",
    IshikawaCategory.MATERIAL: "Malzeme (Material): Girdi/malzeme ile ilgili hangi etkenler soz konusu?",
    IshikawaCategory.MEASUREMENT: "Olcum (Measurement): Olcum/kontrol ile ilgili hangi etkenler soz konusu?",
    IshikawaCategory.ENVIRONMENT: "Ortam (Environment): Calisma ortamiyla ilgili hangi etkenler soz konusu?",
}


class IshikawaEngine(MethodologyEngine):
    """Ishikawa (balik kilcigi) analizinin alti kategorisini adim adim yonetir."""

    @property
    def steps(self) -> list[StepDefinition]:
        return [
            StepDefinition(name=category.value, prompt=prompt)
            for category, prompt in _CATEGORY_PROMPTS.items()
        ]
