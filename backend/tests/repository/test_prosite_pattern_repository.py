import pytest
from backend.repository.PrositePatternRepository import PrositePatternRepository

def test_get_all_patterns():
    repo = PrositePatternRepository()
    expected_patterns = [
        "PS00157", "PS00155", "PS00866", "PS00867", "PS00188", "PS00781",
        "PS00393", "PS00012", "PS00703", "PS00768", "PS00878", "PS00879",
        "PS00103", "PS00156", "PS01330", "PS01336", "PS00906", "PS00907",
        "PS00392", "PS00923", "PS00924"
    ]

    result = repo.get_all_patterns()
    assert isinstance(result, list), "Result should be a list"
    assert set(result) == set(expected_patterns), "Returned patterns do not match expected patterns"
    assert len(result) == len(expected_patterns), "Length of pattern list is incorrect"