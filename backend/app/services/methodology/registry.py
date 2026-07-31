from app.domain.enums import MethodologyType
from app.services.methodology.base import MethodologyEngine
from app.services.methodology.eight_d_engine import EightDEngine
from app.services.methodology.five_why_engine import FiveWhyEngine
from app.services.methodology.ishikawa_engine import IshikawaEngine
from app.services.methodology.pdca_engine import PDCAEngine

_ENGINES: dict[MethodologyType, type[MethodologyEngine]] = {
    MethodologyType.ISHIKAWA: IshikawaEngine,
    MethodologyType.EIGHT_D: EightDEngine,
    MethodologyType.FIVE_WHY: FiveWhyEngine,
    MethodologyType.PDCA: PDCAEngine,
}


def get_engine(methodology: MethodologyType) -> MethodologyEngine:
    engine_cls = _ENGINES[methodology]
    return engine_cls()
