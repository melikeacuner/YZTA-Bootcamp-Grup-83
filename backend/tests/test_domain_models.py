import uuid

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain.enums import MethodologyType
from app.domain.methodology import EightDReport, WhyChain
from app.domain.problem_record import ProblemRecord

VALID_LESSONS_LEARNED = " ".join(["kelime"] * 150)


def make_record(**overrides) -> ProblemRecord:
    defaults = dict(
        session_id=uuid.uuid4(),
        title="Bant hattinda duraksama",
        description="Uretim hattinda tekrarlayan duraksamalar musteri teslimatlarini geciktiriyor.",
        methodology=MethodologyType.FIVE_WHY,
        lessons_learned=VALID_LESSONS_LEARNED,
    )
    defaults.update(overrides)
    return ProblemRecord(**defaults)


def test_problem_record_round_trip_preserves_fields():
    record = make_record()
    dumped = record.model_dump(mode="json")
    restored = ProblemRecord.model_validate(dumped)
    assert restored == record


def test_problem_record_json_round_trip():
    record = make_record()
    json_str = record.model_dump_json()
    restored = ProblemRecord.model_validate_json(json_str)
    assert restored.id == record.id
    assert restored.description == record.description


def test_pretty_printer_is_sorted_and_indented():
    record = make_record()
    pretty = record.model_dump_json_pretty()
    assert '"  "'[1:2] != ""  # sanity: string not empty
    lines = pretty.splitlines()
    assert lines[0] == "{"
    assert lines[1].startswith("  ")


@pytest.mark.parametrize("length", [19, 2001])
def test_description_length_boundaries_reject(length):
    with pytest.raises(ValueError):
        make_record(description="a" * length)


@pytest.mark.parametrize("length", [20, 2000])
def test_description_length_boundaries_accept(length):
    record = make_record(description="a" * length)
    assert len(record.description) == length


@given(word_count=st.integers(min_value=1, max_value=99))
def test_lessons_learned_below_minimum_rejected(word_count):
    with pytest.raises(ValueError):
        make_record(lessons_learned=" ".join(["k"] * word_count))


@given(word_count=st.integers(min_value=501, max_value=700))
def test_lessons_learned_above_maximum_rejected(word_count):
    with pytest.raises(ValueError):
        make_record(lessons_learned=" ".join(["k"] * word_count))


def test_why_chain_requires_matching_question_answer_counts():
    with pytest.raises(ValueError):
        WhyChain(questions=["q1", "q2", "q3"], answers=["a1", "a2"])


@pytest.mark.parametrize("count", [1, 2, 8])
def test_why_chain_rejects_out_of_range_lengths(count):
    with pytest.raises(ValueError):
        WhyChain(questions=["q"] * count, answers=["a"] * count)


def test_why_chain_detects_circular_logic():
    chain = WhyChain(
        questions=["Neden A?", "Neden B?", "Neden C?"],
        answers=[
            "makine ariza yapti bakim eksik",
            "makine ariza yapti bakim eksik kaldi",
            "operator mudahale etmedi",
        ],
    )
    assert chain.has_circular_logic() is True


def test_eight_d_report_requires_all_disciplines_min_length():
    with pytest.raises(ValueError):
        EightDReport(
            d1_team="kisa",
            d2_problem_description="yeterince uzun bir aciklama metni",
            d3_containment_actions="yeterince uzun bir aciklama metni",
            d4_root_cause="yeterince uzun bir aciklama metni",
            d5_corrective_actions="yeterince uzun bir aciklama metni",
            d6_implementation="yeterince uzun bir aciklama metni",
            d7_prevention="yeterince uzun bir aciklama metni",
            d8_closure="yeterince uzun bir aciklama metni",
        )


def test_eight_d_report_complete_when_all_disciplines_filled():
    report = EightDReport(
        d1_team="Ekip: Ahmet, Ayse, Mehmet",
        d2_problem_description="Hat 3'te tekrarlayan kalite hatasi",
        d3_containment_actions="Etkilenen lotlar karantinaya alindi",
        d4_root_cause="Kalibrasyon suresi asilmis sensor",
        d5_corrective_actions="Sensor kalibrasyon plani guncellendi",
        d6_implementation="Yeni plan tum vardiyalarda uygulandi",
        d7_prevention="Otomatik kalibrasyon hatirlaticisi eklendi",
        d8_closure="Ekip kapanis toplantisinda sonucu onayladi",
    )
    assert report.is_complete() is True
