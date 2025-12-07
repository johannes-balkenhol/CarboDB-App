from backend.domain.PrositeSearchResult import PrositeSearchResult


def test_initialization():

    result = PrositeSearchResult(
        sequence_id="seq1",
        prosite_accession="PS00001",
        prosite_name="name",
        start_position=55,
        end_position=59,
        pattern_sequence="ABCDE"
    )

    assert result.sequence_id == "seq1"
    assert result.prosite_accession == "PS00001"
    assert result.prosite_name == "name"
    assert result.start_position == 55
    assert result.end_position == 59
    assert result.pattern_sequence == "ABCDE"

def test_to_dict():
    result = PrositeSearchResult(
        sequence_id="seq1",
        prosite_accession="PS00001",
        prosite_name="name1",
        start_position=55,
        end_position=59,
        pattern_sequence="ABCDE"
    )

    expected = {
        "sequence_id": "seq1",
        "prosite_accession": "PS00001",
        "prosite_name": "name1",
        "start_position": 55,
        "end_position": 59,
        "pattern_sequence": "ABCDE",
        "type": "Prosite hits"
    }
    assert result.to_dict() == expected