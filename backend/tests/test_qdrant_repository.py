from app.infrastructure.repositories.qdrant_repository import build_filter


def test_build_filter_returns_none_when_no_criteria():
    assert build_filter() is None


def test_build_filter_includes_provided_criteria_only():
    result = build_filter(methodology="5why", industry=None, department="kalite")

    assert result is not None
    keys = {condition.key for condition in result.must}
    assert keys == {"methodology", "department"}


def test_build_filter_includes_all_criteria_when_provided():
    result = build_filter(methodology="8d", industry="otomotiv", department="uretim")

    assert result is not None
    assert len(result.must) == 3
