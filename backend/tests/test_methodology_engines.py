import pytest

from app.domain.enums import MethodologyType
from app.services.methodology.eight_d_engine import EightDEngine
from app.services.methodology.five_why_engine import MAX_WHY_QUESTIONS, MIN_WHY_QUESTIONS, FiveWhyEngine
from app.services.methodology.ishikawa_engine import IshikawaEngine
from app.services.methodology.pdca_engine import PDCAEngine
from app.services.methodology.registry import get_engine


@pytest.mark.parametrize(
    "methodology,engine_cls,expected_step_count",
    [
        (MethodologyType.ISHIKAWA, IshikawaEngine, 6),
        (MethodologyType.EIGHT_D, EightDEngine, 8),
        (MethodologyType.FIVE_WHY, FiveWhyEngine, MAX_WHY_QUESTIONS),
        (MethodologyType.PDCA, PDCAEngine, 4),
    ],
)
def test_registry_returns_correct_engine_with_expected_step_count(
    methodology, engine_cls, expected_step_count
):
    engine = get_engine(methodology)
    assert isinstance(engine, engine_cls)
    assert len(engine.steps) == expected_step_count


def test_ishikawa_requires_all_six_categories_to_complete():
    engine = IshikawaEngine()
    assert engine.min_steps_to_complete == 6
    partial = {s.name: "yeterince uzun bir yanit metni" for s in engine.steps[:5]}
    assert engine.is_complete(partial) is False

    full = {s.name: "yeterince uzun bir yanit metni" for s in engine.steps}
    assert engine.is_complete(full) is True


def test_eight_d_requires_all_eight_disciplines_to_complete():
    engine = EightDEngine()
    assert engine.min_steps_to_complete == 8
    partial = {s.name: "yeterince uzun bir yanit metni" for s in engine.steps[:7]}
    assert engine.is_complete(partial) is False


def test_five_why_completes_with_minimum_three_answers():
    engine = FiveWhyEngine()
    assert engine.min_steps_to_complete == MIN_WHY_QUESTIONS
    answers = {f"why_{i}": "yeterince uzun bir yanit metni" for i in range(1, 4)}
    assert engine.is_complete(answers) is True


def test_five_why_incomplete_with_two_answers():
    engine = FiveWhyEngine()
    answers = {f"why_{i}": "yeterince uzun bir yanit metni" for i in range(1, 3)}
    assert engine.is_complete(answers) is False


def test_pdca_requires_all_four_phases():
    engine = PDCAEngine()
    partial = {s.name: "yeterince uzun bir yanit metni" for s in engine.steps[:3]}
    assert engine.is_complete(partial) is False
    full = {s.name: "yeterince uzun bir yanit metni" for s in engine.steps}
    assert engine.is_complete(full) is True


def test_validate_response_rejects_short_answers():
    engine = PDCAEngine()
    step = engine.step_at(0)
    with pytest.raises(ValueError):
        engine.validate_response(step, "kisa")


def test_validate_response_accepts_min_length_answer():
    engine = PDCAEngine()
    step = engine.step_at(0)
    engine.validate_response(step, "0123456789")  # tam 10 karakter


def test_step_at_out_of_range_raises_index_error():
    engine = PDCAEngine()
    with pytest.raises(IndexError):
        engine.step_at(99)
